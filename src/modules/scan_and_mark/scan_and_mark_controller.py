from fastapi import APIRouter, Request
from .pydantic_model.scan_and_mark_pydantic_model import (
    UploadForSignedUrlRequest,
    OnetimeCriteria,
    ClassCriteria,
)

router = APIRouter(prefix="/scan-and-mark", tags=["Scan and Mark"])


@router.post("/upload-for-signed-url")
async def upload_for_signed_url(request: Request, body: UploadForSignedUrlRequest):
    teacher_id = request.state.user.get("sub")
    homework_type = body.homework_criteria[0] if body.homework_criteria else "unknown"
    raw_criteria = body.homework_criteria[1] if len(body.homework_criteria) > 1 else {}

    print(f"[upload-for-signed-url] Teacher: {teacher_id} | Type: {homework_type} | PDFs: {len(body.homework_pdf_entries)}")

    match homework_type:
        case "onetime":
            criteria = OnetimeCriteria(**raw_criteria)
            print(f"  homeworkName: {criteria.homeworkName} | level: {criteria.selectedLevel} | subject: {criteria.selectedOneTimeSubject}")
            print(f"  markingScheme: {criteria.markingScheme.file_name} | {criteria.markingScheme.file_size} bytes | checksum: {criteria.markingScheme.checksum}")
        case "class":
            criteria = ClassCriteria(**raw_criteria)
            # TODO: log class criteria fields
        case _:
            print(f"  Unknown homework_type: {homework_type}")

    for pdf in body.homework_pdf_entries:
        print(f"  - student: {pdf.student_name} | {pdf.file_name} | {pdf.file_size} bytes | checksum: {pdf.checksum}")

    return {"received": len(body.homework_pdf_entries)}
