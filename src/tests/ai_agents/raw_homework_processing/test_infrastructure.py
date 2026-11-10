"""Offline checks for infrastructure retained during the graph rebuild."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from fastapi import HTTPException
from ai_agents.llm import OpenRouterCaller
from src.modules.raw_homework_processing.raw_homework_processing_service import RawHomeworkProcessingService

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

    def homework_fixture(self):
        document = SimpleNamespace(
            id="document-1", file_name="questions.pdf", file_path="homework/questions.pdf",
            content_type="application/pdf", checksum="checksum", status="ocr", err=None,
            student_name="Student",
        )
        homework = SimpleNamespace(
            id="homework-1", title="Algebra", subject="Mathematics", level="Secondary 1",
            homework_type="onetime", classes=None, homework_classes=[],
            homework_submission_onetime=[document], homework_submission_class=[],
            homework_question_document=document, marking_scheme=None,
            question_text="Solve x + 1 = 2", marking_guidance="Show working",
            marking_answers="x = 1", question_filter="1",
        )
        db = SimpleNamespace(homework=SimpleNamespace(find_first=AsyncMock(return_value=homework)))
        graph = SimpleNamespace(ainvoke=AsyncMock(return_value={
            "messages": [AIMessage(content="Review is ready.")], "tasks": [{"task_id": "task-1"}],
        }))
        return db, homework, document, graph

    async def test_service_loads_owned_homework_and_initial_graph_inputs(self):
        db, homework, document, graph = self.homework_fixture()
        teacher_id = "5a32ca73-354b-4ad8-bcc5-8e10631c2a29"
        with patch.dict("os.environ", {"SUPABASE_STORAGE_BUCKET_PATH": "storage/v1/object/upload/sign/homework"}):
            result = await RawHomeworkProcessingService(db).process(
                homework.id, teacher_id, homework_marking_graph=graph,
            )
        self.assertEqual(db.homework.find_first.call_args.kwargs["where"],
                         {"id": homework.id, "teacher_id": teacher_id})
        state = graph.ainvoke.call_args.args[0]
        self.assertEqual(state, {"messages": [], "tasks": [], "coordinator_decision": None})
        runtime = graph.ainvoke.call_args.kwargs["config"]["configurable"]
        self.assertEqual(runtime["thread_id"], result["conversation_id"])
        self.assertEqual(runtime["initial_task_type"], "raw_homework_processing")
        inputs = runtime["initial_task_inputs"]
        self.assertEqual(inputs["question_document"]["file_path"], document.file_path)
        self.assertEqual(inputs["submissions"][0]["student_name"], "Student")
        self.assertEqual(inputs["storage_bucket"], "homework")
        self.assertEqual(inputs["extra_information"]["question_text"], homework.question_text)
        self.assertIsNone(inputs["marking_scheme"])
        self.assertNotIn("image_bundle", runtime)
        self.assertEqual(result["response"], "Review is ready.")

    async def test_service_rejects_missing_or_unowned_homework(self):
        db, homework, _, graph = self.homework_fixture()
        db.homework.find_first.return_value = None
        with self.assertRaises(HTTPException) as caught:
            await RawHomeworkProcessingService(db).process(
                homework.id, "5a32ca73-354b-4ad8-bcc5-8e10631c2a29", homework_marking_graph=graph,
            )
        self.assertEqual(caught.exception.status_code, 404)
        graph.ainvoke.assert_not_awaited()

    async def test_service_rejects_unfinished_documents_and_empty_submissions(self):
        for scenario, code in (("uploading", 409), ("failed", 409), ("empty", 422)):
            with self.subTest(scenario=scenario):
                db, homework, document, graph = self.homework_fixture()
                if scenario == "empty":
                    homework.homework_submission_onetime = []
                elif scenario == "failed":
                    document.err = "upload_failed"
                else:
                    document.status = "uploading"
                with self.assertRaises(HTTPException) as caught:
                    await RawHomeworkProcessingService(db).process(
                        homework.id, "5a32ca73-354b-4ad8-bcc5-8e10631c2a29", homework_marking_graph=graph,
                    )
                self.assertEqual(caught.exception.status_code, code)
                graph.ainvoke.assert_not_awaited()

    async def test_service_rejects_debug_identity_without_database_access(self):
        db, homework, _, graph = self.homework_fixture()
        with self.assertRaises(HTTPException) as caught:
            await RawHomeworkProcessingService(db).process(
                homework.id, "debug-user", homework_marking_graph=graph,
            )
        self.assertEqual(caught.exception.status_code, 403)
        db.homework.find_first.assert_not_awaited()
        graph.ainvoke.assert_not_awaited()
