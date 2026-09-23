"""Explicit fixture-only adapter for local contract checks.

It serves only examples present in shared/fixtures.json. It never calculates live
analytics or invents a profile for a gid lacking a fixture response.
"""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .boundary import LIMITS, ROLES, require_gid, require_int


class EntityNotFound(LookupError):
    pass


class FixtureUnavailable(LookupError):
    pass


class FixtureProvider:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(__file__).resolve().parents[1] / "shared" / "fixtures.json"
        with self.path.open(encoding="utf-8") as handle:
            self._fixture = json.load(handle)
        self.meta: dict[str, Any] = deepcopy(self._fixture["summary"]["meta"])
        if self.meta["data_mode"] != "fixture":
            raise ValueError("FixtureProvider requires data_mode=fixture")
        self.known_gids = frozenset(item["gid"] for item in self._fixture["entities"]["items"])
        self._profiles = {
            self._fixture[key]["entity"]["gid"]: self._fixture[key]
            for key in ("entity", "entity_isolate", "entity_boundary")
        }

    def _known(self, gid: str) -> str:
        require_gid(gid)
        if gid not in self.known_gids:
            raise EntityNotFound(f"ENTITY_NOT_FOUND: {gid}")
        return gid

    async def get_entity_profile(self, gid: str) -> dict[str, Any]:
        gid = self._known(gid)
        if gid not in self._profiles:
            raise FixtureUnavailable(f"No fixture-only profile for gid {gid}")
        return deepcopy(self._profiles[gid])

    async def get_subgraph(
        self, gid: str, hops: int = 1, limit: int = 80
    ) -> dict[str, Any]:
        gid = self._known(gid)
        require_int(hops, name="hops", minimum=1, maximum=LIMITS.subgraph_hops_max)
        require_int(limit, name="limit", minimum=1, maximum=LIMITS.subgraph_limit_max)
        if gid == self._fixture["subgraph_isolate"]["center_gid"] and hops == 1:
            return deepcopy(self._fixture["subgraph_isolate"])
        full = self._fixture["subgraph"]
        if gid == full["center_gid"] and hops == 1:
            if limit >= full["total_nodes"]:
                return deepcopy(full)
            if limit == 2:
                return deepcopy(self._fixture["subgraph_truncated"])
        raise FixtureUnavailable(f"No fixture-only subgraph for gid={gid}, hops={hops}, limit={limit}")

    async def rank_entities(
        self, role: str | None = None, cluster_id: int | None = None, limit: int = 20
    ) -> dict[str, Any]:
        if role is not None and role not in ROLES:
            raise ValueError("invalid role")
        if cluster_id is not None:
            require_int(cluster_id, name="cluster_id", minimum=0)
        require_int(limit, name="limit", minimum=1, maximum=LIMITS.list_limit_max)
        items = [
            item for item in self._fixture["entities"]["items"]
            if (role is None or item["role"] == role)
            and (cluster_id is None or item["cluster_id"] == cluster_id)
        ]
        items.sort(key=lambda item: (-item["priority_score"], int(item["gid"])))
        return {
            "meta": deepcopy(self.meta),
            "items": deepcopy(items[:limit]),
            "total": len(items),
            "offset": 0,
            "limit": limit,
        }

    async def find_common_recipients(self, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict) or set(request) != {"gids", "max_hops", "limit"}:
            raise ValueError("request must match CommonRecipientsRequest")
        gids = request["gids"]
        if not isinstance(gids, list):
            raise ValueError("gids must be an array")
        require_int(len(gids), name="gids length", minimum=1, maximum=LIMITS.selected_gids_max)
        for gid in gids:
            self._known(gid)
        if len(set(gids)) != len(gids):
            raise ValueError("gids must be unique")
        hops = require_int(request["max_hops"], name="max_hops", minimum=1, maximum=LIMITS.common_hops_max)
        limit = require_int(request["limit"], name="limit", minimum=1, maximum=LIMITS.common_limit_max)
        for key in ("common_recipients", "common_recipients_empty"):
            response = self._fixture[key]
            if gids == response["selected_gids"] and hops == response["max_hops"]:
                if response["total"] <= limit:
                    return deepcopy(response)
        raise FixtureUnavailable("No fixture-only common-recipient result for these inputs")
