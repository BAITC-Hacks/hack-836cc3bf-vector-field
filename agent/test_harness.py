import asyncio
from copy import deepcopy
import unittest

from agent import FinalAction, FixtureProvider, ToolAction, investigate
from agent.boundary import ToolLimits
from agent.evidence import common_recipient_evidence
from agent.session import SnapshotMismatch


REQUEST = {
    "question": "Какие признаки у узла?",
    "selected_gids": ["900000000000000001"],
    "snapshot_id": "fixture-v1",
}


class ProfileModel:
    async def next_step(self, request, observations):
        if not observations:
            return ToolAction("get_entity_profile", {"gid": request["selected_gids"][0]})
        entity = observations[0]["result"]["entity"]
        fact = entity["evidence"][0]
        return FinalAction(
            findings=[{
                "text": "Наблюдается несколько входящих связей.",
                "gids": [entity["gid"]], "evidence_ids": [fact["evidence_id"]],
                "limitations": list(entity["limitations"]),
            }],
            evidence=[deepcopy(fact)],
            limitations=list(entity["limitations"]),
            next_checks=list(entity["next_checks"]),
        )


class BadFactModel(ProfileModel):
    async def next_step(self, request, observations):
        action = await super().next_step(request, observations)
        if isinstance(action, FinalAction):
            fact = deepcopy(action.evidence[0])
            fact["value"] = "invented"
            return FinalAction(action.findings, [fact], action.limitations, action.next_checks)
        return action


class AccusatoryModel(ProfileModel):
    async def next_step(self, request, observations):
        action = await super().next_step(request, observations)
        if isinstance(action, FinalAction):
            finding = dict(action.findings[0])
            finding["text"] = "Этот человек организовал преступление."
            return FinalAction(
                [finding], action.evidence, action.limitations,
                [*action.next_checks, "Заблокировать счёт немедленно."],
            )
        return action


class SlowModel:
    async def next_step(self, request, observations):
        await asyncio.sleep(0.05)
        return FinalAction([], [], [], [])


class EndlessModel:
    async def next_step(self, request, observations):
        return ToolAction("rank_entities", {"limit": 1})


class PathModel:
    async def next_step(self, request, observations):
        if not observations:
            return ToolAction("find_common_recipients", {
                "gids": ["900000000000000002", "900000000000000003"],
                "max_hops": 1, "limit": 50,
            })
        facts = common_recipient_evidence(observations[0]["result"])
        return FinalAction(
            findings=[{
                "text": "Модель могла написать неподтверждённый вывод.",
                "gids": [fact["gid"] for fact in facts],
                "evidence_ids": [fact["evidence_id"] for fact in facts],
                "limitations": ["path_not_money_provenance", "date_only"],
            }],
            evidence=facts,
            limitations=["path_not_money_provenance", "date_only"],
            next_checks=["Запросить точное время переводов и подтверждение связи операций."],
        )


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.provider = FixtureProvider()

    def run_investigation(self, model, **kwargs):
        return asyncio.run(investigate(
            deepcopy(REQUEST), self.provider, model,
            meta=self.provider.meta, known_gids=self.provider.known_gids, **kwargs,
        ))

    def test_one_grounded_question(self):
        response = self.run_investigation(ProfileModel())
        self.assertEqual(response["status"], "completed")
        self.assertEqual(len(response["tool_calls"]), 1)
        self.assertEqual(response["tool_calls"][0]["status"], "completed")
        self.assertEqual(response["findings"][0]["gids"], REQUEST["selected_gids"])

    def test_unavailable_has_no_fake_success(self):
        response = self.run_investigation(None)
        self.assertEqual(response["status"], "unavailable")
        self.assertEqual(response["tool_calls"], [])
        self.assertEqual(response["findings"], [])

    def test_fabricated_fact_becomes_failed(self):
        response = self.run_investigation(BadFactModel())
        self.assertEqual(response["status"], "failed")
        self.assertEqual(response["findings"], [])
        self.assertEqual(response["evidence"], [])
        self.assertEqual(len(response["tool_calls"]), 1)

    def test_model_prose_and_unsupported_next_check_are_discarded(self):
        response = self.run_investigation(AccusatoryModel())
        self.assertEqual(response["status"], "completed")
        self.assertNotIn("преступление", response["findings"][0]["text"])
        self.assertNotIn("Заблокировать счёт немедленно.", response["next_checks"])

    def test_grounded_common_path_with_cautious_wording(self):
        response = self.run_investigation(PathModel())
        self.assertEqual(response["status"], "completed")
        self.assertEqual(len(response["evidence"]), 3)
        self.assertIn("происхождение средств не установлено", response["findings"][0]["text"])
        self.assertIn("path_not_money_provenance", response["limitations"])

    def test_model_timeout(self):
        response = self.run_investigation(
            SlowModel(), limits=ToolLimits(timeout_seconds=0.01)
        )
        self.assertEqual(response["status"], "timeout")
        self.assertEqual(response["findings"], [])

    def test_seventh_call_is_not_executed(self):
        response = self.run_investigation(EndlessModel())
        self.assertEqual(response["status"], "failed")
        self.assertEqual(len(response["tool_calls"]), 6)
        self.assertTrue(all(call["status"] == "completed" for call in response["tool_calls"]))

    def test_stale_request_is_rejected_before_model(self):
        request = deepcopy(REQUEST)
        request["snapshot_id"] = "old"
        with self.assertRaises(SnapshotMismatch):
            asyncio.run(investigate(
                request, self.provider, ProfileModel(),
                meta=self.provider.meta, known_gids=self.provider.known_gids,
            ))


if __name__ == "__main__":
    unittest.main()
