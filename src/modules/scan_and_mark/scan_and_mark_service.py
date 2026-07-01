import os
from typing import List
from uuid import uuid4

import httpx
from fastapi import HTTPException, status
from prisma import Prisma

from .pydantic_model.scan_and_mark_pydantic_model import (
    HomeworkPdfMetadata,
    MarkingSchemeMetadata,
    OnetimeCriteria,
)


class ScanAndMarkService:
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
        marking_scheme_id: str,
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
                "status": "uploading",
            }
        )

    async def create_onetime_submissions(
        self,
        org_id: str,
        teacher_id: str,
        homework_id: str,
        pdf_entries: List[HomeworkPdfMetadata],
    ) -> List[dict]:
        path_template = os.getenv("STORAGE_PATH_ONETIME", "")
        results = []
        for pdf in pdf_entries:
            sub_id = str(uuid4())
            file_path = path_template.format(
                educational_organization_id=org_id,
                teacher_id=teacher_id,
                homework_id=homework_id,
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
    ) -> tuple[str, dict]:
        ms_id = str(uuid4())
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
        return ms_id, {"file_name": ms.file_name, "file_path": file_path}

    async def confirm_submission_upload(self, submission_id: str, teacher_id: str) -> dict:
        """On upload confirmation, move the submission and its homework to the 'ocr' phase.
        Homework status is a coarse phase marker: any confirmed submission puts the homework
        into 'ocr' (no rollup). Returns {submission_id, homework_id, homework_status}."""
        submission = await self.db.homework_submission_onetime.find_unique(where={"id": submission_id})
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found",
            )

        async with self.db.tx() as tx:
            # ownership enforced here: only updates if this teacher owns the homework
            owned = await tx.homework.update_many(
                where={"id": submission.homework_id, "teacher_id": teacher_id},
                data={"status": "ocr"},
            )
            if owned == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Submission not found",
                )
            await tx.homework_submission_onetime.update(
                where={"id": submission_id}, data={"status": "ocr"}
            )

        return {
            "submission_id": submission_id,
            "homework_id": submission.homework_id,
            "homework_status": "ocr",
        }

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
