"""Provider-boundary tests; the read-only tools below are the real ToolSession path."""

import asyncio
import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from agent import FixtureProvider, investigate
from agent.openai_model import OpenAIInvestigatorModel, model_from_environment


GID = "900000000000000001"


class FakeResponses:
    def __init__(self, tool="get_entity_profile", arguments=None, *, text=None, error=None):
        self.tool = tool
        self.arguments = arguments or {"gid": GID}
        self.text = text
        self.error = error
        self.requests = []

    async def create(self, **kwargs):
        self.requests.append(kwargs)
        if self.error:
            raise self.error
        if kwargs.get("tool_choice") == "required":
            return SimpleNamespace(output=[SimpleNamespace(
                type="function_call", name=self.tool,
                arguments=json.dumps(self.arguments),
            )])
        payload = json.loads(kwargs["input"][0]["content"])
        observations = payload["verified_tool_observations"]
        facts = [fact for item in observations for fact in item["evidence"]]
        if self.text is None:
            text = "Наблюдаемые признаки требуют дополнительной проверки."
        else:
            text = self.text
        if facts:
            fact = next((item for item in facts if item["metric"].startswith("priority_component_")), facts[0])
            findings = [{"text": text, "gids": [fact["gid"]],
                         "evidence_ids": [fact["evidence_id"]]}]
        else:
            findings = []
        return SimpleNamespace(output_text=json.dumps({
            "findings": findings, "next_checks": [],
        }, ensure_ascii=False))


class FakeClient:
    def __init__(self, responses):
        self.responses = responses


class APITimeoutError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class OpenAIModelTests(unittest.TestCase):
    def setUp(self):
        self.provider = FixtureProvider()
        self.request = {"question": "Что известно об узле?", "selected_gids": [GID],
                        "snapshot_id": self.provider.meta["snapshot_id"]}

    def run_question(self, fake):
        model = OpenAIInvestigatorModel(FakeClient(fake))
        return asyncio.run(investigate(
            self.request, self.provider, model, meta=self.provider.meta,
            known_gids=self.provider.known_gids,
        ))

    def test_model_selects_real_profile_and_synthesizes_verified_evidence(self):
        fake = FakeResponses()
        result = self.run_question(fake)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["tool_calls"][0]["name"], "get_entity_profile")
        self.assertEqual(result["tool_calls"][0]["status"], "completed")
        self.assertEqual(result["findings"][0]["gids"], [GID])
        self.assertEqual(result["findings"][0]["text"],
                         "Наблюдаемые признаки требуют дополнительной проверки.")
        self.assertEqual(result["evidence"][0]["gid"], GID)
        self.assertEqual(len(fake.requests), 2)
        final_input = fake.requests[1]["input"][0]["content"]
        self.assertIn(result["evidence"][0]["evidence_id"], final_input)
        self.assertIn(GID, final_input)
        self.assertNotIn("OPENAI_API_KEY", final_input)

    def test_ranking_fetches_actual_profile_for_evidence(self):
        self.request["question"] = "Какие узлы наиболее приоритетны для проверки?"
        self.request["selected_gids"] = []
        fake = FakeResponses("rank_entities", {"role": None, "cluster_id": None, "limit": 1})
        result = self.run_question(fake)
        self.assertEqual(result["status"], "completed")
        self.assertEqual([call["name"] for call in result["tool_calls"]],
                         ["rank_entities", "get_entity_profile"])
        self.assertEqual(result["evidence"][0]["metric"], "in_degree")
        self.assertEqual(len(fake.requests), 2)

    def test_empty_common_result_is_reported_without_invented_finding(self):
        fake = FakeResponses("find_common_recipients", {
            "gids": ["900000000000000002", "900000000000000006"],
            "max_hops": 1, "limit": 5,
        })
        result = self.run_question(fake)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["findings"], [])
        self.assertIn("не найдены", result["message"])
        self.assertEqual(len(fake.requests), 2)

    def test_unknown_gid_and_invalid_tool_arguments_fail_without_fake_facts(self):
        for fake in (
            FakeResponses(arguments={"gid": "900000000000000999"}),
            FakeResponses("get_subgraph", {"gid": GID, "hops": 99, "limit": 5}),
        ):
            with self.subTest(arguments=fake.arguments):
                result = self.run_question(fake)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result["findings"], [])
                self.assertEqual(result["tool_calls"][0]["status"], "failed")

    def test_provider_timeout_and_missing_credentials_are_controlled(self):
        result = self.run_question(FakeResponses(error=APITimeoutError()))
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(self.run_question(FakeResponses(error=AuthenticationError()))["status"],
                         "unavailable")
        self.assertEqual(self.run_question(FakeResponses(error=RuntimeError()))["status"],
                         "failed")
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            self.assertIsNone(model_from_environment())

    def test_accusation_in_model_prose_is_rejected(self):
        for text in (
            "Это доказанное мошенничество.",
            "Наблюдаемые признаки не доказывают виновность.",
            "Приоритет не является вероятностью преступления.",
        ):
            with self.subTest(text=text):
                result = self.run_question(FakeResponses(text=text))
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result["findings"], [])
                self.assertEqual(result["evidence"], [])
        numeric = self.run_question(FakeResponses(text="Вероятность преступления 87%."))
        self.assertEqual(numeric["status"], "failed")

    def test_priority_claim_requires_priority_evidence_in_supported_languages(self):
        # The fixture profile only supplies a raw in_degree fact, not a
        # priority component. Neither language may promote it to priority.
        for text in (
            "This node has high priority.",
            "This node should be prioritized for review.",
            "Узел имеет высокий приоритет проверки.",
        ):
            with self.subTest(text=text):
                result = self.run_question(FakeResponses(text=text))
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result["findings"], [])
                self.assertEqual(result["evidence"], [])
                self.assertEqual(result["tool_calls"][0]["status"], "completed")

    def test_tool_call_preserves_leading_zero_gid(self):
        fake = FakeResponses(arguments={"gid": "001234"})
        model = OpenAIInvestigatorModel(FakeClient(fake))
        action = asyncio.run(model.next_step(self.request, []))
        self.assertEqual(action.arguments["gid"], "001234")


if __name__ == "__main__":
    unittest.main()
