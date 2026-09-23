"""Real Parquet/snapshot/services/API with only the external model boundary faked."""

from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from agent.openai_model import OpenAIInvestigatorModel
from agent.test_openai_model import FakeClient, FakeResponses
from backend.app import create_app
from backend.service import SnapshotService
from pipeline.run import DEFAULT_DATA, analyze, load_and_validate
from pipeline.snapshot import build_snapshot


class AIModelPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodes, edges, tx = load_and_validate(DEFAULT_DATA)
        analysis = analyze(nodes, edges, tx)
        cls.service = SnapshotService(build_snapshot(analysis, nodes, edges, DEFAULT_DATA))
        cls.top_gid = cls.service.summary()["top_nodes"][0]["gid"]
        cls.isolate = next(gid for gid, p in cls.service.profiles.items()
                           if "isolated_seed" in p["limitations"])

    def client_for(self, fake):
        model = OpenAIInvestigatorModel(FakeClient(fake))
        return TestClient(create_app(service=self.service, model=model,
                                     static_dir=Path("no-frontend-build")))

    def ask(self, client, question, selected):
        return client.post("/api/investigate", json={
            "question": question, "selected_gids": selected,
            "snapshot_id": self.service.meta["snapshot_id"],
        })

    def test_ranking_model_tool_real_profiles_synthesis_and_core_routes(self):
        fake = FakeResponses("rank_entities", {"role": None, "cluster_id": None, "limit": 3},
                             text="Рассчитанные признаки повышают аналитический приоритет узла.")
        client = self.client_for(fake)
        response = self.ask(client, "Кого проверить первым и почему?", [self.top_gid])
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual([call["name"] for call in data["tool_calls"]],
                         ["rank_entities", "get_entity_profile", "get_entity_profile", "get_entity_profile"])
        self.assertTrue(all(call["status"] == "completed" for call in data["tool_calls"]))
        fact = data["evidence"][0]
        self.assertEqual(fact, next(item for item in self.service.profiles[fact["gid"]]["evidence"]
                                    if item["evidence_id"] == fact["evidence_id"]))
        self.assertTrue(fact["metric"].startswith("priority_component_"))
        self.assertIn(fact["evidence_id"], data["findings"][0]["evidence_ids"])
        self.assertNotIn("вероятность", data["findings"][0]["text"])
        self.assertEqual(client.get(f"/api/entities/{self.top_gid}").status_code, 200)
        self.assertEqual(client.get("/api/summary").json()["meta"], self.service.meta)

    def test_exact_gid_profile_and_empty_common_recipients(self):
        profile_client = self.client_for(FakeResponses(arguments={"gid": self.top_gid}))
        result = self.ask(profile_client, "Что известно об этом узле?", [self.top_gid]).json()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["findings"][0]["gids"], [self.top_gid])
        self.assertIsInstance(result["evidence"][0]["gid"], str)

        empty = FakeResponses("find_common_recipients", {
            "gids": [self.isolate, self.top_gid], "max_hops": 1, "limit": 5,
        })
        empty_client = self.client_for(empty)
        answer = self.ask(empty_client, "Есть ли общие получатели?",
                          [self.isolate, self.top_gid]).json()
        self.assertEqual(answer["status"], "completed")
        self.assertEqual(answer["findings"], [])
        self.assertIn("не найдены", answer["message"])
        self.assertIn("path_not_money_provenance", answer["limitations"])


if __name__ == "__main__":
    unittest.main()
