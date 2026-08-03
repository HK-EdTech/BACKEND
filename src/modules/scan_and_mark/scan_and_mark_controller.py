import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from google.cloud import vision
from prisma.errors import UniqueViolationError
from pydantic import BaseModel, ValidationError

from ...database import prisma_client
from ...ocrs.models.GoogleCloudVisionAPI import GoogleCloudVisionAPI
from .pydantic_model.scan_and_mark_pydantic_model import (
    UploadForSignedUrlRequest,
    OnetimeCriteria,
    ClassCriteria,
)
from .scan_and_mark_service import ScanAndMarkService

router = APIRouter(prefix="/scan-and-mark", tags=["Scan and Mark"])


@router.post("/upload-for-signed-url")
async def upload_for_signed_url(request: Request, body: UploadForSignedUrlRequest):
    teacher_id = request.state.user.get("sub")
    homework_type = body.homework_criteria[0] if body.homework_criteria else "unknown"
    raw_criteria = body.homework_criteria[1] if len(body.homework_criteria) > 1 else {}

    print(f"[upload-for-signed-url] Teacher: {teacher_id} | Type: {homework_type} | PDFs: {len(body.submission_pdf_entries)}")

    try:
        service = ScanAndMarkService(prisma_client)
        org_id = await service.get_teacher_org_id(teacher_id)
        homework_id = body.homework_id  # client-generated PK


        #process the homework criteria from different type of homework first then create the marking scheme db record
        criteria = OnetimeCriteria(**raw_criteria) if homework_type == "onetime" else None
        marking_scheme_id = None
        marking_scheme_info = None
        submission_infos = []

        # Marking scheme is optional. Only create the record when the teacher actually
        # picked a file (non-empty file_name). criteria is None for class -> skips safely.
        has_marking_scheme = (
            criteria is not None
            and bool((criteria.markingScheme.file_name or "").strip())
        )

        async with prisma_client.tx() as tx:
            tx_service = ScanAndMarkService(tx)

            #create the marking_scheme record first then pass it to create the homework record
            if has_marking_scheme:
                marking_scheme_id, marking_scheme_info = await tx_service.create_marking_scheme_record(
                    org_id, teacher_id, homework_id, criteria.markingScheme
                )
                print(f"  marking_scheme_id: {marking_scheme_id} | {criteria.markingScheme.file_name} | {criteria.markingScheme.file_size} bytes | checksum: {criteria.markingScheme.checksum}")
            else:
                print("  no marking scheme provided — skipping marking_scheme record and signed URL")

            match homework_type:
                case "onetime":
                    print(f"  homeworkTitle: {criteria.homeworkTitle} | level: {criteria.selectedLevel} | subject: {criteria.selectedOneTimeSubject}")
                    await tx_service.create_onetime_homework(teacher_id, homework_type, criteria, homework_id, marking_scheme_id, has_marking_scheme)
                case "class":
                    criteria = ClassCriteria(**raw_criteria)
                case _:
                    print(f"  Unknown homework_type: {homework_type}")

            for pdf in body.submission_pdf_entries:
                print(f"  - student: {pdf.student_name} | {pdf.file_name} | {pdf.file_size} bytes | checksum: {pdf.checksum}")

            # After match block — create submissions (onetime only)
            if homework_type == "onetime":
                submission_infos = await tx_service.create_onetime_submissions(org_id, teacher_id, homework_id, body.submission_pdf_entries)

        # Generate signed upload URLs after transaction (external HTTP calls)
        marking_scheme_signed_url = None
        submission_signed_urls = []
        if marking_scheme_info:
            marking_scheme_signed_url = await service.generate_signed_upload_url(marking_scheme_info["file_path"])
        if homework_type == "onetime":
            for submission in submission_infos:
                signed_url = await service.generate_signed_upload_url(submission["file_path"])
                submission_signed_urls.append({
                    "id": submission["id"],
                    "student_name": submission["student_name"],
                    "file_name": submission["file_name"],
                    "signed_url": signed_url,
                })

        return {
            "homework_id": homework_id,
            "marking_scheme_upload": (
                {
                    "id": marking_scheme_id,
                    "file_name": marking_scheme_info["file_name"],
                    "signed_url": marking_scheme_signed_url,
                }
                if marking_scheme_info else None
            ),
            "submission_uploads": submission_signed_urls,
        }

    except HTTPException:
        raise
    except UniqueViolationError:
        # Client re-sent ids that already exist (e.g. a retry hitting this endpoint instead of the
        # reconcile endpoint). The rows are already there — signal a conflict rather than duplicating.
        print(f"[upload-for-signed-url] Duplicate id — homework_id: {homework_id}")
        raise HTTPException(status_code=409, detail="Homework or submission with this id already exists")
    except ValidationError as e:
        print(f"[upload-for-signed-url] Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"[upload-for-signed-url] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/submissions/{submission_id}/confirm")
async def confirm_submission(submission_id: str, request: Request):
    """Confirm one submission's upload — moves it and its homework to the 'ocr' phase."""
    teacher_id = request.state.user.get("sub")
    service = ScanAndMarkService(prisma_client)
    return await service.confirm_submission_upload(submission_id, teacher_id)


@router.patch("/marking-scheme/{marking_scheme_id}/confirm")
async def confirm_marking_scheme(marking_scheme_id: str, request: Request):
    """Confirm the marking scheme's upload — moves it to the 'ocr' phase."""
    teacher_id = request.state.user.get("sub")
    service = ScanAndMarkService(prisma_client)
    return await service.confirm_marking_scheme_upload(marking_scheme_id, teacher_id)


class OcrTestRequest(BaseModel):
    bucket: str
    file_path: str


@router.post("/ocr/test")
async def test_ocr_from_supabase(request: Request, body: OcrTestRequest):
    """Download a PDF from Supabase Storage and run Google Cloud Vision OCR on it."""
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        raise HTTPException(status_code=500, detail="SUPABASE_URL not configured")

    # Use the user's bearer token to access Supabase Storage
    raw_token = request.headers.get("Authorization", "")[7:]  # strip "Bearer "

    download_url = f"{supabase_url}/storage/v1/object/{body.bucket}/{body.file_path}"

    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            download_url,
            headers={
                "Authorization": f"Bearer {raw_token}",
                "apikey": supabase_anon_key,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to download from Supabase Storage: {resp.text}",
            )
        pdf_bytes = resp.content

    gcv_client = vision.ImageAnnotatorClient()
    result = GoogleCloudVisionAPI._detect_pdf(gcv_client, pdf_bytes)
    return result
