from fastapi import APIRouter, Request
from typing import List
from ....database import prisma_client
from .pydantic_model.scan_and_upload_pydantic_model import ClassWithHomeworkResponse
from .scan_and_upload_service import ScanAndUploadService

router = APIRouter(prefix="/scan-and-mark", tags=["Scan and Mark / Scan and Upload"])


def get_scan_and_upload_service():
    return ScanAndUploadService(prisma_client)


@router.get("/classes_subject_homework", response_model=List[ClassWithHomeworkResponse])
async def get_classes_subject_homework(request: Request):
    """Get all classes with their homework for the authenticated teacher."""
    teacher_id = request.state.user.get("sub")
    service = get_scan_and_upload_service()
    return await service.get_classes_with_homework(teacher_id)
