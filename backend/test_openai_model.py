"""Actual OpenAI SDK serialization over a network-free HTTP transport.

The canonical adapter lives in agent.openai_model. These checks exercise the
SDK boundary in addition to its existing scripted provider tests.
"""

from copy import deepcopy
import json
import unittest

import httpx2
from openai import APITimeoutError, AsyncOpenAI

from agent import FinalAction, ToolAction
from agent.openai_model import OpenAIInvestigatorModel


GID = "001234567890123456789"
EVIDENCE_ID = "priority-in-degree-001234"
REQUEST = {
    "question": "Какие наблюдаемые признаки проверить?",
    "selected_gids": [GID],
    "snapshot_id": "snapshot-test",
}
FACT = {
    "evidence_id": EVIDENCE_ID, "gid": GID,
    "metric": "priority_component_in_degree", "value": 0.12,
    "unit": "ratio", "rule_id": "priority_v0", "source": "derived",
    "scope": "node", "text": "Вклад входящих связей в приоритет: 0.12.",
    "limitations": ["inflow_incomplete"],
}
OBSERVATION = {
    "name": "get_entity_profile", "arguments": {"gid": GID},
    "result": {
        "meta": {"contract_version": "1", "snapshot_id": "snapshot-test",
                 "rules_version": "test", "data_mode": "live"},
        "entity": {
            "gid": GID, "depth": 1, "is_seed": False, "role": "peripheral",
            "role_score": 0.1, "priority_score": 0.12, "cluster_id": 0,
            "metrics": {}, "evidence": [FACT],
            "limitations": ["inflow_incomplete"], "next_checks": [],
        },
    },
    "evidence": [FACT],
}


class OpenAISDKTests(unittest.IsolatedAsyncioTestCase):
    async def test_sdk_serializes_tool_selection_and_grounded_synthesis(self):
        sent = []

        def respond(request):
            sent.append(json.loads(request.content))
            if len(sent) == 1:
                output = [{
                    "type": "function_call", "name": "get_entity_profile",
                    "arguments": json.dumps({"gid": GID}),
                    "call_id": "call-profile", "status": "completed",
                }]
            else:
                draft = {
                    "findings": [{
                        "text": "Наблюдаемые признаки требуют дополнительной проверки.",
                        "gids": [GID], "evidence_ids": [EVIDENCE_ID],
                    }],
                    "next_checks": [],
                }
                output = [{
                    "type": "message", "id": "message-final", "role": "assistant",
                    "status": "completed", "content": [{
                        "type": "output_text", "text": json.dumps(draft, ensure_ascii=False),
                        "annotations": [],
                    }],
                }]
            return httpx2.Response(200, json={
                "id": f"response-{len(sent)}", "object": "response",
                "created_at": 0, "model": "test-model", "output": output,
            })

        async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as http_client:
            async with AsyncOpenAI(api_key="test", http_client=http_client, max_retries=0) as client:
                model = OpenAIInvestigatorModel(client, model="test-model")
                self.assertEqual(await model.next_step(deepcopy(REQUEST), ()),
                                 ToolAction("get_entity_profile", {"gid": GID}))
                final = await model.next_step(deepcopy(REQUEST), (deepcopy(OBSERVATION),))

        self.assertIsInstance(final, FinalAction)
        self.assertTrue(final.model_text)
        self.assertEqual(final.findings[0]["gids"], [GID])
        self.assertEqual(final.evidence, [FACT])
        self.assertIsNot(final.evidence[0], FACT)
        self.assertEqual(len(sent), 2)
        self.assertTrue(all(payload["store"] is False for payload in sent))
        self.assertTrue(all(payload["model"] == "test-model" for payload in sent))
        self.assertTrue(all("previous_response_id" not in payload for payload in sent))
        self.assertEqual(sent[0]["tool_choice"], "required")
        self.assertFalse(sent[0]["parallel_tool_calls"])
        self.assertEqual({tool["name"] for tool in sent[0]["tools"]}, {
            "get_entity_profile", "get_subgraph", "rank_entities", "find_common_recipients",
        })
        observation = json.loads(sent[1]["input"][0]["content"])["verified_tool_observations"][0]
        self.assertEqual(observation["result"]["gid"], GID)
        self.assertEqual(observation["evidence"], [FACT])
        response_format = sent[1]["text"]["format"]
        self.assertEqual(response_format["type"], "json_schema")
        ids = response_format["schema"]["properties"]["findings"]["items"]["properties"]["evidence_ids"]
        self.assertEqual(ids["items"]["enum"], [EVIDENCE_ID])

    async def test_real_sdk_timeout_maps_to_harness_timeout(self):
        def time_out(request):
            raise httpx2.ReadTimeout("scripted timeout", request=request)

        async with httpx2.AsyncClient(transport=httpx2.MockTransport(time_out)) as http_client:
            async with AsyncOpenAI(api_key="test", http_client=http_client, max_retries=0) as client:
                model = OpenAIInvestigatorModel(client, model="test-model")
                with self.assertRaises(TimeoutError) as caught:
                    await model.next_step(deepcopy(REQUEST), ())
        self.assertIsInstance(caught.exception.__cause__, APITimeoutError)


if __name__ == "__main__":
    unittest.main()
