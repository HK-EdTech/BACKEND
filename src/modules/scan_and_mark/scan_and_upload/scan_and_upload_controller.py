from fastapi import APIRouter, Request, HTTPException
from typing import List
import os
import httpx
from pydantic import BaseModel
from google.cloud import vision
from ....database import prisma_client
from .pydantic_model.scan_and_upload_pydantic_model import ClassWithHomeworkResponse
from .scan_and_upload_service import ScanAndUploadService
from ....ocrs.models.GoogleCloudVisionAPI import GoogleCloudVisionAPI

router = APIRouter(prefix="/scan-and-mark", tags=["Scan and Mark / Scan and Upload"])


def get_scan_and_upload_service():
    return ScanAndUploadService(prisma_client)


@router.get("/classes_subject_homework", response_model=List[ClassWithHomeworkResponse])
async def get_classes_subject_homework(request: Request):
    """Get all classes with their homework for the authenticated teacher."""
    teacher_id = request.state.user.get("sub")
    service = get_scan_and_upload_service()
    return await service.get_classes_with_homework(teacher_id)


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
