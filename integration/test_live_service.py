"""Real Parquet -> snapshot -> HTTP and all four Investigator tools."""

import asyncio
from collections import defaultdict
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from agent import FinalAction, ToolAction
from agent.boundary import ToolLimits
from agent.openai_model import OpenAIInvestigatorModel
from agent.session import ToolSession
from backend.app import create_app
from backend.service import EntityNotFound, InvestigatorProvider, SnapshotService
from pipeline.run import CSV_COLUMNS, DEFAULT_DATA, analyze, export_csv, load_and_validate
from pipeline.snapshot import build_snapshot


class ProfileModel:
    """Scripted model that cites a fact returned by the live profile tool."""

    def __init__(self):
        self.calls = 0

    async def next_step(self, request, observations):
        self.calls += 1
        if not observations:
            return ToolAction("get_entity_profile", {"gid": request["selected_gids"][0]})
        entity = observations[0]["result"]["entity"]
        fact = observations[0]["evidence"][0]
        limitations = sorted(set(entity["limitations"]) | set(fact["limitations"]))
        return FinalAction(
            findings=[{
                "text": "Проверить наблюдаемые признаки узла.",
                "gids": [entity["gid"]],
                "evidence_ids": [fact["evidence_id"]],
                "limitations": limitations,
            }],
            evidence=[fact],
            limitations=limitations,
            next_checks=entity["next_checks"],
        )


class TimeoutModel:
    async def next_step(self, request, observations):
        raise TimeoutError("model provider timed out")


class ErrorModel:
    async def next_step(self, request, observations):
        raise RuntimeError("model provider failed")


class InvalidToolModel:
    async def next_step(self, request, observations):
        return ToolAction("get_subgraph", {
            "gid": request["selected_gids"][0], "hops": 99, "limit": 1,
        })


class FakeResponses:
    """SDK-shaped tool selection and synthesis over the real snapshot tools."""

    def __init__(self, gid, evidence_id):
        self.gid = gid
        self.evidence_id = evidence_id
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return SimpleNamespace(output=[SimpleNamespace(
                type="function_call", name="get_entity_profile",
                arguments=json.dumps({"gid": self.gid}), call_id="call-profile",
            )])
        elif len(self.calls) == 2:
            return SimpleNamespace(output_text=json.dumps({
                "findings": [{
                    "text": "Наблюдаемые признаки требуют дополнительной проверки.",
                    "gids": [self.gid], "evidence_ids": [self.evidence_id],
                }],
                "next_checks": [],
            }, ensure_ascii=False))
        else:
            raise AssertionError("unexpected model call")


class FakeOpenAIClient:
    def __init__(self, gid, evidence_id):
        self.responses = FakeResponses(gid, evidence_id)
        self.closed = False

    async def close(self):
        self.closed = True


class LiveIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodes, edges, tx = load_and_validate(DEFAULT_DATA)
        cls.analysis = analyze(nodes, edges, tx)
        cls.snapshot = build_snapshot(cls.analysis, nodes, edges, DEFAULT_DATA)
        cls.service = SnapshotService(cls.snapshot)
        cls.exports = TemporaryDirectory(prefix="hackalem-integration-")
        cls.addClassCleanup(cls.exports.cleanup)
        cls.export_dir = Path(cls.exports.name)
        export_csv(cls.analysis, cls.export_dir)
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
        self.assertEqual(client.post("/api/investigate", json=request | {"snapshot_id": None}).status_code, 422)
        self.assertEqual(client.post("/api/investigate", json=request | {"selected_gids": ["999999999999999999"]}).status_code, 404)

    def test_http_investigator_completed_uses_live_tool_evidence(self):
        gid = self.common_target
        model = ProfileModel()
        client = TestClient(create_app(service=self.service, model=model,
                                       static_dir=Path("no-frontend-build")))
        request = {"question": "Какие признаки у узла?", "selected_gids": [gid],
                   "snapshot_id": self.service.meta["snapshot_id"]}
        response = client.post("/api/investigate", json=request)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(set(result), {
            "meta", "status", "message", "findings", "evidence",
            "limitations", "next_checks", "tool_calls",
        })
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["meta"], self.service.meta)
        self.assertEqual(model.calls, 2)
        fact = self.service.get_entity(gid)["entity"]["evidence"][0]
        self.assertEqual(result["evidence"], [fact])
        self.assertEqual(result["findings"][0]["gids"], [gid])
        self.assertEqual(result["findings"][0]["evidence_ids"], [fact["evidence_id"]])
        self.assertEqual(result["tool_calls"][0]["name"], "get_entity_profile")
        self.assertEqual(result["tool_calls"][0]["status"], "completed")
        self.assertIn(fact["evidence_id"], result["tool_calls"][0]["evidence_ids"])
        self.assertIsInstance(result["findings"][0]["gids"][0], str)

    def test_http_investigator_failures_preserve_core_routes(self):
        gid = self.common_target
        request = {"question": "Какие признаки у узла?", "selected_gids": [gid],
                   "snapshot_id": self.service.meta["snapshot_id"]}
        for model, expected_status in (
            (TimeoutModel(), "timeout"),
            (ErrorModel(), "failed"),
            (InvalidToolModel(), "failed"),
        ):
            with self.subTest(model=type(model).__name__):
                client = TestClient(create_app(service=self.service, model=model,
                                               snapshot_path=self.export_dir / "snapshot.json",
                                               static_dir=Path("no-frontend-build")))
                response = client.post("/api/investigate", json=request)
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertEqual(result["status"], expected_status)
                self.assertEqual(result["meta"], self.service.meta)
                self.assertEqual(result["findings"], [])
                self.assertEqual(result["evidence"], [])
                if isinstance(model, InvalidToolModel):
                    self.assertEqual(len(result["tool_calls"]), 1)
                    self.assertEqual(result["tool_calls"][0]["status"], "failed")
                self.assertEqual(client.get("/api/summary").json()["counts"]["n_nodes"], 2248)
                self.assertEqual(client.get(f"/api/entities/{gid}").json()["entity"]["gid"], gid)
                self.assertEqual(client.get("/api/subgraph", params={"gid": gid}).status_code, 200)
                for filename, columns in CSV_COLUMNS.items():
                    exported = client.get(f"/api/export/{filename}")
                    self.assertEqual(exported.status_code, 200)
                    self.assertEqual(exported.content, (self.export_dir / filename).read_bytes())
                    self.assertEqual(exported.text.splitlines()[0], ",".join(columns))
                    self.assertIn("attachment", exported.headers["content-disposition"])

    def test_http_investigator_rejects_unknown_or_numeric_gid_before_model(self):
        model = ProfileModel()
        client = TestClient(create_app(service=self.service, model=model,
                                       static_dir=Path("no-frontend-build")))
        request = {"question": "Какие признаки у узла?",
                   "snapshot_id": self.service.meta["snapshot_id"]}
        missing = client.post("/api/investigate", json=request | {
            "selected_gids": ["999999999999999999"],
        })
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "ENTITY_NOT_FOUND")
        numeric = client.post("/api/investigate", json=request | {
            "selected_gids": [int(self.common_target)],
        })
        self.assertEqual(numeric.status_code, 422)
        self.assertEqual(numeric.json()["error"]["code"], "INVALID_REQUEST")
        leading_zero_gid = "0" + self.common_target
        self.assertNotIn(leading_zero_gid, self.service.known_gids)
        self.assertEqual(client.get(f"/api/entities/{leading_zero_gid}").status_code, 404)
        leading_zero = client.post("/api/investigate", json=request | {
            "selected_gids": [leading_zero_gid],
        })
        self.assertEqual(leading_zero.status_code, 404)
        self.assertEqual(model.calls, 0)

    def test_synthetic_leading_zero_gid_survives_http_model_tools_and_evidence(self):
        # Isolated transport fixture derived from a live profile; never an analysis result.
        gid = "0" + self.isolate
        profile = deepcopy(self.service.profiles[self.isolate])
        profile["gid"] = gid
        for fact in profile["evidence"]:
            fact["gid"] = gid
            fact["evidence_id"] = "leading-zero-test:" + fact["evidence_id"]
        meta = self.service.meta | {"snapshot_id": "synthetic-leading-zero-transport"}
        service = SnapshotService({"meta": meta, "profiles": {gid: profile}, "edges": []})
        fake = FakeOpenAIClient(gid, profile["evidence"][0]["evidence_id"])
        model = OpenAIInvestigatorModel(fake, model="test-model")
        client = TestClient(create_app(service=service, model=model,
                                       static_dir=Path("no-frontend-build")))

        self.assertEqual(client.get(f"/api/entities/{gid}").json()["entity"]["gid"], gid)
        graph = client.get("/api/subgraph", params={"gid": gid}).json()
        self.assertEqual(graph["center_gid"], gid)
        self.assertEqual([node["gid"] for node in graph["nodes"]], [gid])
        self.assertEqual(graph["edges"], [])
        result = client.post("/api/investigate", json={
            "question": "Какие признаки у узла?", "selected_gids": [gid],
            "snapshot_id": meta["snapshot_id"],
        }).json()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["findings"][0]["gids"], [gid])
        self.assertEqual(result["evidence"], [profile["evidence"][0]])
        self.assertEqual(result["tool_calls"][0]["status"], "completed")
        selection = json.loads(fake.responses.calls[0]["input"][0]["content"])
        self.assertEqual(selection["selected_gids"], [gid])
        synthesis = json.loads(fake.responses.calls[1]["input"][0]["content"])
        observation = synthesis["verified_tool_observations"][0]
        self.assertEqual(observation["result"]["gid"], gid)
        self.assertTrue(all(fact["gid"] == gid for fact in observation["evidence"]))

    def test_unexpected_server_error_uses_contract_without_internal_details(self):
        client = TestClient(create_app(service=self.service, static_dir=Path("no-frontend-build")),
                            raise_server_exceptions=False)
        with patch.object(self.service, "summary", side_effect=RuntimeError("private-test-detail")):
            response = client.get("/api/summary")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn("private-test-detail", response.text)
        self.assertNotIn("Traceback", response.text)
        self.assertEqual(client.get("/api/summary").status_code, 200)

    def test_http_auto_model_uses_sdk_and_live_snapshot_evidence(self):
        gid = self.common_target
        fact = self.service.get_entity(gid)["entity"]["evidence"][0]
        fake = FakeOpenAIClient(gid, fact["evidence_id"])
        request = {"question": "Какие признаки у узла?", "selected_gids": [gid],
                   "snapshot_id": self.service.meta["snapshot_id"]}
        with patch.dict(os.environ, {"OPENAI_API_KEY": "dummy", "OPENAI_MODEL": "test-model"}), \
                patch("openai.AsyncOpenAI", return_value=fake) as sdk_client:
            client = TestClient(create_app(service=self.service, auto_model=True,
                                           static_dir=Path("no-frontend-build")))
            response = client.post("/api/investigate", json=request)

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["meta"], self.service.meta)
        self.assertEqual(result["evidence"], [fact])
        self.assertEqual(result["findings"][0]["gids"], [gid])
        self.assertEqual(result["findings"][0]["evidence_ids"], [fact["evidence_id"]])
        self.assertEqual(result["tool_calls"][0]["name"], "get_entity_profile")
        self.assertEqual(result["tool_calls"][0]["status"], "completed")
        sdk_client.assert_called_once_with(api_key="dummy", timeout=15.0, max_retries=0)
        self.assertTrue(fake.closed)
        self.assertEqual(len(fake.responses.calls), 2)
        self.assertEqual(fake.responses.calls[0]["model"], "test-model")
        self.assertTrue(all(call["store"] is False for call in fake.responses.calls))
        self.assertTrue(all("previous_response_id" not in call for call in fake.responses.calls))
        payload = json.loads(fake.responses.calls[1]["input"][0]["content"])
        observed = payload["verified_tool_observations"][0]
        self.assertEqual(observed["tool"], "get_entity_profile")
        self.assertEqual(observed["result"]["gid"], gid)
        self.assertEqual(observed["evidence"][0], fact)
        self.assertEqual(fake.responses.calls[1]["text"]["format"]["type"], "json_schema")

    def test_http_auto_model_without_key_is_unavailable(self):
        gid = self.common_target
        request = {"question": "Какие признаки у узла?", "selected_gids": [gid],
                   "snapshot_id": self.service.meta["snapshot_id"]}
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            client = TestClient(create_app(service=self.service, auto_model=True,
                                           static_dir=Path("no-frontend-build")))
            response = client.post("/api/investigate", json=request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "unavailable")
        self.assertEqual(response.json()["findings"], [])
        self.assertEqual(response.json()["tool_calls"], [])


if __name__ == "__main__":
    unittest.main()
