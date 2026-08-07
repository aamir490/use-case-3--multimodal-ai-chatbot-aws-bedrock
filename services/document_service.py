"""
services/document_service.py
──────────────────────────────
Handles all PDF and document file processing for the multimodal chatbot.

Responsibilities:
  - Validate uploaded document files (size, extension, MIME type, content)
  - Extract raw bytes for direct Bedrock Converse API submission
  - Extract text content for display / preview (pypdf, fallback to raw bytes)
  - Return structured DocumentResult objects consumed by the frontend
  - No Streamlit imports — this layer is UI-agnostic

Design decision — Direct document understanding vs RAG:
  Nova Pro supports PDFs up to 4.5 MB directly in the Converse API.
  For single-document Q&A (the primary portfolio use case) we send document
  bytes directly to the model — no chunking, no vector store, no embeddings.
  This is simpler, cheaper, and more impressive to demo.
  RAG would be appropriate for: corpus of many documents, docs >4.5 MB,
  semantic retrieval across a knowledge base.
"""

from __future__ import annotations

import io
import logging
import mimetypes
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Maximum file size Nova Pro accepts per document block (4.5 MB)
MAX_DOC_SIZE_BYTES = 4 * 1024 * 1024 + 512 * 1024   # 4.5 MB

# Supported document formats and their Bedrock format identifiers
SUPPORTED_DOC_FORMATS: dict[str, str] = {
    ".pdf":  "pdf",
    ".txt":  "txt",
    ".md":   "md",
    ".html": "html",
    ".htm":  "html",
    ".csv":  "csv",
    ".doc":  "doc",
    ".docx": "docx",
    ".xls":  "xls",
    ".xlsx": "xlsx",
}

# Friendly display labels
FORMAT_LABELS: dict[str, str] = {
    "pdf":  "PDF Document",
    "txt":  "Text File",
    "md":   "Markdown File",
    "html": "HTML File",
    "csv":  "CSV Spreadsheet",
    "doc":  "Word Document",
    "docx": "Word Document",
    "xls":  "Excel Spreadsheet",
    "xlsx": "Excel Spreadsheet",
}

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class DocumentResult:
    """Returned by DocumentService.process() on success."""
    file_name:     str
    file_size:     int           # bytes
    doc_format:    str           # e.g. "pdf"
    raw_bytes:     bytes         # raw file bytes — sent directly to Bedrock
    preview_text:  str           # first ~500 chars of extracted text for UI display
    page_count:    int   = 0     # number of pages (PDFs only)
    is_valid:      bool  = True
    error_message: str   = ""

    @property
    def size_kb(self) -> float:
        return round(self.file_size / 1024, 1)

    @property
    def size_mb(self) -> float:
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def format_label(self) -> str:
        return FORMAT_LABELS.get(self.doc_format, self.doc_format.upper())

    @property
    def display_name(self) -> str:
        """Safe short name for Bedrock document block (≤100 chars, no spaces)."""
        stem = Path(self.file_name).stem[:80].replace(" ", "_")
        return stem or "document"


@dataclass
class DocumentValidationError:
    """Returned by DocumentService.process() on validation failure."""
    file_name:     str
    error_message: str
    is_valid:      bool = False


# ── Service class ─────────────────────────────────────────────────────────────

