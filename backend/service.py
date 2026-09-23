"""One in-process source of contract v1 responses for HTTP and Investigator."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
import json
from pathlib import Path
from typing import Any


class EntityNotFound(LookupError):
    pass


def _gid(value: str) -> str:
    if not isinstance(value, str) or not value or not value.isascii() or not value.isdecimal():
        raise ValueError("gid must be a decimal string")
    return value


def _bounded(value: int, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


class SnapshotService:
    def __init__(self, snapshot: dict[str, Any]):
        if snapshot.get("meta", {}).get("contract_version") != "1" or snapshot["meta"].get("data_mode") != "live":
            raise ValueError("expected live contract v1 snapshot")
        self.snapshot = snapshot
        self.meta = deepcopy(snapshot["meta"])
        self.profiles: dict[str, dict] = snapshot["profiles"]
        self.known_gids = frozenset(self.profiles)
        self.edges: list[dict] = snapshot["edges"]
        self.out_neighbors = {gid: set() for gid in self.known_gids}
        self.neighbors = {gid: set() for gid in self.known_gids}
        for edge in self.edges:
            src, dst = edge["src"], edge["dst"]
            if src not in self.known_gids or dst not in self.known_gids:
                raise ValueError("snapshot edge has unknown endpoint")
            self.out_neighbors[src].add(dst)
            self.neighbors[src].add(dst)
            self.neighbors[dst].add(src)
        self.ranked = sorted(self.known_gids, key=self._rank_key)

    @classmethod
    def from_file(cls, path: Path) -> "SnapshotService":
        with path.open("r", encoding="utf-8") as handle:
            return cls(json.load(handle))

    def _rank_key(self, gid: str) -> tuple[float, int]:
        return (-self.profiles[gid]["priority_score"], int(gid))

    def _known(self, gid: str) -> str:
        _gid(gid)
        if gid not in self.known_gids:
            raise EntityNotFound(gid)
        return gid

    def _summary(self, gid: str) -> dict:
        p = self.profiles[gid]
        return {key: deepcopy(p[key]) for key in (
            "gid", "depth", "is_seed", "role", "role_score", "priority_score",
            "cluster_id", "why", "limitations",
        )} | {"evidence": p["evidence_text"]}

    def summary(self) -> dict:
        return {"meta": deepcopy(self.meta), **deepcopy(self.snapshot["summary"])}

    def get_entity(self, gid: str) -> dict:
        gid = self._known(gid)
        return {"meta": deepcopy(self.meta), "entity": deepcopy(self.profiles[gid])}

    def list_entities(self, *, role: str | None = None, cluster_id: int | None = None,
                      is_seed: bool | None = None, offset: int = 0, limit: int = 20) -> dict:
        _bounded(offset, "offset", 0, 2**31 - 1)
        _bounded(limit, "limit", 1, 200)
        if role is not None and role not in {
            "consolidator", "transit", "distributor", "terminal", "coordinator", "peripheral"
        }:
            raise ValueError("invalid role")
        if cluster_id is not None:
            _bounded(cluster_id, "cluster_id", 0, 2**31 - 1)
        if is_seed is not None and type(is_seed) is not bool:
            raise ValueError("is_seed must be boolean")
        gids = [gid for gid in self.ranked if
                (role is None or self.profiles[gid]["role"] == role) and
                (cluster_id is None or self.profiles[gid]["cluster_id"] == cluster_id) and
                (is_seed is None or self.profiles[gid]["is_seed"] == is_seed)]
        return {"meta": deepcopy(self.meta), "items": [self._summary(gid) for gid in gids[offset:offset + limit]],
                "total": len(gids), "offset": offset, "limit": limit}

    def get_subgraph(self, gid: str, hops: int = 1, limit: int = 80) -> dict:
        gid = self._known(gid)
        _bounded(hops, "hops", 1, 2)
        _bounded(limit, "limit", 1, 200)
        distance = {gid: 0}
        queue = deque([gid])
        while queue:
            current = queue.popleft()
            if distance[current] == hops:
                continue
            for neighbor in sorted(self.neighbors[current], key=int):
                if neighbor not in distance:
                    distance[neighbor] = distance[current] + 1
                    queue.append(neighbor)
        ordered = sorted(distance, key=lambda item: (distance[item], *self._rank_key(item)))
        shown = set(ordered[:limit])
        all_gids = set(distance)
        full_edges = [edge for edge in self.edges if edge["src"] in all_gids and edge["dst"] in all_gids]
        shown_edges = [deepcopy(edge) for edge in full_edges if edge["src"] in shown and edge["dst"] in shown]
        omitted_count = len(ordered) - len(shown)
        omitted_edges = len(full_edges) - len(shown_edges)
        return {"meta": deepcopy(self.meta), "center_gid": gid, "hops": hops,
                "nodes": [self._summary(node) for node in ordered[:limit]],
                "edges": shown_edges, "total_nodes": len(ordered), "total_edges": len(full_edges),
                "truncated": bool(omitted_count or omitted_edges),
                "omitted_count": omitted_count, "omitted_edges": omitted_edges}

    def clusters(self) -> dict:
        return {"meta": deepcopy(self.meta), "items": deepcopy(self.snapshot["clusters"])}

    def _reachable_paths(self, source: str, max_hops: int) -> dict[str, list[str]]:
        paths = {source: [source]}
        queue = deque([source])
        while queue:
            current = queue.popleft()
            if len(paths[current]) - 1 == max_hops:
                continue
            for neighbor in sorted(self.out_neighbors[current], key=int):
                if neighbor not in paths:
                    paths[neighbor] = paths[current] + [neighbor]
                    queue.append(neighbor)
        paths.pop(source)
        return paths

    def find_common_recipients(self, request: dict) -> dict:
        if not isinstance(request, dict) or set(request) != {"gids", "max_hops", "limit"}:
            raise ValueError("invalid common recipients request")
        gids = request["gids"]
        if not isinstance(gids, list) or not 1 <= len(gids) <= 20 or len(set(gids)) != len(gids):
            raise ValueError("gids must be 1..20 unique strings")
        for gid in gids:
            self._known(gid)
        max_hops = _bounded(request["max_hops"], "max_hops", 1, 4)
        limit = _bounded(request["limit"], "limit", 1, 50)
        paths = {source: self._reachable_paths(source, max_hops) for source in gids}
        common = set.intersection(*(set(paths[source]) for source in gids)) - set(gids)
        ordered = sorted(common, key=self._rank_key)
        items = [{"gid": candidate, "paths": [
            {"source_gid": source, "gids": paths[source][candidate]} for source in gids
        ]} for candidate in ordered[:limit]]
        return {"meta": deepcopy(self.meta), "selected_gids": list(gids),
                "mode": "direct" if max_hops == 1 else "reachable", "max_hops": max_hops,
                "items": items, "total": len(ordered), "truncated": len(ordered) > limit,
                "limitations": ["path_not_money_provenance", "date_only"]}


class InvestigatorProvider:
    """Async protocol facade; all four operations delegate to SnapshotService."""

    def __init__(self, service: SnapshotService):
        self.service = service

    async def get_entity_profile(self, gid: str) -> dict:
        return self.service.get_entity(gid)

    async def get_subgraph(self, gid: str, hops: int = 1, limit: int = 80) -> dict:
        return self.service.get_subgraph(gid, hops, limit)

    async def rank_entities(self, role: str | None = None, cluster_id: int | None = None,
                            limit: int = 20) -> dict:
        return self.service.list_entities(role=role, cluster_id=cluster_id, limit=limit)

    async def find_common_recipients(self, request: dict) -> dict:
        return self.service.find_common_recipients(request)
