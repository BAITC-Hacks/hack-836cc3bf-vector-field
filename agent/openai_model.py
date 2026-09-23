"""One OpenAI Responses adapter for the existing read-only Investigator loop.

The adapter does not read the snapshot. It sees only bounded tool observations
that ToolSession has already checked against the current snapshot.
"""

from __future__ import annotations

from copy import deepcopy
import json
import logging
import os
from typing import Any, Mapping, Sequence

from .harness import (
    FinalAction, ModelProtocolError, ModelProviderError, ModelUnavailableError,
    PATH_NEXT_CHECK, ToolAction,
)


LOG = logging.getLogger(__name__)
DEFAULT_MODEL = "gpt-6-luna"

INSTRUCTIONS = """Ты помощник AML-аналитика по финансовой сети. Отвечай на языке вопроса.
Факты бери только из вызовов доступных read-only инструментов текущего snapshot.
Сохраняй gid в точности как строки. Не угадывай профили, связи, evidence_id или числа.
priority_score — очередь аналитической проверки, не вероятность преступления.
Разделяй наблюдение и гипотезу. Не обвиняй людей и не утверждай происхождение денег.
Путь в графе не доказывает хронологию операций или движение тех же средств.
Учитывай ограничения: неполный inflow, только июль 2026, даты до дня, depth=4.
При пустом результате или недостатке фактов прямо сообщай о нехватке данных.
Не раскрывай скрытые рассуждения; верни только краткие выводы с ссылками на evidence.
В finding.text не вставляй цифры, gid или значения score: интерфейс показывает их из fact objects.
Каждый вывод должен ссылаться на существующие evidence_ids и gids из результатов tools.
"""


def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function", "name": name, "description": description,
        "strict": True,
        "parameters": {
            "type": "object", "properties": properties, "required": required,
            "additionalProperties": False,
        },
    }


_GID = {"type": "string", "description": "Exact decimal gid string; never convert to a number."}
TOOL_DEFINITIONS = [
    _tool("get_entity_profile", "Read one exact gid profile, metrics, evidence and limitations.",
          {"gid": _GID}, ["gid"]),
    _tool("get_subgraph", "Read directed observed edges around a gid; use for connection questions. Hops 1..2, limit 1..200.",
          {"gid": _GID, "hops": {"type": "integer"}, "limit": {"type": "integer"}},
          ["gid", "hops", "limit"]),
    _tool("rank_entities", "Read priority ranking; use for who-to-review-first questions. Limit 1..200. Null means no filter.",
          {"role": {"type": ["string", "null"]},
           "cluster_id": {"type": ["integer", "null"]},
           "limit": {"type": "integer"}},
          ["role", "cluster_id", "limit"]),
    _tool("find_common_recipients", "Find common directed recipients for 1..20 exact gids. One hop means direct transfers; more hops mean structural reachability, not a money trail. Limit 1..50.",
          {"gids": {"type": "array", "items": _GID},
           "max_hops": {"type": "integer"}, "limit": {"type": "integer"}},
          ["gids", "max_hops", "limit"]),
]

FINAL_FORMAT = {
    "type": "json_schema", "name": "investigator_findings", "strict": True,
    "schema": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string"},
                        "gids": {"type": "array", "items": {"type": "string"}},
                        "evidence_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["text", "gids", "evidence_ids"],
                },
            },
            "next_checks": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["findings", "next_checks"],
    },
}


