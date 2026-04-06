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

        criteria = OnetimeCriteria(**raw_criteria) if homework_type == "onetime" else None
        marking_scheme_id = None

        async with prisma_client.tx() as tx:
            tx_service = ScanAndMarkService(tx)

            if homework_type == "onetime":
                marking_scheme_id = await tx_service.create_marking_scheme_record(
                    org_id, teacher_id, homework_id, criteria.markingScheme
                )
                print(f"  marking_scheme_id: {marking_scheme_id}")

            match homework_type:
                case "onetime":
                    print(f"  homeworkTitle: {criteria.homeworkTitle} | level: {criteria.selectedLevel} | subject: {criteria.selectedOneTimeSubject}")
                    print(f"  markingScheme: {criteria.markingScheme.file_name} | {criteria.markingScheme.file_size} bytes | checksum: {criteria.markingScheme.checksum}")
                    await tx_service.create_onetime_homework(teacher_id, homework_type, criteria, homework_id, marking_scheme_id)
                case "class":
                    criteria = ClassCriteria(**raw_criteria)
                case _:
                    print(f"  Unknown homework_type: {homework_type}")

            for pdf in body.homework_pdf_entries:
                print(f"  - student: {pdf.student_name} | {pdf.file_name} | {pdf.file_size} bytes | checksum: {pdf.checksum}")

            # After match block — create submissions (onetime only)
            if homework_type == "onetime":
                await tx_service.create_onetime_submissions(org_id, teacher_id, homework_id, body.homework_pdf_entries)

        return {
            "homework_id": homework_id,
            "submissions_created": len(body.homework_pdf_entries),
        }

    except HTTPException:
        raise
    except ValidationError as e:
        print(f"[upload-for-signed-url] Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"[upload-for-signed-url] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
