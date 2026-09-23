"""One bounded Investigator loop with an injectable model adapter.

This module has no SDK or API-key dependency. It can be tested with scripted
model steps while the backend snapshot and live provider are unfinished.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Collection, Mapping, Protocol, Sequence

from .boundary import InvestigatorTools, LIMITS, ToolLimits
from .session import ToolSession

PATH_NEXT_CHECK = "Запросить точное время переводов и подтверждение связи операций."


def _finding_text(finding: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> str:
    """Use controlled wording; model prose is never treated as verified fact."""
    cited = set(finding.get("evidence_ids", []))
    metrics = {fact.get("metric") for fact in evidence if fact.get("evidence_id") in cited}
    if "common_recipient_path" in metrics or "common_recipient_sources" in metrics:
        return "Наблюдаются направленные пути к общему получателю; происхождение средств не установлено."
    if any(isinstance(metric, str) and metric.startswith("priority_component_") for metric in metrics):
        return "Узел включён в очередь проверки по рассчитанным признакам приоритета."
    return "Для узла приведены наблюдаемые признаки; вывод о роли требует дополнительной проверки."


def _trusted_next_checks(session: ToolSession, proposed: Sequence[str]) -> list[str]:
    allowed: set[str] = set()
    for result in session.results:
        entity = result.get("entity")
        if isinstance(entity, dict):
            allowed.update(entity.get("next_checks", []))
        if "selected_gids" in result and "mode" in result:
            allowed.add(PATH_NEXT_CHECK)
    return list(dict.fromkeys(check for check in proposed if check in allowed))


@dataclass(frozen=True)
class ToolAction:
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True)
class FinalAction:
    findings: Sequence[Mapping[str, Any]]
    evidence: Sequence[Mapping[str, Any]]
    limitations: Sequence[str]
    next_checks: Sequence[str]


class InvestigatorModel(Protocol):
    async def next_step(
        self, request: Mapping[str, Any], observations: Sequence[Mapping[str, Any]]
    ) -> ToolAction | FinalAction:
        """Return a tool request or structured final draft, never raw prose."""


def _failure(
    session: ToolSession, status: str, message: str
) -> dict[str, Any]:
    limitations: set[str] = set()
    for result in session.results:
        if "selected_gids" in result and "mode" in result:
            limitations.update(result.get("limitations", []))
        if result.get("truncated") and "center_gid" in result:
            limitations.add("subgraph_truncated")
    return {
        "meta": session.meta,
        "status": status,
        "message": message,
        "findings": [],
        "evidence": [],
        "limitations": sorted(limitations),
        "next_checks": [],
        "tool_calls": session.calls,
    }


async def investigate(
    request: Mapping[str, Any],
    tools: InvestigatorTools,
    model: InvestigatorModel | None,
    *,
    meta: Mapping[str, Any],
    known_gids: Collection[str],
    limits: ToolLimits = LIMITS,
) -> dict[str, Any]:
    """Run at most six tool calls and return contract v1 InvestigationResponse.

    Request validation errors propagate for backend HTTP 422/404/409 mapping.
    Model/tool failures become explicit non-completed responses. No facts are
    accepted from a model unless `ToolSession.validate` verifies them.
    """
    session = ToolSession(tools, meta=meta, known_gids=known_gids, limits=limits)
    clean_request = session.validate_request(request)
    if model is None:
        return _failure(session, "unavailable", "Investigator недоступен.")

    observations: list[dict[str, Any]] = []
    try:
        for _ in range(limits.max_calls + 1):
            remaining = session.remaining_seconds()
            if remaining <= 0:
                raise TimeoutError("Investigator deadline exceeded")
            action = await asyncio.wait_for(
                model.next_step(clean_request, tuple(observations)), timeout=remaining
            )
            if isinstance(action, ToolAction):
                result = await session.call(action.name, action.arguments)
                observations.append({
                    "name": action.name,
                    "arguments": dict(action.arguments),
                    "result": result,
                })
                continue
            if isinstance(action, FinalAction):
                evidence = [dict(fact) for fact in action.evidence]
                findings = [
                    {**dict(finding), "text": _finding_text(finding, evidence)}
                    for finding in action.findings
                ]
                candidate = {
                    "meta": session.meta,
                    "status": "completed",
                    "message": "Гипотезы основаны на проверенных фактах snapshot.",
                    "findings": findings,
                    "evidence": evidence,
                    "limitations": list(action.limitations),
                    "next_checks": _trusted_next_checks(session, action.next_checks),
                    "tool_calls": session.calls,
                }
                return session.validate(candidate)
            raise ValueError("model returned an unsupported action")
        return _failure(session, "failed", "Превышен лимит вызовов инструментов.")
    except (asyncio.TimeoutError, TimeoutError):
        return _failure(session, "timeout", "Investigator превысил лимит времени.")
    except Exception:
        return _failure(session, "failed", "Ответ Investigator не прошёл проверку.")