def _short_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Keep model input small without changing any cited facts."""
    name, result = observation["name"], observation["result"]
    if name == "get_entity_profile":
        entity = result["entity"]
        view = {key: deepcopy(entity[key]) for key in (
            "gid", "depth", "is_seed", "role", "role_score", "priority_score",
            "cluster_id", "metrics", "evidence", "limitations", "next_checks",
        )}
    elif name == "rank_entities":
        view = {"total": result["total"], "items": deepcopy(result["items"][:10]),
                "shown_to_model": min(10, len(result["items"]))}
    elif name == "get_subgraph":
        view = {key: deepcopy(result[key]) for key in (
            "center_gid", "hops", "total_nodes", "total_edges", "truncated",
            "omitted_count", "omitted_edges",
        )}
        view["nodes"] = deepcopy(result["nodes"][:40])
        view["edges"] = deepcopy(result["edges"][:80])
        view["model_view_limited"] = (
            len(view["nodes"]) < len(result["nodes"])
            or len(view["edges"]) < len(result["edges"])
        )
    else:
        view = {key: deepcopy(result[key]) for key in (
            "selected_gids", "mode", "max_hops", "total", "truncated", "limitations",
        )}
        shown = 3 if len(result["selected_gids"]) <= 4 else 1
        view["items"] = deepcopy(result["items"][:shown])
        view["shown_to_model"] = len(view["items"])
        evidence_count = shown * (len(result["selected_gids"]) + 1)
        return {"tool": name, "result": view,
                "evidence": deepcopy(observation["evidence"][:evidence_count])}
    return {"tool": name, "result": view, "evidence": deepcopy(observation["evidence"])}


def _profile_followup(observations: Sequence[Mapping[str, Any]]) -> ToolAction | None:
    if not observations:
        return None
    first = observations[0]
    profiled = {
        item["result"]["entity"]["gid"] for item in observations
        if item["name"] == "get_entity_profile"
    }
    if first["name"] == "rank_entities":
        for item in first["result"]["items"][:3]:
            if item["gid"] not in profiled:
                return ToolAction("get_entity_profile", {"gid": item["gid"]})
    if first["name"] == "get_subgraph":
        center = first["result"]["center_gid"]
        if center not in profiled:
            return ToolAction("get_entity_profile", {"gid": center})
    return None


def _final_action(draft: Mapping[str, Any], observations: Sequence[Mapping[str, Any]]) -> FinalAction:
    if set(draft) != {"findings", "next_checks"} or not isinstance(draft["findings"], list):
        raise ModelProtocolError("invalid final response shape")
    if not isinstance(draft["next_checks"], list) or len(draft["findings"]) > 3:
        raise ModelProtocolError("too many or malformed findings")
    facts = {
        fact["evidence_id"]: fact
        for item in observations for fact in _short_observation(item)["evidence"]
    }
    entities = {
        item["result"]["entity"]["gid"]: item["result"]["entity"]
        for item in observations if item["name"] == "get_entity_profile"
    }
    allowed_checks = {
        check for entity in entities.values() for check in entity["next_checks"]
    }
    if any(item["name"] == "find_common_recipients" for item in observations):
        allowed_checks.add(PATH_NEXT_CHECK)
    findings = []
    selected_facts: dict[str, dict] = {}
    global_limits: set[str] = set()
    for item in observations:
        result = item["result"]
        if item["name"] == "find_common_recipients":
            global_limits.update(result["limitations"])
        if item["name"] == "get_subgraph" and result["truncated"]:
            global_limits.add("subgraph_truncated")
    for raw in draft["findings"]:
        if not isinstance(raw, dict) or set(raw) != {"text", "gids", "evidence_ids"}:
            raise ModelProtocolError("invalid finding shape")
        gids, ids = raw["gids"], raw["evidence_ids"]
        if (
            not isinstance(gids, list) or not isinstance(ids, list)
            or not gids or not ids or len(ids) > 8
            or any(not isinstance(value, str) for value in [*gids, *ids])
            or any(evidence_id not in facts for evidence_id in ids)
        ):
            raise ModelProtocolError("finding cites unknown or excessive evidence")
        limits = set(global_limits)
        for evidence_id in ids:
            fact = facts[evidence_id]
            selected_facts[evidence_id] = deepcopy(fact)
            limits.update(fact["limitations"])
        for gid in gids:
            if gid in entities:
                limits.update(entities[gid]["limitations"])
        findings.append({"text": raw["text"], "gids": gids,
                         "evidence_ids": ids, "limitations": sorted(limits)})
    response_limits = set(global_limits)
    for finding in findings:
        response_limits.update(finding["limitations"])
    checks = [check for check in draft["next_checks"]
              if isinstance(check, str) and check in allowed_checks][:3]
    return FinalAction(findings, list(selected_facts.values()), sorted(response_limits),
                       checks, model_text=True)


class OpenAIInvestigatorModel:
    """Stateless per-request adapter; safe to share across concurrent API calls."""

    def __init__(self, client: Any, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model

    async def _create(self, **kwargs: Any) -> Any:
        LOG.info("Investigator model invoked: %s", self.model)
        try:
            return await self.client.responses.create(
                model=self.model, instructions=INSTRUCTIONS, store=False,
                max_output_tokens=1200, **kwargs,
            )
        except Exception as error:
            kind = type(error).__name__
            if kind in {"APITimeoutError", "TimeoutError"}:
                raise TimeoutError("model request timed out") from error
            if kind in {"AuthenticationError", "PermissionDeniedError"}:
                raise ModelUnavailableError("model credentials unavailable") from error
            LOG.warning("Investigator provider request failed: %s", kind)
            raise ModelProviderError("model request failed") from error

    async def next_step(
        self, request: Mapping[str, Any], observations: Sequence[Mapping[str, Any]]
    ) -> ToolAction | FinalAction:
        if observations:
            followup = _profile_followup(observations)
            if followup is not None:
                return followup
        context = {
            "question": request["question"],
            "selected_gids": request["selected_gids"],
            "snapshot_id": request["snapshot_id"],
        }
        if not observations:
            context["phase"] = "tool_selection"
            context["instruction"] = (
                "Вызови ровно один подходящий read-only tool. selected_gids — контекст, "
                "а не обязательный фокус глобального вопроса. Для общих получателей "
                "используй несколько точных gid из вопроса или selected_gids."
            )
            response = await self._create(
                input=[{"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
                tools=TOOL_DEFINITIONS, tool_choice="required", parallel_tool_calls=False,
            )
            calls = [item for item in response.output if item.type == "function_call"]
            if len(calls) != 1 or calls[0].name not in {tool["name"] for tool in TOOL_DEFINITIONS}:
                raise ModelProtocolError("model did not select one read-only tool")
            try:
                arguments = json.loads(calls[0].arguments)
            except (TypeError, ValueError) as error:
                raise ModelProtocolError("model tool arguments are not JSON") from error
            if not isinstance(arguments, dict):
                raise ModelProtocolError("model tool arguments must be an object")
            LOG.info("Investigator tool selected: %s", calls[0].name)
            return ToolAction(calls[0].name, arguments)
        payload = {"request": context,
                   "instruction": (
                       "Сформируй JSON с максимум тремя краткими findings на основе "
                       "verified_tool_observations. Ссылайся только на показанные "
                       "evidence_ids и соответствующие gids. В text не пиши цифры, "
                       "gid или score. Если evidence нет или недостаточно, findings=[]; "
                       "не придумывай связь или профиль. next_checks выбирай только "
                       "из показанных next_checks."
                   ),
                   "verified_tool_observations": [_short_observation(item) for item in observations]}
        response = await self._create(
            input=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            text={"format": FINAL_FORMAT},
        )
        try:
            draft = json.loads(response.output_text)
        except (AttributeError, TypeError, ValueError) as error:
            raise ModelProtocolError("model final response is not JSON") from error
        if not isinstance(draft, dict):
            raise ModelProtocolError("model final response must be an object")
        return _final_action(draft, observations)


def model_from_environment() -> OpenAIInvestigatorModel | None:
    """Enable AI only when credentials and the optional SDK are present."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI
    except ImportError:
        LOG.warning("Investigator unavailable: OpenAI SDK is not installed")
        return None
    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    client = AsyncOpenAI(api_key=api_key, timeout=15.0, max_retries=0)
    return OpenAIInvestigatorModel(client, model)
