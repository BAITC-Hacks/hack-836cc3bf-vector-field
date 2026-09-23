"""Focused Responses adapter tests with a scripted, network-free client."""

from copy import deepcopy
import json
from types import SimpleNamespace
import unittest

import httpx2
from openai import APITimeoutError, AsyncOpenAI

from agent import FinalAction, ToolAction
from backend.openai_model import OpenAIInvestigatorModel


GID = "001234567890123456789"
EVIDENCE_ID = "priority-in-degree-001234"
REQUEST = {
    "question": "Какие наблюдаемые признаки проверить?",
    "selected_gids": [GID],
    "snapshot_id": "snapshot-test",
}
FACT = {
    "evidence_id": EVIDENCE_ID,
    "gid": GID,
    "metric": "priority_component_in_degree",
    "value": 0.12,
    "unit": "ratio",
    "rule_id": "priority_v0",
    "source": "derived",
    "scope": "node",
    "text": "Вклад входящих связей в приоритет: 0.12.",
    "limitations": ["inflow_incomplete"],
}
OBSERVATION = {
    "name": "get_entity_profile",
    "arguments": {"gid": GID},
    "result": {
        "meta": {"contract_version": "1", "snapshot_id": "snapshot-test",
                 "rules_version": "test", "data_mode": "live"},
        "entity": {"gid": GID, "evidence": [FACT],
                   "limitations": ["inflow_incomplete"], "next_checks": []},
    },
    "evidence": [FACT],
}
READ_ONLY_TOOLS = {
    "get_entity_profile", "get_subgraph", "rank_entities", "find_common_recipients"
}


def function_response(name: str, arguments: dict, *, call_id: str, response_id: str):
    """Shape returned by an AsyncOpenAI Responses function call."""
    return SimpleNamespace(
        id=response_id,
        output=[SimpleNamespace(
            type="function_call", name=name,
            arguments=json.dumps(arguments), call_id=call_id,
        )],
    )


class FakeResponses:
    def __init__(self, *scripted):
        self.scripted = list(scripted)
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self.scripted:
            raise AssertionError("Unexpected Responses call")
        return self.scripted.pop(0)


class FakeClient:
    def __init__(self, *scripted):
        self.responses = FakeResponses(*scripted)


