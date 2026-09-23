"""Bounded execution of the four read-only Investigator tools.

The session records actual results and calls for deterministic validation. It
never reads Parquet or computes graph analytics: the injected provider owns the
snapshot service implementation.
"""

import asyncio
from copy import deepcopy
import json
from time import monotonic
from typing import Any, Collection, Mapping

from .boundary import InvestigatorTools, LIMITS, ROLES, ToolLimits, require_gid, require_int
from .evidence import common_recipient_evidence


class ToolLimitExceeded(RuntimeError):
    pass


class SnapshotMismatch(RuntimeError):
    pass


class ToolSession:
    """One question, one snapshot, at most six serial tool attempts."""

    def __init__(
        self,
        provider: InvestigatorTools,
        *,
        meta: Mapping[str, Any],
        known_gids: Collection[str],
        limits: ToolLimits = LIMITS,
    ):
        self.provider = provider
        self.meta = deepcopy(dict(meta))
        self.known_gids = frozenset(known_gids)
        self.limits = limits
        self._deadline = monotonic() + limits.timeout_seconds
        self._lock = asyncio.Lock()
        self._calls: list[dict[str, Any]] = []
        self._results: list[dict[str, Any]] = []

    @property
    def calls(self) -> list[dict[str, Any]]:
        return deepcopy(self._calls)

    @property
    def results(self) -> list[dict[str, Any]]:
        return deepcopy(self._results)

    @staticmethod
    def evidence_for_result(name: str, result: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Facts exposed to the model alongside a bounded tool result."""
        if name == "get_entity_profile":
            return deepcopy(result["entity"]["evidence"])
        if name == "find_common_recipients":
            return common_recipient_evidence(result)
        return []

    def remaining_seconds(self) -> float:
        return max(0.0, self._deadline - monotonic())

    def _known_gid(self, gid: Any) -> str:
        require_gid(gid)
        if gid not in self.known_gids:
            raise LookupError(f"ENTITY_NOT_FOUND: {gid}")
        return gid

    def validate_request(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Validate contract v1 InvestigationRequest before any model call."""
        if not isinstance(request, Mapping) or set(request) != {
            "question", "selected_gids", "snapshot_id"
        }:
            raise ValueError("request must match InvestigationRequest")
        question = request["question"]
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
            raise ValueError("question must contain 1..2000 characters after trim")
        gids = request["selected_gids"]
        if not isinstance(gids, list) or len(gids) > self.limits.selected_gids_max:
            raise ValueError("selected_gids must be an array of up to 20 gids")
        for gid in gids:
            self._known_gid(gid)
        if len(set(gids)) != len(gids):
            raise ValueError("selected_gids must be unique")
        if not isinstance(request["snapshot_id"], str):
            raise ValueError("snapshot_id must be a string")
        if request["snapshot_id"] != self.meta.get("snapshot_id"):
            raise SnapshotMismatch("SNAPSHOT_MISMATCH")
        return {
            "question": question.strip(),
            "selected_gids": list(gids),
            "snapshot_id": request["snapshot_id"],
        }

    def _arguments(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, Mapping):
            raise ValueError("tool arguments must be an object")
        args = dict(arguments)
        if name == "get_entity_profile":
            if set(args) != {"gid"}:
                raise ValueError("get_entity_profile requires only gid")
            return {"gid": self._known_gid(args["gid"])}
        if name == "get_subgraph":
            if "gid" not in args or set(args) - {"gid", "hops", "limit"}:
                raise ValueError("get_subgraph accepts gid, hops, limit")
            return {
                "gid": self._known_gid(args["gid"]),
                "hops": require_int(args.get("hops", 1), name="hops", minimum=1,
                                    maximum=self.limits.subgraph_hops_max),
                "limit": require_int(args.get("limit", 80), name="limit", minimum=1,
                                     maximum=self.limits.subgraph_limit_max),
            }
        if name == "rank_entities":
            if set(args) - {"role", "cluster_id", "limit"}:
                raise ValueError("rank_entities accepts role, cluster_id, limit")
            role = args.get("role")
            if role is not None and role not in ROLES:
                raise ValueError("invalid role")
            cluster_id = args.get("cluster_id")
            if cluster_id is not None:
                require_int(cluster_id, name="cluster_id", minimum=0)
            return {
                "role": role,
                "cluster_id": cluster_id,
                "limit": require_int(args.get("limit", 20), name="limit", minimum=1,
                                     maximum=self.limits.list_limit_max),
            }
        if name == "find_common_recipients":
            if set(args) != {"gids", "max_hops", "limit"}:
                raise ValueError("find_common_recipients requires gids, max_hops, limit")
            gids = args["gids"]
            if not isinstance(gids, list):
                raise ValueError("gids must be an array")
            require_int(len(gids), name="gids length", minimum=1,
                        maximum=self.limits.selected_gids_max)
            for gid in gids:
                self._known_gid(gid)
            if len(set(gids)) != len(gids):
                raise ValueError("gids must be unique")
            return {
                "gids": list(gids),
                "max_hops": require_int(args["max_hops"], name="max_hops", minimum=1,
                                        maximum=self.limits.common_hops_max),
                "limit": require_int(args["limit"], name="limit", minimum=1,
                                     maximum=self.limits.common_limit_max),
            }
        raise ValueError(f"unknown tool: {name}")

    def _check_result(self, name: str, args: dict[str, Any], raw: Any) -> tuple[dict[str, Any], list[str]]:
        if not isinstance(raw, dict) or raw.get("meta") != self.meta:
            raise SnapshotMismatch("SNAPSHOT_MISMATCH: tool response meta")
        try:
            result = json.loads(json.dumps(raw, ensure_ascii=False, allow_nan=False))
        except (TypeError, ValueError) as error:
            raise ValueError("tool response is not finite JSON") from error
        if name == "get_entity_profile":
            entity = result.get("entity")
            if not isinstance(entity, dict) or entity.get("gid") != args["gid"]:
                raise ValueError("profile gid does not match request")
            evidence = entity.get("evidence")
            if not isinstance(evidence, list):
                raise ValueError("profile evidence must be an array")
            ids = []
            for fact in evidence:
                if not isinstance(fact, dict) or fact.get("gid") != args["gid"]:
                    raise ValueError("profile evidence gid mismatch")
                evidence_id = fact.get("evidence_id")
                if not isinstance(evidence_id, str) or not evidence_id:
                    raise ValueError("invalid evidence_id")
                if (
                    not isinstance(fact.get("metric"), str)
                    or not isinstance(fact.get("rule_id"), str)
                    or not isinstance(fact.get("scope"), str)
                    or not isinstance(fact.get("text"), str)
                    or fact.get("unit") not in {"count", "KZT", "ratio", "text"}
                    or fact.get("source") not in {
                        "nodes.parquet", "edges.parquet", "transactions.parquet", "derived"
                    }
                    or not isinstance(fact.get("limitations"), list)
                    or any(not isinstance(code, str) for code in fact["limitations"])
                    or type(fact.get("value")) not in (int, float, str, type(None))
                ):
                    raise ValueError("profile evidence differs from contract v1")
                ids.append(evidence_id)
            if len(set(ids)) != len(ids):
                raise ValueError("duplicate profile evidence_id")
            return result, ids
        if name == "get_subgraph":
            nodes, edges = result.get("nodes"), result.get("edges")
            if (result.get("center_gid") != args["gid"] or result.get("hops") != args["hops"]
                    or not isinstance(nodes, list) or not isinstance(edges, list)
                    or len(nodes) > args["limit"]):
                raise ValueError("invalid subgraph response")
            gids = [node.get("gid") for node in nodes if isinstance(node, dict)]
            if len(gids) != len(nodes) or len(set(gids)) != len(gids) or args["gid"] not in gids:
                raise ValueError("subgraph nodes must include unique center gid")
            for gid in gids:
                self._known_gid(gid)
            for edge in edges:
                if not isinstance(edge, dict) or edge.get("src") not in gids or edge.get("dst") not in gids:
                    raise ValueError("subgraph edge endpoint not shown")
            total_nodes, total_edges = result.get("total_nodes"), result.get("total_edges")
            if (type(total_nodes) is not int or type(total_edges) is not int
                    or total_nodes < len(nodes) or total_edges < len(edges)
                    or result.get("omitted_count") != total_nodes - len(nodes)
                    or result.get("omitted_edges") != total_edges - len(edges)
                    or result.get("truncated") != (total_nodes > len(nodes) or total_edges > len(edges))):
                raise ValueError("subgraph truncation counts disagree")
            return result, []
        if name == "rank_entities":
            items = result.get("items")
            if (not isinstance(items, list) or len(items) > args["limit"]
                    or result.get("offset") != 0 or result.get("limit") != args["limit"]
                    or type(result.get("total")) is not int or result["total"] < len(items)):
                raise ValueError("invalid ranked list response")
            previous: tuple[float, int] | None = None
            seen_gids: set[str] = set()
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError("invalid ranked item")
                gid = self._known_gid(item.get("gid"))
                if gid in seen_gids:
                    raise ValueError("duplicate gid in ranked list")
                seen_gids.add(gid)
                if args["role"] is not None and item.get("role") != args["role"]:
                    raise ValueError("ranked item role differs from filter")
                if args["cluster_id"] is not None and item.get("cluster_id") != args["cluster_id"]:
                    raise ValueError("ranked item cluster differs from filter")
                score = item.get("priority_score")
                if type(score) not in (int, float) or not 0 <= score <= 1:
                    raise ValueError("invalid priority_score")
                key = (-score, int(gid))
                if previous is not None and key < previous:
                    raise ValueError("ranked list order differs from contract")
                previous = key
            return result, []
        if name == "find_common_recipients":
            if (result.get("selected_gids") != args["gids"]
                    or result.get("max_hops") != args["max_hops"]
                    or not isinstance(result.get("items"), list)
                    or len(result["items"]) > args["limit"]):
                raise ValueError("common-recipient response differs from request")
            facts = common_recipient_evidence(result)
            for item in result["items"]:
                self._known_gid(item["gid"])
                for path in item["paths"]:
                    for gid in path["gids"]:
                        self._known_gid(gid)
            return result, [fact["evidence_id"] for fact in facts]
        raise AssertionError("unreachable tool dispatch")

    async def call(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if name not in {
            "get_entity_profile", "get_subgraph", "rank_entities", "find_common_recipients"
        }:
            raise ValueError(f"unknown tool: {name}")
        async with self._lock:
            if len(self._calls) >= self.limits.max_calls:
                raise ToolLimitExceeded("maximum six tool calls reached")
            start = monotonic()
            ids: list[str] = []
            completed = False
            try:
                args = self._arguments(name, arguments)
                remaining = self.remaining_seconds()
                if remaining <= 0:
                    raise TimeoutError("Investigator deadline exceeded")
                if name == "get_entity_profile":
                    operation = self.provider.get_entity_profile(**args)
                elif name == "get_subgraph":
                    operation = self.provider.get_subgraph(**args)
                elif name == "rank_entities":
                    operation = self.provider.rank_entities(**args)
                else:
                    operation = self.provider.find_common_recipients(args)
                raw = await asyncio.wait_for(operation, timeout=remaining)
                result, ids = self._check_result(name, args, raw)
                self._results.append(result)
                completed = True
                return deepcopy(result)
            except asyncio.TimeoutError as error:
                raise TimeoutError("Investigator tool timed out") from error
            finally:
                self._calls.append({
                    "name": name,
                    "status": "completed" if completed else "failed",
                    "duration_ms": max(0, int((monotonic() - start) * 1000)),
                    "evidence_ids": ids,
                })

    def validate(self, response: Mapping[str, Any]) -> dict[str, Any]:
        from .validation import validate_investigation_response

        return validate_investigation_response(
            response,
            expected_meta=self.meta,
            known_gids=self.known_gids,
            trusted_tool_results=self.results,
            executed_tool_calls=self.calls,
        )
