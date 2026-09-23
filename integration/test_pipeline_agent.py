"""Profile-only smoke test of real pipeline output through the agent boundary.

This deliberately does not claim that backend HTTP or a persistent snapshot is
implemented. It uses the same in-memory AnalysisResult returned by pipeline.
"""

import asyncio
from copy import deepcopy
import hashlib
from pathlib import Path
import unittest

from agent import FinalAction, ToolAction, investigate
from pipeline.run import DEFAULT_DATA, analyze, load_and_validate


ROOT = Path(__file__).resolve().parents[1]


class ProfileOnlyProvider:
    """Test adapter over AnalysisResult; production service is still pending."""

    def __init__(self, result, meta):
        self.result = result
        self.meta = meta
        self.known_gids = frozenset(str(gid) for gid in result.profiles)

    async def get_entity_profile(self, gid):
        profile = deepcopy(self.result.profiles[int(gid)])
        profile.pop("priority_components")  # Pipeline internal, absent from Entity v1.
        return {"meta": deepcopy(self.meta), "entity": profile}

    async def get_subgraph(self, gid, hops=1, limit=80):
        raise NotImplementedError("backend snapshot service not published")

    async def rank_entities(self, role=None, cluster_id=None, limit=20):
        raise NotImplementedError("backend snapshot service not published")

    async def find_common_recipients(self, request):
        raise NotImplementedError("backend snapshot service not published")


class ProfileQuestion:
    async def next_step(self, request, observations):
        if not observations:
            return ToolAction("get_entity_profile", {"gid": request["selected_gids"][0]})
        entity = observations[0]["result"]["entity"]
        fact = observations[0]["evidence"][0]
        return FinalAction(
            findings=[{
                "text": "Model text is replaced by a controlled template.",
                "gids": [entity["gid"]],
                "evidence_ids": [fact["evidence_id"]],
                "limitations": list(entity["limitations"]),
            }],
            evidence=[fact],
            limitations=list(entity["limitations"]),
            next_checks=list(entity["next_checks"]),
        )


class PipelineAgentSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodes, edges, tx = load_and_validate(DEFAULT_DATA)
        cls.result = analyze(nodes, edges, tx)
        digest = hashlib.sha256()
        for path in (
            DEFAULT_DATA / "nodes.parquet",
            DEFAULT_DATA / "edges.parquet",
            DEFAULT_DATA / "transactions.parquet",
            ROOT / "pipeline" / "config.py",
        ):
            digest.update(path.read_bytes())
        cls.meta = {
            "contract_version": "1", "snapshot_id": "smoke-" + digest.hexdigest()[:20],
            "rules_version": "v0", "data_mode": "live",
        }
        cls.provider = ProfileOnlyProvider(cls.result, cls.meta)

    def test_real_profiles_validate_through_agent(self):
        profiles = self.result.profiles
        mixed = "100000003684369100"
        isolate = next(p["gid"] for p in profiles.values() if "isolated_seed" in p["limitations"])
        boundary = next(p["gid"] for p in profiles.values() if p["depth"] == 4)
        for gid in (mixed, isolate, boundary):
            with self.subTest(gid=gid):
                response = asyncio.run(investigate(
                    {"question": "Какие наблюдаемые признаки у узла?",
                     "selected_gids": [gid], "snapshot_id": self.meta["snapshot_id"]},
                    self.provider, ProfileQuestion(), meta=self.meta,
                    known_gids=self.provider.known_gids,
                ))
                self.assertEqual(response["status"], "completed")
                self.assertEqual(response["findings"][0]["gids"], [gid])
                self.assertEqual(response["evidence"][0]["gid"], gid)
                self.assertEqual(response["tool_calls"][0]["status"], "completed")
        self.assertIn("isolated_seed", profiles[int(isolate)]["limitations"])
        self.assertIn("depth_truncated", profiles[int(boundary)]["limitations"])
        self.assertNotEqual(profiles[int(boundary)]["role"], "terminal")

    def test_every_real_priority_is_explained_by_six_facts(self):
        self.assertEqual(len(self.result.profiles), 2248)
        for profile in self.result.profiles.values():
            facts = [fact for fact in profile["evidence"] if fact["rule_id"] == "priority_v0"]
            self.assertEqual(len(facts), 6)
            self.assertAlmostEqual(sum(fact["value"] for fact in facts), profile["priority_score"], places=9)
            self.assertEqual(profile["gid"], str(int(profile["gid"])))


if __name__ == "__main__":
    unittest.main()
