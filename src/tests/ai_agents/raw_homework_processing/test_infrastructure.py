"""Offline checks for infrastructure retained during the graph rebuild."""
import io
from PIL import Image
import unittest
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from fastapi import UploadFile, HTTPException
from ai_agents.llm import OpenRouterCaller
from modules.raw_homework_processing.raw_homework_processing_service import RawHomeworkProcessingService

def response(text):
    return AIMessage(content=text, usage_metadata={"input_tokens": 2, "output_tokens": 3, "total_tokens": 5})

class InfrastructureTests(unittest.IsolatedAsyncioTestCase):
    def caller(self, replies):
        fake = AsyncMock()
        fake.ainvoke.side_effect = replies
        with patch("ai_agents.llm.build_chat_model", return_value=fake):
            caller = OpenRouterCaller("cheap", "unused", max_retries=2)
        return caller, fake

    async def test_text_and_explicit_format(self):
        caller, fake = self.caller([response("Review complete.")])
        messages = [HumanMessage(content="Review")]
        with self.assertRaises(TypeError):
            await caller(messages, "review")
        result, meta = await caller(messages, "review", response_format="text")
        self.assertEqual(result, "Review complete.")
        self.assertEqual(meta["usage"]["total_tokens"], 5)
        self.assertEqual(fake.ainvoke.call_args.args[0], messages)

    async def test_json_retry_counts_all_usage(self):
        caller, fake = self.caller([response("invalid"), response('{"arbitrary": [1, 2]}')])
        result, meta = await caller([], "review", response_format="json")
        self.assertEqual(result, {"arbitrary": [1, 2]})
        self.assertEqual(meta["attempts"], 2)
        self.assertEqual(meta["usage"]["total_tokens"], 10)
        self.assertTrue(meta["ok"])
        self.assertEqual(set(fake.ainvoke.call_args.kwargs), {"config"})

    async def test_failure_and_invalid_format(self):
        caller, fake = self.caller([RuntimeError("offline"), RuntimeError("offline")])
        with self.assertRaises(ValueError):
            await caller([], "review", response_format="xml")
        result, meta = await caller([], "review", response_format="text")
        self.assertIsNone(result)
        self.assertFalse(meta["ok"])
        self.assertEqual(meta["attempts"], 2)

    async def test_service_validation_and_initial_graph_invocation(self):
        service = RawHomeworkProcessingService()

        class FakeGraph:
            async def ainvoke(self, state, config):
                self.state = state
                self.config = config
                return {
                    "messages": [AIMessage(content="Review is ready.")],
                    "tasks": [{"task_id": "task-1"}],
                }

        graph = FakeGraph()
        with self.assertRaises(HTTPException) as caught:
            await service.process([], teacher_assistant_graph=graph)
        self.assertEqual(caught.exception.status_code, 422)
        bad = UploadFile(filename="bad.pdf", file=io.BytesIO(b"%PDF-1.4"))
        bad.read = AsyncMock(return_value=b"%PDF-1.4")
        with self.assertRaises(HTTPException) as caught:
            await service.process([bad], teacher_assistant_graph=graph)
        self.assertEqual(caught.exception.status_code, 415)
        buffer = io.BytesIO()
        Image.new("RGB", (1, 1), "white").save(buffer, format="PNG")
        image = UploadFile(filename="s.png", file=io.BytesIO(buffer.getvalue()))
        image.read = AsyncMock(return_value=buffer.getvalue())

        result = await service.process(
            [image],
            extra_information="Mark question 1",
            teacher_assistant_graph=graph,
        )

        self.assertEqual(result["response"], "Review is ready.")
        self.assertEqual(result["tasks"], [{"task_id": "task-1"}])
        self.assertTrue(result["conversation_id"])
        self.assertEqual(graph.state, {
            "messages": [],
            "tasks": [],
            "coordinator_decision": None,
        })
        runtime = graph.config["configurable"]
        self.assertEqual(runtime["thread_id"], result["conversation_id"])
        self.assertEqual(
            runtime["initial_task_type"], "raw_homework_processing"
        )
        self.assertEqual(
            runtime["initial_task_inputs"],
            {
                "submission_image_ids": ["submissions-1"],
                "question_image_ids": [],
                "marking_scheme_image_ids": [],
                "extra_information": "Mark question 1",
            },
        )
