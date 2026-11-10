"""Start raw homework processing from an existing homework's saved materials."""
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from ...database import prisma_client
from .raw_homework_processing_service import RawHomeworkProcessingService

router = APIRouter(prefix="/raw-homework", tags=["Raw Homework Processing"])


class ProcessRawHomeworkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    homework_id: UUID


def get_raw_homework_processing_service() -> RawHomeworkProcessingService:
    return RawHomeworkProcessingService(prisma_client)


@router.post("/process")
async def process_raw_homework(
    request: Request,
    body: ProcessRawHomeworkRequest,
    service: RawHomeworkProcessingService = Depends(get_raw_homework_processing_service),
):
    """Load saved homework context and start its initial processing task."""
    teacher_id = request.state.user.get("sub")

    return await service.process(
        homework_id=str(body.homework_id),
        teacher_id=teacher_id,
        homework_marking_graph=request.app.state.homework_marking_graph,
    )
