"""Real Parquet -> snapshot -> HTTP and all four Investigator tools."""

import asyncio
from collections import defaultdict
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from agent.boundary import ToolLimits
from agent.session import ToolSession
from backend.app import create_app
from backend.service import EntityNotFound, InvestigatorProvider, SnapshotService
from pipeline.run import DEFAULT_DATA, analyze, load_and_validate
from pipeline.snapshot import build_snapshot


class LiveIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodes, edges, tx = load_and_validate(DEFAULT_DATA)
        cls.analysis = analyze(nodes, edges, tx)
        cls.snapshot = build_snapshot(cls.analysis, nodes, edges, DEFAULT_DATA)
        cls.service = SnapshotService(cls.snapshot)
        cls.provider = InvestigatorProvider(cls.service)
        cls.client = TestClient(create_app(service=cls.service, static_dir=Path("no-frontend-build")))
        cls.isolate = next(gid for gid, p in cls.service.profiles.items() if "isolated_seed" in p["limitations"])
        cls.boundary = next(gid for gid, p in cls.service.profiles.items() if p["depth"] == 4)
        incoming = defaultdict(list)
        for edge in cls.service.edges:
            incoming[edge["dst"]].append(edge["src"])
        cls.common_target, senders = next((dst, srcs) for dst, srcs in incoming.items() if len(srcs) >= 2)
        cls.common_sources = senders[:2]

    def test_snapshot_and_all_four_tools_share_exact_facts(self):
        service = self.service
        self.assertEqual(service.meta["data_mode"], "live")
        self.assertEqual(len(service.known_gids), 2248)
        self.assertEqual(service.summary()["counts"]["n_isolates"], 19)
        gid = self.common_target

        async def check():
            session = ToolSession(self.provider, meta=service.meta, known_gids=service.known_gids)
            profile = await session.call("get_entity_profile", {"gid": gid})
            graph = await session.call("get_subgraph", {"gid": gid, "hops": 1, "limit": 2})
            ranked = await session.call("rank_entities", {"role": None, "cluster_id": None, "limit": 20})
            common = await session.call("find_common_recipients", {
                "gids": self.common_sources, "max_hops": 1, "limit": 50,
            })
            return session, profile, graph, ranked, common

        session, profile, graph, ranked, common = asyncio.run(check())
        self.assertTrue(all(item["meta"] == service.meta for item in (profile, graph, ranked, common)))
        self.assertEqual(profile["entity"]["gid"], gid)
        self.assertEqual(profile["entity"]["priority_score"], service.profiles[gid]["priority_score"])
        self.assertEqual(len([fact for fact in profile["entity"]["evidence"] if fact["rule_id"] == "priority_v0"]), 6)
        self.assertEqual(graph["center_gid"], gid)
        self.assertTrue(graph["truncated"])
        self.assertGreater(graph["omitted_count"], 0)
        self.assertEqual(len(ranked["items"]), 20)
        self.assertEqual(ranked["items"][0]["gid"], service.summary()["top_nodes"][0]["gid"])
        self.assertIn(self.common_target, [item["gid"] for item in common["items"]])
        self.assertEqual(common["mode"], "direct")
        self.assertIn("path_not_money_provenance", common["limitations"])
        for item in common["items"]:
            for path in item["paths"]:
                self.assertEqual(path["gids"][0], path["source_gid"])
                self.assertEqual(path["gids"][-1], item["gid"])
                self.assertTrue(all(isinstance(x, str) for x in path["gids"]))
        self.assertEqual([call["status"] for call in session.calls], ["completed"] * 4)

    def test_empty_unknown_isolate_boundary_and_timeout(self):
        service = self.service
        empty = service.find_common_recipients({
            "gids": [self.isolate, self.common_sources[0]], "max_hops": 4, "limit": 50,
        })
        self.assertEqual(empty["items"], [])
        self.assertEqual(empty["total"], 0)
        isolated = service.get_subgraph(self.isolate)
        self.assertEqual([node["gid"] for node in isolated["nodes"]], [self.isolate])
        self.assertEqual(isolated["edges"], [])
        self.assertFalse(isolated["truncated"])
        boundary = service.get_entity(self.boundary)["entity"]
        self.assertIn("depth_truncated", boundary["limitations"])
        self.assertNotEqual(boundary["role"], "terminal")
        with self.assertRaises(EntityNotFound):
            service.get_entity("999999999999999999")

        class SlowProvider(InvestigatorProvider):
            async def get_entity_profile(self, gid):
                await asyncio.sleep(0.05)
                return await super().get_entity_profile(gid)

        session = ToolSession(SlowProvider(service), meta=service.meta, known_gids=service.known_gids,
                              limits=ToolLimits(timeout_seconds=0.001))
        async def time_out():
            with self.assertRaises(TimeoutError):
                await session.call("get_entity_profile", {"gid": self.isolate})
        asyncio.run(time_out())
        self.assertEqual(session.calls[0]["status"], "failed")

    def test_http_live_core_errors_and_ai_outage(self):
        client = self.client
        gid = self.common_target
        summary = client.get("/api/summary")
        self.assertEqual(summary.status_code, 200)
        snapshot_id = summary.json()["meta"]["snapshot_id"]
        self.assertEqual(client.get(f"/api/entities/{gid}").json()["entity"]["gid"], gid)
        self.assertEqual(client.get("/api/entities", params={"offset": 0, "limit": 20}).json()["total"], 2248)
        self.assertEqual(client.get("/api/subgraph", params={"gid": self.isolate}).json()["edges"], [])
        self.assertEqual(len(client.get("/api/clusters").json()["items"]), 105)
        self.assertEqual(client.get("/api/entities/999999999999999999").status_code, 404)
        self.assertEqual(client.get("/api/subgraph", params={"gid": gid, "hops": 3}).status_code, 422)
        self.assertEqual(client.get("/api/export/nope.csv").status_code, 422)
        request = {"question": "Какие признаки у узла?", "selected_gids": [gid], "snapshot_id": snapshot_id}
        unavailable = client.post("/api/investigate", json=request)
        self.assertEqual(unavailable.status_code, 200)
        self.assertEqual(unavailable.json()["status"], "unavailable")
        self.assertEqual(unavailable.json()["findings"], [])
        self.assertEqual(client.post("/api/investigate", json=request | {"snapshot_id": "stale"}).status_code, 409)
        self.assertEqual(client.post("/api/investigate", json=request | {"selected_gids": ["999999999999999999"]}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
