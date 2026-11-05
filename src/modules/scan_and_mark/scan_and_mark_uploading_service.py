import os
from typing import List

import httpx
from fastapi import HTTPException, status
from prisma import Prisma

from .pydantic_model.scan_and_mark_pydantic_model import (
    SubmissionPdfMetadata,
    MarkingSchemeMetadata,
    OnetimeCriteria,
    QuestionDocumentMetadata,
)


class ScanAndMarkUploadingService:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_teacher_org_id(self, teacher_id: str) -> str:
        profile = await self.db.profiles.find_unique(where={"id": teacher_id})
        if not profile or not profile.organization_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher profile or organization not found",
            )
        return profile.organization_id

    async def create_onetime_homework(
        self,
        teacher_id: str,
        homework_type: str,
        criteria: OnetimeCriteria,
        homework_id: str,
        marking_scheme_id: str | None,
        has_marking_scheme: bool,
    ) -> None:
        await self.db.homework.create(
            data={
                "id": homework_id,
                "title": criteria.homeworkTitle,
                "subject": criteria.selectedOneTimeSubject,
                "level": criteria.selectedLevel,
                "teacher_id": teacher_id,
                "homework_type": homework_type,
                "marking_scheme_id": marking_scheme_id,
                "has_marking_scheme": has_marking_scheme,
                "status": "prepare_upload",
                "question_text": criteria.extra_information.questions,
                "marking_guidance": criteria.extra_information.marking_guidance,
                "marking_answers": criteria.extra_information.marking_answers,
                "question_filter": criteria.extra_information.question_filter,
            }
        )

    async def create_onetime_submissions(
        self,
        org_id: str,
        teacher_id: str,
        homework_id: str,
        pdf_entries: List[SubmissionPdfMetadata],
    ) -> List[dict]:
        path_template = os.getenv("STORAGE_PATH_ONETIME", "")
        results = []
        for pdf in pdf_entries:
            sub_id = pdf.submission_id  # client-generated PK
            file_path = path_template.format(
                educational_organization_id=org_id,
                teacher_id=teacher_id,
                homework_id=homework_id,
                submission_id=pdf.submission_id,
                file_name=pdf.file_name,
            )
            await self.db.homework_submission_onetime.create(
                data={
                    "id": sub_id,
                    "homework_id": homework_id,
                    "student_name": pdf.student_name,
                    "file_name": pdf.file_name,
                    "file_path": file_path,
                    "file_size_bytes": pdf.file_size,
                    "content_type": pdf.content_type,
                    "checksum": pdf.checksum,
                    "status": "uploading",
                }
            )
            results.append({
                "id": sub_id,
                "student_name": pdf.student_name,
                "file_name": pdf.file_name,
                "file_path": file_path,
            })
        return results

    async def create_marking_scheme_record(
        self,
        org_id: str,
        teacher_id: str,
        homework_id: str,
        ms: MarkingSchemeMetadata,
    ) -> dict:
        # Client-generated PK — the caller already owns this id (in the payload); no longer returned.
        ms_id = ms.marking_scheme_id
        path_template = os.getenv("STORAGE_PATH_MARKING_SCHEME", "")
        file_path = path_template.format(
            educational_organization_id=org_id,
            teacher_id=teacher_id,
            homework_id=homework_id,
            marking_scheme_id=ms_id,
            file_name=ms.file_name,
        )
        await self.db.marking_scheme.create(
            data={
                "id": ms_id,
                "file_name": ms.file_name,
                "file_path": file_path,
                "file_size_bytes": ms.file_size,
                "content_type": ms.content_type,
                "checksum": ms.checksum,
                "status": "uploading",
            }
        )
        return {"file_name": ms.file_name, "file_path": file_path}

    async def _owned_homework(self, homework_id: str, teacher_id: str):
        homework = await self.db.homework.find_first(
            where={"id": homework_id, "teacher_id": teacher_id}
        )
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")
        return homework

    async def _owned_question_document(self, document_id: str, teacher_id: str):
        document = await self.db.homework_question_document.find_unique(where={"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Question document not found")
        await self._owned_homework(document.homework_id, teacher_id)
        return document

    async def create_question_document_record(
        self, org_id: str, teacher_id: str, homework_id: str,
        document: QuestionDocumentMetadata,
    ) -> dict:
        await self._owned_homework(homework_id, teacher_id)
        template = os.getenv("STORAGE_PATH_QUESTION_DOCUMENT") or (
            "educational_organization/{educational_organization_id}/teacher/{teacher_id}/"
            "homework/{homework_id}/question_document/{question_document_id}/{file_name}"
        )
        file_path = template.format(
            educational_organization_id=org_id, teacher_id=teacher_id,
            homework_id=homework_id, question_document_id=document.question_document_id,
            file_name=document.file_name,
        )
        await self.db.homework_question_document.create(data={
            "id": document.question_document_id,
            "homework_id": homework_id,
            "file_name": document.file_name,
            "file_path": file_path,
            "file_size_bytes": document.file_size,
            "content_type": document.content_type,
            "checksum": document.checksum,
            "status": "uploading",
        })
        return {"id": document.question_document_id, "file_name": document.file_name, "file_path": file_path}

    async def ensure_question_document_record(
        self, org_id: str, teacher_id: str, homework_id: str,
        document: QuestionDocumentMetadata,
    ) -> dict:
        await self._owned_homework(homework_id, teacher_id)
        existing = await self.db.homework_question_document.find_unique(
            where={"id": document.question_document_id}
        )
        if existing:
            if existing.homework_id != homework_id:
                raise HTTPException(status_code=404, detail="Question document not found")
            # A retry refers to the same artifact; do not issue a URL for a
            # different file under an already-committed document identity.
            if any((
                existing.file_name != document.file_name,
                existing.file_size_bytes != document.file_size,
                existing.content_type != document.content_type,
                existing.checksum != document.checksum,
            )):
                raise HTTPException(status_code=409, detail="Question document metadata differs from the existing upload")
            return {"id": existing.id, "file_name": existing.file_name, "file_path": existing.file_path}
        previous = await self.db.homework_question_document.find_unique(where={"homework_id": homework_id})
        if previous:
            raise HTTPException(status_code=409, detail="This homework already has a question document")
        return await self.create_question_document_record(org_id, teacher_id, homework_id, document)

    async def confirm_question_document_upload(self, document_id: str, teacher_id: str) -> dict:
        document = await self._owned_question_document(document_id, teacher_id)
        if not await self.storage_object_exists(document.file_path):
            raise HTTPException(status_code=409, detail="Question PDF is not available in storage yet")
        await self.db.homework_question_document.update(
            where={"id": document_id}, data={"status": "ocr", "err": None}
        )
        return {"question_document_id": document_id, "status": "ocr"}

    async def set_question_document_err(self, document_id: str, teacher_id: str, err: str) -> dict:
        await self._owned_question_document(document_id, teacher_id)
        await self.db.homework_question_document.update(where={"id": document_id}, data={"err": err})
        return {"question_document_id": document_id, "err": err}

    async def confirm_submission_upload(self, submission_id: str, teacher_id: str) -> dict:
        """On upload confirmation, move ONLY the submission to the 'ocr' phase.
        The homework status is left unchanged (no coarse phase marker).
        Returns {submission_id, homework_id, homework_status}."""
        submission = await self.db.homework_submission_onetime.find_unique(where={"id": submission_id})
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found",
            )

        # ownership check only — do NOT change the homework status here
        homework = await self.db.homework.find_first(
            where={"id": submission.homework_id, "teacher_id": teacher_id}
        )
        if not homework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Homework not found",
            )

        await self.db.homework_submission_onetime.update(
            where={"id": submission_id}, data={"status": "ocr"}
        )

        return {
            "submission_id": submission_id,
            "homework_id": submission.homework_id,
            "homework_status": homework.status,
        }

    async def confirm_marking_scheme_upload(self, marking_scheme_id: str, teacher_id: str) -> dict:
        """On upload confirmation, move the marking scheme to the 'ocr' phase.
        Ownership is verified via the homework that references this marking scheme."""
        homework = await self.db.homework.find_first(
            where={"marking_scheme_id": marking_scheme_id, "teacher_id": teacher_id}
        )
        if not homework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Marking scheme not found",
            )
        await self.db.marking_scheme.update(
            where={"id": marking_scheme_id}, data={"status": "ocr"}
        )
        return {"marking_scheme_id": marking_scheme_id, "status": "ocr"}

    async def set_submission_err(self, submission_id: str, teacher_id: str, err: str) -> dict:
        """Set a submission's err (e.g. 'uploading' when the file upload failed). Ownership via its homework."""
        submission = await self.db.homework_submission_onetime.find_unique(where={"id": submission_id})
        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        homework = await self.db.homework.find_first(
            where={"id": submission.homework_id, "teacher_id": teacher_id}
        )
        if not homework:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")
        await self.db.homework_submission_onetime.update(
            where={"id": submission_id}, data={"err": err}
        )
        return {"submission_id": submission_id, "err": err}

    async def set_marking_scheme_err(self, marking_scheme_id: str, teacher_id: str, err: str) -> dict:
        """Set the marking scheme's err. Ownership verified via its homework."""
        homework = await self.db.homework.find_first(
            where={"marking_scheme_id": marking_scheme_id, "teacher_id": teacher_id}
        )
        if not homework:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marking scheme not found")
        await self.db.marking_scheme.update(
            where={"id": marking_scheme_id}, data={"err": err}
        )
        return {"marking_scheme_id": marking_scheme_id, "err": err}

    async def generate_signed_upload_url(self, file_path: str) -> str:
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        bucket_path = os.getenv("SUPABASE_STORAGE_BUCKET_PATH")

        url = f"{supabase_url}/{bucket_path}/{file_path}"
        headers = {
            "Authorization": f"Bearer {service_role_key}",
            "apikey": service_role_key,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json={"expiresIn": 120})
            response.raise_for_status()
            data = response.json()

        token = data['token']
        return f"{supabase_url}/{bucket_path}/{file_path}?token={token}"

    async def storage_object_exists(self, file_path: str) -> bool:
        """HEAD the storage object to see if the file is already uploaded. The upload-sign bucket path
        (…/object/upload/sign/<bucket>) maps to the read path by dropping the 'upload/sign/' segment."""
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        object_path = os.getenv("SUPABASE_STORAGE_BUCKET_PATH", "").replace("upload/sign/", "")
        url = f"{supabase_url}/{object_path}/{file_path}"
        headers = {
            "Authorization": f"Bearer {service_role_key}",
            "apikey": service_role_key,
        }
        async with httpx.AsyncClient() as client:
            response = await client.head(url, headers=headers)
        return response.status_code == 200

    # ----- Retry: create-if-missing (idempotent variants of the create_* methods above) -----

    async def ensure_marking_scheme_record(
        self,
        org_id: str,
        teacher_id: str,
        homework_id: str,
        ms: MarkingSchemeMetadata,
    ) -> dict:
        existing = await self.db.marking_scheme.find_unique(where={"id": ms.marking_scheme_id})
        if existing:
            return {"file_name": existing.file_name, "file_path": existing.file_path}
        return await self.create_marking_scheme_record(org_id, teacher_id, homework_id, ms)

    async def ensure_onetime_homework(
        self,
        teacher_id: str,
        homework_type: str,
        criteria: OnetimeCriteria,
        homework_id: str,
        marking_scheme_id: str | None,
        has_marking_scheme: bool,
    ) -> None:
        existing = await self.db.homework.find_unique(where={"id": homework_id})
        if existing:
            if existing.teacher_id != teacher_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")
            # Legacy requests omit this object. A retry must not erase text
            # already saved by a newer client just because fields were omitted.
            information = criteria.extra_information.model_dump(
                include=criteria.extra_information.model_fields_set
            )
            if "questions" in information:
                information["question_text"] = information.pop("questions")
            if information:
                await self.db.homework.update(where={"id": homework_id}, data=information)
            return
        await self.create_onetime_homework(
            teacher_id, homework_type, criteria, homework_id, marking_scheme_id, has_marking_scheme
        )

    async def ensure_onetime_submissions(
        self,
        org_id: str,
        teacher_id: str,
        homework_id: str,
        pdf_entries: List[SubmissionPdfMetadata],
    ) -> List[dict]:
        path_template = os.getenv("STORAGE_PATH_ONETIME", "")
        results = []
        for pdf in pdf_entries:
            existing = await self.db.homework_submission_onetime.find_unique(where={"id": pdf.submission_id})
            if existing:
                results.append({
                    "id": existing.id,
                    "student_name": existing.student_name,
                    "file_name": existing.file_name,
                    "file_path": existing.file_path,
                })
                continue
            file_path = path_template.format(
                educational_organization_id=org_id,
                teacher_id=teacher_id,
                homework_id=homework_id,
                submission_id=pdf.submission_id,
                file_name=pdf.file_name,
            )
            await self.db.homework_submission_onetime.create(
                data={
                    "id": pdf.submission_id,
                    "homework_id": homework_id,
                    "student_name": pdf.student_name,
                    "file_name": pdf.file_name,
                    "file_path": file_path,
                    "file_size_bytes": pdf.file_size,
                    "content_type": pdf.content_type,
                    "checksum": pdf.checksum,
                    "status": "uploading",
                }
            )
            results.append({
                "id": pdf.submission_id,
                "student_name": pdf.student_name,
                "file_name": pdf.file_name,
                "file_path": file_path,
            })
        return results

    async def retry_check_storage(
        self,
        teacher_id: str,
        homework_id: str,
        submission_ids: List[str],
        marking_scheme_id: str | None,
        question_document_id: str | None = None,
    ) -> dict:
        """Per id, report whether the file is already in storage; for the not-stored ones, hand back a
        fresh signed upload URL so the frontend can re-PUT. Ownership is verified via the homework."""
        homework = await self.db.homework.find_first(
            where={"id": homework_id, "teacher_id": teacher_id}
        )
        if not homework:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")

        submissions = []
        for sid in submission_ids:
            sub = await self.db.homework_submission_onetime.find_unique(where={"id": sid})
            if not sub or sub.homework_id != homework_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
            stored = await self.storage_object_exists(sub.file_path)
            signed_url = None if stored else await self.generate_signed_upload_url(sub.file_path)
            submissions.append({"id": sid, "stored": stored, "signed_url": signed_url})

        marking_scheme = None
        if marking_scheme_id:
            if homework.marking_scheme_id != marking_scheme_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marking scheme not found")
            ms = await self.db.marking_scheme.find_unique(where={"id": marking_scheme_id})
            if not ms:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marking scheme not found")
            stored = await self.storage_object_exists(ms.file_path)
            signed_url = None if stored else await self.generate_signed_upload_url(ms.file_path)
            marking_scheme = {"id": marking_scheme_id, "stored": stored, "signed_url": signed_url}

        question_document = None
        if question_document_id:
            document = await self._owned_question_document(question_document_id, teacher_id)
            if document.homework_id != homework_id:
                raise HTTPException(status_code=404, detail="Question document not found")
            stored = await self.storage_object_exists(document.file_path)
            signed_url = None if stored else await self.generate_signed_upload_url(document.file_path)
            question_document = {"id": document.id, "stored": stored, "signed_url": signed_url}

        return {"submissions": submissions, "marking_scheme": marking_scheme, "question_document": question_document}