class OpenAIModelTests(unittest.IsolatedAsyncioTestCase):
    def _model(self, *, evidence_id=EVIDENCE_ID):
        client = FakeClient(
            function_response("get_entity_profile", {"gid": GID},
                              call_id="call_profile", response_id="resp_profile"),
            function_response("submit_investigation", {
                "findings": [{"gids": [GID], "evidence_ids": [evidence_id]}],
                "next_checks": [],
            }, call_id="call_final", response_id="resp_final"),
        )
        return OpenAIInvestigatorModel(client, model_name="test-model"), client

    async def test_first_step_forces_read_only_tool_and_preserves_exact_gid(self):
        model, client = self._model()

        action = await model.next_step(deepcopy(REQUEST), ())

        self.assertEqual(action, ToolAction("get_entity_profile", {"gid": GID}))
        self.assertIsInstance(action.arguments["gid"], str)
        self.assertEqual(client.responses.calls[0]["model"], "test-model")
        self.assertIs(client.responses.calls[0]["store"], False)
        self.assertNotIn("previous_response_id", client.responses.calls[0])
        tools = {tool["name"] for tool in client.responses.calls[0]["tools"]}
        self.assertTrue(READ_ONLY_TOOLS.issubset(tools))
        choice = client.responses.calls[0].get("tool_choice")
        if isinstance(choice, dict):
            self.assertIn(choice.get("name"), READ_ONLY_TOOLS)
        else:
            self.assertEqual(choice, "required")
            self.assertNotIn("submit_investigation", tools)

    async def test_next_step_returns_tool_output_and_reconstructs_trusted_evidence(self):
        model, client = self._model()
        await model.next_step(deepcopy(REQUEST), ())

        final = await model.next_step(deepcopy(REQUEST), (deepcopy(OBSERVATION),))

        self.assertIsInstance(final, FinalAction)
        self.assertEqual(final.findings[0]["gids"], [GID])
        self.assertEqual(final.findings[0]["evidence_ids"], [EVIDENCE_ID])
        self.assertEqual(final.evidence, [FACT])
        self.assertIsNot(final.evidence[0], FACT)
        self.assertEqual(client.responses.calls[1]["model"], "test-model")
        self.assertIs(client.responses.calls[1]["store"], False)
        self.assertNotIn("previous_response_id", client.responses.calls[1])
        self.assertEqual(client.responses.calls[1]["input"][0], client.responses.calls[0]["input"][0])
        self.assertEqual(client.responses.calls[1]["input"][1].call_id, "call_profile")
        tool_outputs = [item for item in client.responses.calls[1]["input"]
                        if isinstance(item, dict) and item.get("type") == "function_call_output"]
        self.assertEqual(len(tool_outputs), 1)
        self.assertEqual(tool_outputs[0]["call_id"], "call_profile")
        output = tool_outputs[0]["output"]
        if isinstance(output, str):
            output = json.loads(output)
        self.assertEqual(output["result"]["entity"]["gid"], GID)
        self.assertEqual(output["evidence"][0]["evidence_id"], EVIDENCE_ID)

    async def test_final_rejects_citation_absent_from_trusted_observation(self):
        model, _client = self._model(evidence_id="invented-evidence-id")
        await model.next_step(deepcopy(REQUEST), ())

        with self.assertRaises(ValueError):
            await model.next_step(deepcopy(REQUEST), (deepcopy(OBSERVATION),))

    async def test_sdk_timeout_is_mapped_to_harness_timeout(self):
        class TimeoutResponses:
            async def create(self, **_kwargs):
                request = httpx2.Request("POST", "https://api.openai.com/v1/responses")
                raise APITimeoutError(request=request)

        model = OpenAIInvestigatorModel(
            SimpleNamespace(responses=TimeoutResponses()), model_name="test-model"
        )

        with self.assertRaises(TimeoutError) as caught:
            await model.next_step(deepcopy(REQUEST), ())
        self.assertIsInstance(caught.exception.__cause__, APITimeoutError)

    async def test_sdk_serializes_stateless_tool_continuation(self):
        sent = []

        def respond(request):
            sent.append(json.loads(request.content))
            if len(sent) == 1:
                name, arguments = "get_entity_profile", {"gid": GID}
            else:
                name = "submit_investigation"
                arguments = {
                    "findings": [{"gids": [GID], "evidence_ids": [EVIDENCE_ID]}],
                    "next_checks": [],
                }
            return httpx2.Response(200, json={
                "id": f"response-{len(sent)}", "object": "response",
                "created_at": 0, "model": "test-model",
                "output": [{
                    "type": "function_call", "name": name,
                    "arguments": json.dumps(arguments),
                    "call_id": f"call-{len(sent)}", "status": "completed",
                }],
            })

        async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as http_client:
            client = AsyncOpenAI(api_key="test", http_client=http_client, max_retries=0)
            model = OpenAIInvestigatorModel(client, model_name="test-model")
            self.assertEqual(await model.next_step(deepcopy(REQUEST), ()),
                             ToolAction("get_entity_profile", {"gid": GID}))
            final = await model.next_step(deepcopy(REQUEST), (deepcopy(OBSERVATION),))

        self.assertIsInstance(final, FinalAction)
        self.assertEqual(len(sent), 2)
        self.assertTrue(all(payload["store"] is False for payload in sent))
        self.assertTrue(all("previous_response_id" not in payload for payload in sent))
        self.assertEqual(sent[1]["input"][1]["type"], "function_call")
        self.assertEqual(sent[1]["input"][2]["type"], "function_call_output")
        self.assertEqual(sent[1]["input"][2]["call_id"], "call-1")


if __name__ == "__main__":
    unittest.main()
