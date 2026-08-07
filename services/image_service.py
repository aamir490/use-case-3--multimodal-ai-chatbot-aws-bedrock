"""
services/image_service.py
───────────────────────────
Handles all image file processing for the multimodal chatbot.

Responsibilities:
  - Validate uploaded image files (size, extension, MIME type, dimensions)
  - Normalise image format (convert JPEG aliases, handle transparency)
  - Generate thumbnails for UI preview
  - Return raw bytes for direct Bedrock Converse API image blocks
  - Return structured ImageResult objects consumed by the frontend
  - No Streamlit imports — this layer is UI-agnostic

Supported formats: JPEG, PNG, GIF, WebP
  (Amazon Nova Pro Converse API image block supported formats)
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Maximum image size Nova Pro accepts per image block
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB (conservative; Bedrock limit is higher)

# Supported image extensions → Bedrock format identifiers
SUPPORTED_IMAGE_FORMATS: dict[str, str] = {
    ".jpg":  "jpeg",
    ".jpeg": "jpeg",
    ".png":  "png",
    ".gif":  "gif",
    ".webp": "webp",
}

# Human-readable labels
FORMAT_LABELS: dict[str, str] = {
    "jpeg": "JPEG Image",
    "png":  "PNG Image",
    "gif":  "GIF Image",
    "webp": "WebP Image",
}

# Maximum dimension for thumbnail generation (pixels)
THUMBNAIL_MAX_SIZE = (400, 400)

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ImageResult:
    """Returned by ImageService.process() on success."""
    file_name:     str
    file_size:     int           # bytes
    img_format:    str           # e.g. "jpeg" — the Bedrock format identifier
    raw_bytes:     bytes         # raw image bytes — sent directly to Bedrock
    thumbnail_bytes: Optional[bytes]  # compressed preview for Streamlit st.image()
    width:         int   = 0
    height:        int   = 0
    is_valid:      bool  = True
    error_message: str   = ""

    @property
    def size_kb(self) -> float:
        return round(self.file_size / 1024, 1)

    @property
    def dimensions(self) -> str:
        if self.width and self.height:
            return f"{self.width} × {self.height} px"
        return "Unknown dimensions"

    @property
    def format_label(self) -> str:
        return FORMAT_LABELS.get(self.img_format, self.img_format.upper())


@dataclass
class ImageValidationError:
    """Returned by ImageService.process() on validation failure."""
    file_name:     str
    error_message: str
    is_valid:      bool = False


# ── Service class ─────────────────────────────────────────────────────────────

class ImageService:
    """
    Processes and validates image uploads for Bedrock multimodal inference.

    Usage:
        svc = ImageService()
        result = svc.process(file_bytes, file_name)
        if result.is_valid:
            # pass result.raw_bytes and result.img_format to BedrockService
            # use result.thumbnail_bytes in st.image() for preview
    """

    def __init__(self, max_size_bytes: int = MAX_IMAGE_SIZE_BYTES):
        self.max_size_bytes = max_size_bytes

    # ── Public API ────────────────────────────────────────────────────────────

    def process(
        self, file_bytes: bytes, file_name: str
    ) -> ImageResult | ImageValidationError:
        """
        Validate and process an uploaded image file.

        Args:
            file_bytes: Raw bytes of the uploaded file
            file_name:  Original filename (used for extension detection)

        Returns:
            ImageResult on success, ImageValidationError on failure
        """
        file_name = file_name.strip()

        # 1. Empty file check
        if not file_bytes:
            return ImageValidationError(
                file_name=file_name,
                error_message="File is empty. Please upload a valid image.",
            )

        # 2. File size check
        size = len(file_bytes)
        if size > self.max_size_bytes:
            mb    = round(size / (1024 * 1024), 1)
            limit = round(self.max_size_bytes / (1024 * 1024), 1)
            return ImageValidationError(
                file_name=file_name,
                error_message=(
                    f"Image is too large ({mb} MB). "
                    f"Maximum allowed size is {limit} MB."
                ),
            )

        # 3. Extension check
        ext = Path(file_name).suffix.lower()
        if ext not in SUPPORTED_IMAGE_FORMATS:
            supported = ", ".join(SUPPORTED_IMAGE_FORMATS.keys())
            return ImageValidationError(
                file_name=file_name,
                error_message=(
                    f"Unsupported image format '{ext}'. "
                    f"Supported formats: {supported}"
                ),
            )

        img_format = SUPPORTED_IMAGE_FORMATS[ext]

        # 4. Magic bytes / content integrity check
        integrity_error = self._check_magic_bytes(file_bytes, img_format, file_name)
        if integrity_error:
            return ImageValidationError(
                file_name=file_name, error_message=integrity_error
            )

        # 5. Open with Pillow for dimensions + thumbnail
        width, height, raw_bytes_final, thumbnail_bytes = (
            self._process_with_pillow(file_bytes, img_format)
        )

        logger.info(
            "Image processed: %s | format=%s | size=%d bytes | dims=%dx%d",
            file_name, img_format, size, width, height,
        )

        return ImageResult(
            file_name=file_name,
            file_size=len(raw_bytes_final),
            img_format=img_format,
            raw_bytes=raw_bytes_final,
            thumbnail_bytes=thumbnail_bytes,
            width=width,
            height=height,
            is_valid=True,
        )

    def get_supported_extensions(self) -> list[str]:
        """Return a list of supported file extensions."""
        return list(SUPPORTED_IMAGE_FORMATS.keys())

    def get_accepted_types_string(self) -> list[str]:
        """Return MIME types for Streamlit file_uploader `type` parameter."""
        return ["image/jpeg", "image/png", "image/gif", "image/webp"]

    # ── Private helpers ───────────────────────────────────────────────────────

    def _check_magic_bytes(
        self, file_bytes: bytes, img_format: str, file_name: str
    ) -> Optional[str]:
        """
        Check file magic bytes to catch misnamed or corrupted files.
        Returns an error string if invalid, None if OK.
        """
        header = file_bytes[:12]

        MAGIC: dict[str, list[bytes]] = {
            "jpeg": [b"\xff\xd8\xff"],
            "png":  [b"\x89PNG\r\n\x1a\n"],
            "gif":  [b"GIF87a", b"GIF89a"],
            "webp": [b"RIFF"],  # RIFF....WEBP — needs full 12-byte header
        }

        expected = MAGIC.get(img_format, [])
        if expected:
            # WebP needs a special two-part check: RIFF at 0 and WEBP at 8
            if img_format == "webp":
                if len(file_bytes) < 12 or not (
                    file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP"
                ):
                    return (
                        "File does not appear to be a valid WebP image. "
                        "It may be corrupted or misnamed."
                    )
            elif not any(header.startswith(m) for m in expected):
                return (
                    f"File does not appear to be a valid "
                    f"{img_format.upper()} image. It may be corrupted or misnamed."
                )

        return None

    def _process_with_pillow(
        self, file_bytes: bytes, img_format: str
    ) -> tuple[int, int, bytes, Optional[bytes]]:
        """
        Open image with Pillow to:
          1. Read dimensions
          2. Convert RGBA/palette to RGB for JPEG compatibility
          3. Generate a thumbnail for UI preview

        Returns (width, height, final_bytes, thumbnail_bytes).
        Falls back gracefully if Pillow fails.
        """
        try:
            from PIL import Image, ImageOps

            img = Image.open(io.BytesIO(file_bytes))
            img = ImageOps.exif_transpose(img)  # fix orientation from EXIF

            width, height = img.size

            # For JPEG output, convert palette/RGBA → RGB to avoid Pillow save errors
            final_bytes = file_bytes
            if img_format == "jpeg" and img.mode in ("RGBA", "P", "LA"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                if img.mode in ("RGBA", "LA"):
                    rgb_img.paste(img, mask=img.split()[-1])
                else:
                    rgb_img.paste(img)
                buf = io.BytesIO()
                rgb_img.save(buf, format="JPEG", quality=92)
                final_bytes = buf.getvalue()

            # Generate thumbnail
            thumb = img.copy()
            thumb.thumbnail(THUMBNAIL_MAX_SIZE, Image.LANCZOS)
            # Always save thumbnail as PNG for lossless quality in UI
            if thumb.mode in ("RGBA", "P", "LA"):
                thumb = thumb.convert("RGBA")
            elif thumb.mode not in ("RGB", "L"):
                thumb = thumb.convert("RGB")
            thumb_buf = io.BytesIO()
            thumb.save(thumb_buf, format="PNG", optimize=True)
            thumbnail_bytes = thumb_buf.getvalue()

            return width, height, final_bytes, thumbnail_bytes

        except ImportError:
            logger.warning("Pillow not installed — image processing limited")
            return 0, 0, file_bytes, None
        except Exception as exc:
            logger.warning("Pillow processing failed for image: %s", exc)
            return 0, 0, file_bytes, None