class DocumentService:
    """
    Processes and validates document uploads for Bedrock multimodal inference.

    Usage:
        svc = DocumentService()
        result = svc.process(file_bytes, file_name)
        if result.is_valid:
            # pass result.raw_bytes and result.display_name to BedrockService
    """

    def __init__(self, max_size_bytes: int = MAX_DOC_SIZE_BYTES):
        self.max_size_bytes = max_size_bytes

    # ── Public API ────────────────────────────────────────────────────────────

    def process(
        self, file_bytes: bytes, file_name: str
    ) -> DocumentResult | DocumentValidationError:
        """
        Validate and process an uploaded document file.

        Args:
            file_bytes: Raw bytes of the uploaded file
            file_name:  Original filename (used for extension detection)

        Returns:
            DocumentResult on success, DocumentValidationError on failure
        """
        file_name = file_name.strip()

        # 1. Empty file check
        if not file_bytes:
            return DocumentValidationError(
                file_name=file_name,
                error_message="File is empty. Please upload a valid document.",
            )

        # 2. File size check
        size = len(file_bytes)
        if size > self.max_size_bytes:
            mb = round(size / (1024 * 1024), 1)
            limit_mb = round(self.max_size_bytes / (1024 * 1024), 1)
            return DocumentValidationError(
                file_name=file_name,
                error_message=(
                    f"File is too large ({mb} MB). "
                    f"Maximum allowed size is {limit_mb} MB."
                ),
            )

        # 3. Extension check
        ext = Path(file_name).suffix.lower()
        if ext not in SUPPORTED_DOC_FORMATS:
            supported = ", ".join(SUPPORTED_DOC_FORMATS.keys())
            return DocumentValidationError(
                file_name=file_name,
                error_message=(
                    f"Unsupported file type '{ext}'. "
                    f"Supported formats: {supported}"
                ),
            )

        doc_format = SUPPORTED_DOC_FORMATS[ext]

        # 4. Basic content integrity check
        integrity_error = self._check_content_integrity(file_bytes, doc_format, file_name)
        if integrity_error:
            return DocumentValidationError(
                file_name=file_name, error_message=integrity_error
            )

        # 5. Extract preview text and page count
        preview_text, page_count = self._extract_preview(file_bytes, doc_format)

        logger.info(
            "Document processed: %s | format=%s | size=%d bytes | pages=%d",
            file_name, doc_format, size, page_count,
        )

        return DocumentResult(
            file_name=file_name,
            file_size=size,
            doc_format=doc_format,
            raw_bytes=file_bytes,
            preview_text=preview_text,
            page_count=page_count,
            is_valid=True,
        )

    def get_supported_extensions(self) -> list[str]:
        """Return a list of supported file extensions."""
        return list(SUPPORTED_DOC_FORMATS.keys())

    def get_supported_mime_types(self) -> list[str]:
        """Return MIME types for Streamlit file_uploader type filter."""
        mime_types = []
        for ext in SUPPORTED_DOC_FORMATS:
            mime, _ = mimetypes.guess_type(f"file{ext}")
            if mime:
                mime_types.append(mime)
        # Always include PDF explicitly
        if "application/pdf" not in mime_types:
            mime_types.insert(0, "application/pdf")
        return mime_types

    # ── Private helpers ───────────────────────────────────────────────────────

    def _check_content_integrity(
        self, file_bytes: bytes, doc_format: str, file_name: str
    ) -> Optional[str]:
        """
        Perform a lightweight content integrity check.
        Returns an error string if corrupt/invalid, None if OK.
        """
        if doc_format == "pdf":
            # PDF files must start with the %PDF magic bytes
            if not file_bytes.startswith(b"%PDF"):
                return (
                    "File does not appear to be a valid PDF "
                    "(missing %PDF header). It may be corrupted."
                )
            # Must also contain %%EOF somewhere near the end
            tail = file_bytes[-1024:]
            if b"%%EOF" not in tail and b"startxref" not in tail:
                return (
                    "PDF appears to be truncated or corrupted "
                    "(missing %%EOF marker)."
                )

        elif doc_format in ("doc", "docx", "xls", "xlsx"):
            # Office Open XML and legacy Office files share magic bytes
            if not (
                file_bytes[:4] == b"PK\x03\x04"       # OOXML (docx/xlsx)
                or file_bytes[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # legacy OLE
            ):
                return (
                    f"File does not appear to be a valid "
                    f"{doc_format.upper()} document. It may be corrupted."
                )

        elif doc_format == "html":
            # HTML should contain recognisable markup
            snippet = file_bytes[:512].lower()
            if not (b"<html" in snippet or b"<!doctype" in snippet or b"<body" in snippet):
                logger.debug("HTML file %s lacks standard HTML tags — proceeding anyway", file_name)

        return None  # no error

    def _extract_preview(
        self, file_bytes: bytes, doc_format: str
    ) -> tuple[str, int]:
        """
        Extract a short preview of the document text and page count.

        Returns (preview_text, page_count).
        Falls back gracefully if pypdf is not installed.
        """
        preview_text = ""
        page_count   = 0

        if doc_format == "pdf":
            preview_text, page_count = self._extract_pdf_preview(file_bytes)

        elif doc_format in ("txt", "md", "csv", "html"):
            try:
                raw = file_bytes.decode("utf-8", errors="replace")
                preview_text = raw[:600].strip()
                # Approximate "pages" for text files by line count
                line_count = raw.count("\n")
                page_count = max(1, line_count // 40)
            except Exception:
                preview_text = "[Preview unavailable]"

        else:
            # docx, xlsx, doc, xls — preview not extracted without heavy deps
            preview_text = (
                f"[{doc_format.upper()} document uploaded. "
                "Preview not available — ask questions to explore the content.]"
            )

        return preview_text, page_count

    def _extract_pdf_preview(self, file_bytes: bytes) -> tuple[str, int]:
        """
        Extract text preview and page count from a PDF using pypdf.
        Falls back to a status message if pypdf is not installed.
        """
        try:
            import pypdf  # optional dependency

            reader     = pypdf.PdfReader(io.BytesIO(file_bytes))
            page_count = len(reader.pages)
            extracted  = []

            # Extract text from up to the first 3 pages for preview
            for page in reader.pages[:3]:
                try:
                    text = page.extract_text() or ""
                    extracted.append(text.strip())
                except Exception:
                    continue

            preview = "\n\n".join(extracted)[:600].strip()
            if not preview:
                preview = "[PDF text could not be extracted — may be scanned/image-based. The AI will still analyse it.]"

            return preview, page_count

        except ImportError:
            logger.info("pypdf not installed — PDF preview unavailable")
            return (
                "[PDF uploaded. Install pypdf for text preview: pip install pypdf]\n"
                "The document will still be sent to the AI for analysis.",
                0,
            )
        except Exception as exc:
            logger.warning("PDF preview extraction failed: %s", exc)
            return (
                f"[PDF preview failed: {exc}. The document will still be sent to the AI.]",
                0,
            )
