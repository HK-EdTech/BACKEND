from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from ...database import prisma_client
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

    print(f"[upload-for-signed-url] Teacher: {teacher_id} | Type: {homework_type} | PDFs: {len(body.homework_pdf_entries)}")

    try:
        service = ScanAndMarkService(prisma_client)
        org_id = await service.get_teacher_org_id(teacher_id)
        homework_id = str(uuid4())


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

            for pdf in body.homework_pdf_entries:
                print(f"  - student: {pdf.student_name} | {pdf.file_name} | {pdf.file_size} bytes | checksum: {pdf.checksum}")

            # After match block — create submissions (onetime only)
            if homework_type == "onetime":
                submission_infos = await tx_service.create_onetime_submissions(org_id, teacher_id, homework_id, body.homework_pdf_entries)

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
                    "file_name": marking_scheme_info["file_name"],
                    "signed_url": marking_scheme_signed_url,
                }
                if marking_scheme_info else None
            ),
            "submission_uploads": submission_signed_urls,
        }

    except HTTPException:
        raise
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
