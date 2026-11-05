"""Image loading for vision LLM calls.

The only base64 path in the backend. Uploads are read once, downscaled once and
encoded once into a data URL; everything downstream passes image *ids* around and
pulls the bytes from an ImageBundle held in the graph config, never in graph state.
"""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Iterable

from PIL import Image

try:
    # When running as part of src package (FastAPI)
    from ..utils.logger import get_logger
except ImportError:
    # When running standalone (tox/pytest with PYTHONPATH=src)
    from utils.logger import get_logger

logger = get_logger(name=__name__)

# Long edge in pixels. A 4000px phone photo costs several times a 1600px one for
# identical extraction quality on printed worksheets.
MAX_EDGE = 1600

SUPPORTED_MIMES = {"image/png", "image/jpeg", "image/webp"}

_PIL_FORMAT = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}


def sniff_mime(data: bytes) -> str | None:
    """Identify an image by magic bytes. Never trust the client's content_type."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    # HEIC/HEIF: iPhone default. Pillow cannot open it without pillow-heif, so it is
    # identified here in order to be rejected with a clear message.
    if data[4:8] == b"ftyp" and data[8:12] in (b"heic", b"heix", b"hevc", b"mif1", b"msf1"):
        return "image/heic"
    return None


@dataclass(frozen=True)
class LoadedImage:
    image_id: str
    role: str
    filename: str
    mime: str
    width: int
    height: int
    byte_size: int
    data_url: str


def downscale_and_encode(raw: bytes, mime: str) -> tuple[str, str, int, int]:
    """Downscale to MAX_EDGE if needed and return (data_url, mime, width, height).

    Format is preserved so crisp text in a PNG is not degraded by a JPEG round trip.
    Images already within the limit are passed through without re-encoding.
    """
    with Image.open(io.BytesIO(raw)) as img:
        width, height = img.size
        longest = max(width, height)

        if longest <= MAX_EDGE:
            encoded = base64.b64encode(raw).decode()
            return f"data:{mime};base64,{encoded}", mime, width, height

        scale = MAX_EDGE / longest
        new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
        resized = img.convert("RGB") if mime == "image/jpeg" else img.copy()
        resized = resized.resize(new_size, Image.LANCZOS)

        buffer = io.BytesIO()
        save_kwargs = {"quality": 88} if mime == "image/jpeg" else {}
        resized.save(buffer, format=_PIL_FORMAT[mime], **save_kwargs)
        data = buffer.getvalue()

    logger.info(
        f"downscaled {width}x{height} -> {new_size[0]}x{new_size[1]} "
        f"({len(raw)} -> {len(data)} bytes)"
    )
    encoded = base64.b64encode(data).decode()
    return f"data:{mime};base64,{encoded}", mime, new_size[0], new_size[1]


class ImageBundle:
    """Holds the encoded images for one request, addressed by id."""

    def __init__(self) -> None:
        self._images: dict[str, LoadedImage] = {}

    def add(self, role: str, filename: str, raw: bytes, mime: str) -> LoadedImage:
        image_id = f"{role}-{len(self._images) + 1}"
        data_url, mime, width, height = downscale_and_encode(raw, mime)
        image = LoadedImage(
            image_id=image_id,
            role=role,
            filename=filename,
            mime=mime,
            width=width,
            height=height,
            byte_size=len(raw),
            data_url=data_url,
        )
        self._images[image_id] = image
        return image

    def __len__(self) -> int:
        return len(self._images)

    def ids_for_role(self, role: str) -> list[str]:
        return [i.image_id for i in self._images.values() if i.role == role]

    def get(self, image_id: str) -> LoadedImage | None:
        return self._images.get(image_id)

    def content_parts(self, image_ids: Iterable[str]) -> list[dict]:
        """OpenRouter multimodal parts. Callers put the text part FIRST, then these."""
        parts = []
        for image_id in image_ids:
            image = self._images.get(image_id)
            if image is None:
                logger.warning(f"unknown image id requested: {image_id}")
                continue
            parts.append({"type": "image_url", "image_url": {"url": image.data_url}})
        return parts
