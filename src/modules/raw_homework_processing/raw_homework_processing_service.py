"""Validation and image loading for the raw homework processing endpoint.

Uploads are validated and encoded here, before the graph runs, so a bad file fails as
an HTTP error rather than from somewhere inside an agent.
"""
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import HTTPException, UploadFile

try:
    from ...ai_agents.raw_homework_processing import RawHomeworkProcessingAgent
    from ...ai_agents.raw_homework_processing.agent import WorkflowNotImplementedError
    from ...ai_agents.llm import make_llm_factory
    from ...common.images import SUPPORTED_MIMES, ImageBundle, sniff_mime
except ImportError:
    from ai_agents.raw_homework_processing import RawHomeworkProcessingAgent
    from ai_agents.raw_homework_processing.agent import WorkflowNotImplementedError
    from ai_agents.llm import make_llm_factory
    from common.images import SUPPORTED_MIMES, ImageBundle, sniff_mime

SOURCE_SUBMISSIONS = "submissions"
SOURCE_QUESTION_IMAGES = "question_images"
SOURCE_MARKING_SCHEME = "marking_scheme"

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 40 * 1024 * 1024
MAX_IMAGES = 20


class RawHomeworkProcessingService:
    def __init__(self, agent: Optional[RawHomeworkProcessingAgent] = None) -> None:
        self._agent = agent

    def _get_agent(self) -> RawHomeworkProcessingAgent:
        if self._agent is not None:
            return self._agent
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")
        return RawHomeworkProcessingAgent(llm_factory=make_llm_factory(api_key))

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

        agent = self._get_agent()
        try:
            return await agent.run(bundle=bundle, extra_information=extra_information)
        except WorkflowNotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
