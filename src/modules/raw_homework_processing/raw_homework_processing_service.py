"""Load owned homework context and start the homework marking graph's initial task."""
from __future__ import annotations

import os
from uuid import UUID, uuid4

from fastapi import HTTPException

from ...ai_agents.coordinator.task_definitions import RAW_HOMEWORK_PROCESSING


class RawHomeworkProcessingService:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _document(record) -> dict:
        # Records exist before the browser finishes its storage PUT. Reject
        # unfinished or failed uploads rather than process a partial homework.
        if not record.file_path or record.status in (None, "prepare_upload", "uploading") or record.err:
            raise HTTPException(status_code=409, detail="Homework materials have unfinished or failed uploads")
        return {
            "id": record.id,
            "file_name": record.file_name,
            "file_path": record.file_path,
            "content_type": record.content_type,
            "checksum": record.checksum,
        }

    async def process(self, homework_id: str, teacher_id: str, *, homework_marking_graph) -> dict:
        # Debug identities are not valid UUIDs for database ownership checks.
        try:
            UUID(teacher_id)
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(status_code=403, detail="A valid teacher account is required")

        homework = await self.db.homework.find_first(
            where={"id": homework_id, "teacher_id": teacher_id},
            include={
                "homework_submission_onetime": True,
                "homework_submission_class": True,
                "homework_question_document": True,
                "marking_scheme": True,
                "classes": True,
                "homework_classes": {"include": {"classes": True}},
            },
        )
        if homework is None:
            raise HTTPException(status_code=404, detail="Homework not found")

        submissions = [
            {**self._document(record), "student_name": record.student_name}
            for record in homework.homework_submission_onetime or []
        ] + [
            {**self._document(record), "student_id": record.student_id}
            for record in homework.homework_submission_class or []
        ]
        if not submissions:
            raise HTTPException(status_code=422, detail="At least one uploaded student submission is required")

        classes = {record.id: record for record in [homework.classes] if record}
        for assignment in homework.homework_classes or []:
            if assignment.classes:
                classes[assignment.classes.id] = assignment.classes

        # Keep durable references in checkpoints; the handler will load the PDFs.
        # Reuse the bucket configured for signed uploads, without persisting keys.
        bucket_path = os.getenv("SUPABASE_STORAGE_BUCKET_PATH", "")
        initial_task_inputs = {
            "homework_id": homework.id,
            "title": homework.title,
            "subject": homework.subject,
            "level": homework.level,
            "homework_type": homework.homework_type,
            "classes": [record.model_dump(mode="json") for record in classes.values()],
            "storage_bucket": bucket_path.removeprefix("storage/v1/object/upload/sign/").strip("/"),
            "submissions": submissions,
            "question_document": self._document(homework.homework_question_document) if homework.homework_question_document else None,
            "marking_scheme": self._document(homework.marking_scheme) if homework.marking_scheme else None,
            "extra_information": {
                "question_text": homework.question_text,
                "marking_guidance": homework.marking_guidance,
                "marking_answers": homework.marking_answers,
                "question_filter": homework.question_filter,
            },
        }
        conversation_id = str(uuid4())
        result = await homework_marking_graph.ainvoke(
            {"messages": [], "tasks": [], "coordinator_decision": None},
            config={"configurable": {
                "thread_id": conversation_id,
                "initial_task_type": RAW_HOMEWORK_PROCESSING,
                "initial_task_inputs": initial_task_inputs,
            }},
        )
        messages = result["messages"]
        return {
            "conversation_id": conversation_id,
            "response": messages[-1].content if messages else None,
            "tasks": result["tasks"],
        }
