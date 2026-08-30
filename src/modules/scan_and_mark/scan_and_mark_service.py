import os
from typing import List
from uuid import uuid4

import httpx
from fastapi import HTTPException, status
from prisma import Prisma

from .pydantic_model.scan_and_mark_pydantic_model import (
    SubmissionPdfMetadata,
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
                "status": "prepare_upload",
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
        """Return True if an object already lives at `file_path` in the storage bucket.

        The reconcile endpoint uses this to tell 'file already uploaded' (-> confirm) from
        'file missing' (-> re-issue a signed URL). Uses HEAD so the body is never downloaded.
        Bucket name = SUPABASE_STORAGE_BUCKET if set, else the last segment of
        SUPABASE_STORAGE_BUCKET_PATH (".../upload/sign/<bucket>").
        """
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        bucket = os.getenv("SUPABASE_STORAGE_BUCKET") or os.getenv("SUPABASE_STORAGE_BUCKET_PATH", "").rsplit("/", 1)[-1]

        url = f"{supabase_url}/storage/v1/object/{bucket}/{file_path}"
        headers = {
            "Authorization": f"Bearer {service_role_key}",
            "apikey": service_role_key,
        }
        async with httpx.AsyncClient() as client:
            response = await client.head(url, headers=headers)

        if response.status_code == 200:
            return True
        if response.status_code in (400, 404):
            return False
        response.raise_for_status()  # unexpected status — surface it rather than guess
        return False

    async def reconcile_upload(
        self,
        teacher_id: str,
        homework_id: str,
        homework_type: str,
        criteria: OnetimeCriteria,
        submission_entries: List[SubmissionPdfMetadata],
        has_marking_scheme: bool,
    ) -> dict:
        """Idempotently repair a failed/partial upload by checking EACH record independently.

        Deliberately does NOT assume the homework and its submissions are all-or-nothing — the
        upload's atomicity may change — so every record is verified/created on its own:

          Homework:  missing -> create (owned by teacher_id); exists & not mine -> 404; mine -> use it.
          Each submission (independently): exists under a different homework -> skip; missing -> create
            it under this homework; then storage: present -> confirm ('ocr'); absent -> re-issue URL.

        Returns {homework_id, submissions: [{submission_id, action, ...}]} where action is one of
        'confirmed' | 'needs_upload' | 'skipped'. (Marking-scheme storage reconcile is deferred to
        task #4 — it needs a client-generated marking_scheme_id to be addressable; here the MS row is
        only (re)created as part of a missing homework, for the FK.)
        """
        org_id = await self.get_teacher_org_id(teacher_id)

        # --- Homework: verified on its own ---
        homework = await self.db.homework.find_unique(where={"id": homework_id})
        # Exists but owned by someone else must be indistinguishable from 'missing'.
        if homework is not None and homework.teacher_id != teacher_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")
        if homework is None:
            # Create the missing homework (+ its marking scheme, for the FK) owned by teacher_id.
            async with self.db.tx() as tx:
                tx_service = ScanAndMarkService(tx)
                marking_scheme_id = None
                if has_marking_scheme:
                    marking_scheme_id, _ = await tx_service.create_marking_scheme_record(
                        org_id, teacher_id, homework_id, criteria.markingScheme
                    )
                await tx_service.create_onetime_homework(
                    teacher_id, homework_type, criteria, homework_id, marking_scheme_id, has_marking_scheme
                )

        # --- Submissions: each verified & created independently (no sibling assumption) ---
        results = []
        for entry in submission_entries:
            existing = await self.db.homework_submission_onetime.find_unique(
                where={"id": entry.submission_id}
            )
            # Exists under a different homework -> not ours to touch; skip (don't leak via a 409 either).
            if existing is not None and existing.homework_id != homework_id:
                results.append({"submission_id": entry.submission_id, "action": "skipped"})
                continue

            if existing is None:
                created = await self.create_onetime_submissions(org_id, teacher_id, homework_id, [entry])
                file_path = created[0]["file_path"]
                file_name = created[0]["file_name"]
            else:
                file_path = existing.file_path
                file_name = existing.file_name

            if not file_path:
                results.append({"submission_id": entry.submission_id, "action": "skipped"})
                continue

            if await self.storage_object_exists(file_path):
                await self.db.homework_submission_onetime.update(
                    where={"id": entry.submission_id}, data={"status": "ocr"}
                )
                results.append({"submission_id": entry.submission_id, "action": "confirmed"})
            else:
                signed_url = await self.generate_signed_upload_url(file_path)
                results.append({
                    "submission_id": entry.submission_id,
                    "action": "needs_upload",
                    "file_name": file_name,
                    "signed_url": signed_url,
                })

        return {"homework_id": homework_id, "submissions": results}
