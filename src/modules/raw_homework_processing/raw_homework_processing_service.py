"""Validation and image loading for the raw homework processing endpoint.

Uploads are validated here. Processing remains unavailable until the teacher
assistant is connected.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, UploadFile

try:
    from ...common.constants import (
        MAX_IMAGE_BYTES, MAX_IMAGES, MAX_TOTAL_BYTES,
        SOURCE_MARKING_SCHEME, SOURCE_QUESTION_IMAGES, SOURCE_SUBMISSIONS,
    )
    from ...common.images import SUPPORTED_MIMES, ImageBundle, sniff_mime
except ImportError:
    from common.constants import (
        MAX_IMAGE_BYTES, MAX_IMAGES, MAX_TOTAL_BYTES,
        SOURCE_MARKING_SCHEME, SOURCE_QUESTION_IMAGES, SOURCE_SUBMISSIONS,
    )
    from common.images import SUPPORTED_MIMES, ImageBundle, sniff_mime

class RawHomeworkProcessingService:
    async def _load(self, bundle: ImageBundle, files: Optional[List[UploadFile]], role: str, total: int) -> int:
        for upload in files or []:
            # Swagger UI submits an empty file part for optional List[UploadFile] fields.
            if not upload.filename:
                continue
            raw = await upload.read()
            if not raw:
                continue

            if len(raw) > MAX_IMAGE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"{upload.filename} is {len(raw) // 1024 // 1024} MB; the limit is 10 MB",
                )

            total += len(raw)
            if total > MAX_TOTAL_BYTES:
                raise HTTPException(status_code=413, detail="Total upload size exceeds 40 MB")
            if len(bundle) >= MAX_IMAGES:
                raise HTTPException(status_code=413, detail=f"At most {MAX_IMAGES} images per request")

            mime = sniff_mime(raw)
            if mime == "image/heic":
                raise HTTPException(
                    status_code=415,
                    detail=f"{upload.filename} is HEIC. Convert to JPEG or PNG before uploading.",
                )
            if mime not in SUPPORTED_MIMES:
                raise HTTPException(
                    status_code=415,
                    detail=f"{upload.filename} is not a PNG, JPEG or WebP image.",
                )

            bundle.add(role, upload.filename, raw, mime)
        return total

    async def process(
        self,
        submissions: List[UploadFile],
        question_images: Optional[List[UploadFile]] = None,
        marking_scheme_images: Optional[List[UploadFile]] = None,
        extra_information: Optional[str] = None,
    ) -> dict:
        bundle = ImageBundle()
        total = 0
        total = await self._load(bundle, submissions, SOURCE_SUBMISSIONS, total)
        if not bundle.ids_for_role(SOURCE_SUBMISSIONS):
            raise HTTPException(status_code=422, detail="At least one submission image is required")

        total = await self._load(bundle, question_images, SOURCE_QUESTION_IMAGES, total)
        await self._load(bundle, marking_scheme_images, SOURCE_MARKING_SCHEME, total)

        # Upload validation remains available, but graph integration is deferred.
        raise HTTPException(
            status_code=501,
            detail="Raw homework processing is awaiting implementation.",
        )
