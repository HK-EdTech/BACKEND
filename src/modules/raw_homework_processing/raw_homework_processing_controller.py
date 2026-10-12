"""Raw homework processing endpoint — multipart upload in, question list out."""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from .raw_homework_processing_service import RawHomeworkProcessingService

router = APIRouter(prefix="/raw-homework", tags=["Raw Homework Processing"])


def get_raw_homework_processing_service() -> RawHomeworkProcessingService:
    return RawHomeworkProcessingService()


@router.post("/process")
async def process_raw_homework(
    request: Request,
    submissions: List[UploadFile] = File(..., description="Student answer sheets (1 or more)"),
    question_images: Optional[List[UploadFile]] = File(None, description="Images of the questions"),
    marking_scheme_images: Optional[List[UploadFile]] = File(None, description="Images of the marking scheme"),
    extra_information: Optional[str] = Form(None, description="Additional guidance for marking the homework"),
    service: RawHomeworkProcessingService = Depends(get_raw_homework_processing_service),
):
    """Work out which questions are to be marked from whatever material was uploaded."""
    # 'debug-user' from the DEBUG_TOKEN bypass is not a UUID, so this stays a str.
    teacher_id = request.state.user.get("sub")
    print(f"[raw-homework/process] Teacher: {teacher_id} | submissions: {len(submissions)}")

    return await service.process(
        submissions=submissions,
        question_images=question_images,
        marking_scheme_images=marking_scheme_images,
        extra_information=extra_information,
    )
