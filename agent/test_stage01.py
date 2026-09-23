import asyncio
from copy import deepcopy
import json
from pathlib import Path
import unittest

from agent import FixtureProvider, ValidationError, validate_investigation_response
from agent.fixture_provider import EntityNotFound, FixtureUnavailable


FIXTURE = json.loads(
    (Path(__file__).resolve().parents[1] / "shared" / "fixtures.json").read_text(encoding="utf-8")
)


class StageOneTests(unittest.TestCase):
    def setUp(self):
        self.provider = FixtureProvider()
        self.profile = asyncio.run(self.provider.get_entity_profile("900000000000000001"))
        self.answer = deepcopy(FIXTURE["investigation_completed"])

    def validate(self, answer, tool_results=None):
        return validate_investigation_response(
            answer,
            expected_meta=self.provider.meta,
            known_gids=self.provider.known_gids,
            trusted_tool_results=tool_results if tool_results is not None else [self.profile],
            executed_tool_calls=answer["tool_calls"],
        )

    def test_valid_reference_and_exact_fact(self):
        self.assertEqual(self.validate(self.answer)["status"], "completed")
        self.answer["evidence"][0]["value"] = 30
        with self.assertRaisesRegex(ValidationError, "differs from trusted"):
            self.validate(self.answer)

    def test_unknown_gid_and_missing_fixture_profile(self):
        with self.assertRaises(EntityNotFound):
            asyncio.run(self.provider.get_entity_profile("900000000000000999"))
        with self.assertRaises(FixtureUnavailable):
            asyncio.run(self.provider.get_entity_profile("900000000000000002"))
        self.answer["findings"][0]["gids"] = ["900000000000000999"]
        with self.assertRaisesRegex(ValidationError, "absent from snapshot"):
            self.validate(self.answer)

    def test_invalid_evidence_id(self):
        self.answer["findings"][0]["evidence_ids"] = ["invented:id"]
        with self.assertRaisesRegex(ValidationError, "not resolved"):
            self.validate(self.answer)

    def test_snapshot_mismatch(self):
        self.answer["meta"]["snapshot_id"] = "old-snapshot"
        with self.assertRaisesRegex(ValidationError, "SNAPSHOT_MISMATCH"):
            self.validate(self.answer)

    def test_trace_and_model_written_number_rejected(self):
        trace = deepcopy(self.answer["tool_calls"])
        trace[0]["duration_ms"] = 1
        with self.assertRaisesRegex(ValidationError, "execution log"):
            validate_investigation_response(
                self.answer, expected_meta=self.provider.meta,
                known_gids=self.provider.known_gids,
                trusted_tool_results=[self.profile], executed_tool_calls=trace,
            )
        self.answer["findings"][0]["text"] = "Observed 99 counterparties"
        with self.assertRaisesRegex(ValidationError, "model-written numerals"):
            self.validate(self.answer)

    def test_depth_truncated_must_survive(self):
        boundary = asyncio.run(self.provider.get_entity_profile("900000000000000005"))
        fact = deepcopy(boundary["entity"]["evidence"][0])
        trace = [{"name": "get_entity_profile", "status": "completed", "duration_ms": 0,
                  "evidence_ids": [fact["evidence_id"]]}]
        answer = {
            "meta": deepcopy(self.provider.meta), "status": "completed", "message": "fixture check",
            "findings": [{"text": "observed boundary", "gids": [fact["gid"]],
                          "evidence_ids": [fact["evidence_id"]], "limitations": []}],
            "evidence": [fact], "limitations": [], "next_checks": [], "tool_calls": trace,
        }
        with self.assertRaisesRegex(ValidationError, "omits limitations"):
            self.validate(answer, [boundary])
        answer["findings"][0]["limitations"] = boundary["entity"]["limitations"]
        answer["limitations"] = boundary["entity"]["limitations"]
        self.assertEqual(self.validate(answer, [boundary])["status"], "completed")

    def test_fixture_common_recipients_and_empty_result(self):
        request = {"gids": ["900000000000000002", "900000000000000003"],
                   "max_hops": 1, "limit": 50}
        response = asyncio.run(self.provider.find_common_recipients(request))
        self.assertEqual(response["mode"], "direct")
        self.assertEqual(response["items"][0]["paths"][0]["gids"][0], request["gids"][0])
        request["gids"][1] = "900000000000000006"
        self.assertEqual(asyncio.run(self.provider.find_common_recipients(request))["items"], [])

    def test_fixture_subgraph_truncation_is_exact(self):
        response = asyncio.run(self.provider.get_subgraph("900000000000000001", limit=2))
        self.assertTrue(response["truncated"])
        self.assertEqual(response["omitted_count"], 3)
        with self.assertRaises(FixtureUnavailable):
            asyncio.run(self.provider.get_subgraph("900000000000000001", limit=3))


if __name__ == "__main__":
    unittest.main()
