import asyncio
from copy import deepcopy
import unittest

from agent import FixtureProvider, ToolSession
from agent.boundary import ToolLimits
from agent.evidence import common_recipient_evidence
from agent.session import SnapshotMismatch, ToolLimitExceeded


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.provider = FixtureProvider()
        self.session = ToolSession(
            self.provider, meta=self.provider.meta, known_gids=self.provider.known_gids
        )

    def run_call(self, name, arguments):
        return asyncio.run(self.session.call(name, arguments))

    def test_request_and_exact_gid(self):
        request = self.session.validate_request({
            "question": "  Кого проверить?  ",
            "selected_gids": ["900000000000000001"],
            "snapshot_id": "fixture-v1",
        })
        self.assertEqual(request["question"], "Кого проверить?")
        with self.assertRaises(LookupError):
            self.session.validate_request({
                "question": "test", "selected_gids": ["900000000000000999"],
                "snapshot_id": "fixture-v1",
            })
        with self.assertRaises(SnapshotMismatch):
            self.session.validate_request({
                "question": "test", "selected_gids": [], "snapshot_id": "old",
            })

    def test_real_trace_and_profile_fact(self):
        result = self.run_call("get_entity_profile", {"gid": "900000000000000001"})
        self.assertEqual(self.session.calls[0]["status"], "completed")
        self.assertEqual(
            self.session.calls[0]["evidence_ids"],
            [fact["evidence_id"] for fact in result["entity"]["evidence"]],
        )
        result["entity"]["evidence"][0]["value"] = "tampered"
        self.assertEqual(self.session.results[0]["entity"]["evidence"][0]["value"], 3)

    def test_common_path_facts_citable_without_new_contract_fields(self):
        result = self.run_call("find_common_recipients", {
            "gids": ["900000000000000002", "900000000000000003"],
            "max_hops": 1, "limit": 50,
        })
        facts = common_recipient_evidence(result)
        self.assertEqual(len(facts), 3)
        self.assertEqual(self.session.calls[0]["evidence_ids"],
                         [fact["evidence_id"] for fact in facts])
        answer = {
            "meta": deepcopy(self.provider.meta), "status": "completed",
            "message": "Учебный пример структурного пути.",
            "findings": [{
                "text": "У выбранных узлов есть общий наблюдаемый получатель.",
                "gids": ["900000000000000001", "900000000000000002", "900000000000000003"],
                "evidence_ids": [fact["evidence_id"] for fact in facts],
                "limitations": ["path_not_money_provenance", "date_only"],
            }],
            "evidence": facts,
            "limitations": ["path_not_money_provenance", "date_only"],
            "next_checks": ["Проверить точное время операций."],
            "tool_calls": self.session.calls,
        }
        self.assertEqual(self.session.validate(answer)["status"], "completed")
        answer["evidence"][0]["value"] = "invented"
        with self.assertRaisesRegex(ValueError, "differs from trusted"):
            self.session.validate(answer)

    def test_empty_common_result_is_success(self):
        result = self.run_call("find_common_recipients", {
            "gids": ["900000000000000002", "900000000000000006"],
            "max_hops": 1, "limit": 50,
        })
        self.assertEqual(result["items"], [])
        self.assertEqual(self.session.calls[0]["evidence_ids"], [])

    def test_six_call_limit(self):
        async def run():
            for _ in range(6):
                await self.session.call("rank_entities", {"limit": 2})
            with self.assertRaises(ToolLimitExceeded):
                await self.session.call("rank_entities", {"limit": 2})
        asyncio.run(run())
        self.assertEqual(len(self.session.calls), 6)

    def test_timeout_is_logged_as_failure(self):
        class SlowProvider(FixtureProvider):
            async def get_entity_profile(self, gid):
                await asyncio.sleep(0.05)
                return await super().get_entity_profile(gid)

        provider = SlowProvider()
        session = ToolSession(
            provider, meta=provider.meta, known_gids=provider.known_gids,
            limits=ToolLimits(timeout_seconds=0.01),
        )
        with self.assertRaises(TimeoutError):
            asyncio.run(session.call("get_entity_profile", {"gid": "900000000000000001"}))
        self.assertEqual(session.calls[0]["status"], "failed")
        self.assertEqual(session.results, [])

    def test_snapshot_mismatch_is_logged_as_failure(self):
        class StaleProvider(FixtureProvider):
            async def get_entity_profile(self, gid):
                result = await super().get_entity_profile(gid)
                result["meta"]["snapshot_id"] = "old"
                return result

        provider = StaleProvider()
        session = ToolSession(provider, meta=provider.meta, known_gids=provider.known_gids)
        with self.assertRaises(SnapshotMismatch):
            asyncio.run(session.call("get_entity_profile", {"gid": "900000000000000001"}))
        self.assertEqual(session.calls[0]["status"], "failed")

    def test_invalid_arguments_do_not_reach_provider(self):
        with self.assertRaises(ValueError):
            self.run_call("get_subgraph", {"gid": "900000000000000001", "hops": 3})
        self.assertEqual(self.session.calls[0]["status"], "failed")
        self.assertEqual(self.session.results, [])


if __name__ == "__main__":
    unittest.main()
