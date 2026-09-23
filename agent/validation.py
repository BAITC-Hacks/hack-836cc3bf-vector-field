"""Reference and fact validation for contract v1 InvestigationResponse.

The caller supplies only results of tool calls actually executed against the
current snapshot, plus the recorded calls. This module checks exact facts and
references; it cannot prove the meaning of model-written prose.
"""

import json
from typing import Any, Collection, Mapping, Sequence

from .boundary import LIMITS, require_gid
from .evidence import common_recipient_evidence


class ValidationError(ValueError):
    pass


def _fail(message: str) -> None:
    raise ValidationError(message)


def _object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label} must be an object")
    return value


def _array(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(f"{label} must be an array")
    return value


def _strings(value: Any, label: str) -> list[str]:
    items = _array(value, label)
    if any(not isinstance(item, str) for item in items):
        _fail(f"{label} must contain strings")
    return items


def _same_json(left: Any, right: Any) -> bool:
    try:
        return json.dumps(left, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(
            right, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
    except (TypeError, ValueError) as error:
        raise ValidationError("value is not finite JSON") from error


def _meta_matches(meta: Any, expected_meta: Mapping[str, Any]) -> bool:
    return isinstance(meta, Mapping) and _same_json(meta, expected_meta)


def validate_investigation_response(
    response: Mapping[str, Any],
    *,
    expected_meta: Mapping[str, Any],
    known_gids: Collection[str],
    trusted_tool_results: Sequence[Mapping[str, Any]],
    executed_tool_calls: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return a validated copy or raise ValidationError.

    `known_gids` must come from the current snapshot service, not the model.
    `trusted_tool_results` and `executed_tool_calls` are backend records, never
    model-supplied copies. Each tool result must carry the same snapshot meta.
    """
    result = _object(response, "response")
    if not _meta_matches(result.get("meta"), expected_meta):
        _fail("SNAPSHOT_MISMATCH: response meta differs from current snapshot")
    if len(executed_tool_calls) > LIMITS.max_calls:
        _fail("too many tool calls")
    allowed_tools = {
        "get_entity_profile", "get_subgraph", "rank_entities", "find_common_recipients"
    }
    for call in executed_tool_calls:
        if not isinstance(call, Mapping) or call.get("name") not in allowed_tools:
            _fail("invalid executed tool call")
    if not _same_json(result.get("tool_calls"), list(executed_tool_calls)):
        _fail("tool_calls differ from the execution log")

    facts: dict[str, Mapping[str, Any]] = {}
    entity_limitations: dict[str, set[str]] = {}
    global_limitations: set[str] = set()
    for index, raw in enumerate(trusted_tool_results):
        tool_result = _object(raw, f"trusted_tool_results[{index}]")
        if not _meta_matches(tool_result.get("meta"), expected_meta):
            _fail("SNAPSHOT_MISMATCH: tool result differs from current snapshot")
        entity = tool_result.get("entity")
        if isinstance(entity, Mapping):
            gid = entity.get("gid")
            if gid not in known_gids:
                _fail("trusted entity gid absent from snapshot")
            entity_limitations.setdefault(gid, set()).update(
                _strings(entity.get("limitations"), "entity.limitations")
            )
            for fact in _array(entity.get("evidence"), "entity.evidence"):
                fact = _object(fact, "trusted evidence")
                evidence_id = fact.get("evidence_id")
                if not isinstance(evidence_id, str) or not evidence_id:
                    _fail("trusted evidence has invalid evidence_id")
                if fact.get("gid") != gid:
                    _fail("trusted evidence gid differs from entity gid")
                if evidence_id in facts and not _same_json(facts[evidence_id], fact):
                    _fail("conflicting trusted evidence_id")
                facts[evidence_id] = fact
        for node in tool_result.get("nodes", []):
            node = _object(node, "subgraph node")
            gid = node.get("gid")
            if gid not in known_gids:
                _fail("trusted subgraph gid absent from snapshot")
            entity_limitations.setdefault(gid, set()).update(
                _strings(node.get("limitations"), "node.limitations")
            )
        if tool_result.get("truncated") and "center_gid" in tool_result:
            global_limitations.add("subgraph_truncated")
        if "selected_gids" in tool_result and "mode" in tool_result:
            global_limitations.update(_strings(tool_result.get("limitations"), "tool limitations"))
            try:
                derived = common_recipient_evidence(tool_result)
            except ValueError as error:
                raise ValidationError(f"invalid trusted common-recipient result: {error}") from error
            for fact in derived:
                if fact["gid"] not in known_gids:
                    _fail("common-recipient evidence gid absent from snapshot")
                evidence_id = fact["evidence_id"]
                if evidence_id in facts and not _same_json(facts[evidence_id], fact):
                    _fail("conflicting trusted evidence_id")
                facts[evidence_id] = fact

    status = result.get("status")
    if status not in {"completed", "unavailable", "timeout", "failed"}:
        _fail("invalid investigation status")
    findings = _array(result.get("findings"), "findings")
    evidence = _array(result.get("evidence"), "evidence")
    result_limitations = set(_strings(result.get("limitations"), "limitations"))
    _strings(result.get("next_checks"), "next_checks")
    if status != "completed" and (findings or evidence):
        _fail("non-completed investigation cannot contain findings or evidence")

    returned_facts: dict[str, Mapping[str, Any]] = {}
    required_evidence_limitations: set[str] = set()
    for raw_fact in evidence:
        fact = _object(raw_fact, "response evidence")
        evidence_id = fact.get("evidence_id")
        if not isinstance(evidence_id, str) or evidence_id in returned_facts:
            _fail("duplicate or invalid response evidence_id")
        if evidence_id not in facts or not _same_json(fact, facts[evidence_id]):
            _fail(f"evidence {evidence_id} differs from trusted tool fact")
        returned_facts[evidence_id] = fact
        required_evidence_limitations.update(_strings(fact.get("limitations"), "fact.limitations"))

    required_result_limitations = global_limitations | required_evidence_limitations
    for index, raw_finding in enumerate(findings):
        finding = _object(raw_finding, f"findings[{index}]")
        gids = _strings(finding.get("gids"), "finding.gids")
        ids = _strings(finding.get("evidence_ids"), "finding.evidence_ids")
        finding_limitations = set(_strings(finding.get("limitations"), "finding.limitations"))
        if not isinstance(finding.get("text"), str):
            _fail("finding.text must be a string")
        if any(character.isdigit() for character in finding["text"]):
            _fail("finding.text must not contain model-written numerals; render numbers from facts")
        if not gids or not ids or len(gids) != len(set(gids)) or len(ids) != len(set(ids)):
            _fail("finding needs unique gids and evidence_ids")
        for gid in gids:
            try:
                require_gid(gid)
            except ValueError as error:
                raise ValidationError(str(error)) from error
            if gid not in known_gids:
                _fail(f"finding gid {gid} absent from snapshot")
        cited_gids: set[str] = set()
        required_finding_limitations: set[str] = set()
        for evidence_id in ids:
            if evidence_id not in returned_facts:
                _fail(f"finding evidence_id {evidence_id} not resolved in response")
            fact = returned_facts[evidence_id]
            cited_gids.add(fact["gid"])
            required_finding_limitations.update(_strings(fact.get("limitations"), "fact.limitations"))
        if not set(gids).issubset(cited_gids):
            _fail("every finding gid needs a cited trusted fact for that gid")
        for gid in gids:
            required_finding_limitations.update(entity_limitations.get(gid, set()))
        if not required_finding_limitations.issubset(finding_limitations):
            _fail("finding omits limitations of cited facts or entity")
        required_result_limitations.update(required_finding_limitations)
        required_result_limitations.update(finding_limitations)
    if not required_result_limitations.issubset(result_limitations):
        _fail("result omits limitations from findings or tool results")

    # Round-trip also rejects NaN/Infinity. It provides a copy that the caller
    # can safely serialize without retaining a model-owned mutable object.
    try:
        return json.loads(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise ValidationError("response is not finite JSON") from error
