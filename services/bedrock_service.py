"""
services/bedrock_service.py
────────────────────────────
Central service for all Amazon Bedrock interactions.

Responsibilities:
  - Build well-formed Converse API message payloads for text, image, and document inputs
  - Call Amazon Nova Pro via boto3 bedrock-runtime (streaming + non-streaming)
  - Manage conversation history as a plain list of role/content dicts
  - Provide a clean public interface consumed by mod_chatbot_frontend.py
  - No Streamlit imports — this layer is UI-agnostic

Model used: amazon.nova-pro-v1:0
  Fallback : us.amazon.nova-pro-v1:0  (cross-region inference profile)
"""

from __future__ import annotations

import os
import logging
from typing import Generator, Optional

import boto3
import botocore.exceptions

logger = logging.getLogger(__name__)

# ── Model / region config ─────────────────────────────────────────────────────
# Can be overridden via environment variables — never hard-coded secrets here.
_DEFAULT_MODEL_ID        = "amazon.nova-pro-v1:0"
_FALLBACK_MODEL_ID       = "us.amazon.nova-pro-v1:0"  # cross-region inference profile
_DEFAULT_REGION          = "us-east-1"
_DEFAULT_MAX_TOKENS      = 2048
_DEFAULT_TEMPERATURE     = 0.7

# System prompt that gives the assistant its persona
_DEFAULT_SYSTEM_PROMPT = (
    "You are NovaMind, an intelligent multimodal AI assistant powered by "
    "Amazon Nova Pro on AWS Bedrock. You can understand and discuss text, "
    "images, and documents. Be helpful, accurate, concise, and professional. "
    "When analysing images or documents, be specific and thorough. "
    "If you are unsure about something, say so clearly."
)


class BedrockService:
    """
    Manages all communication with Amazon Bedrock's Converse API.

    Usage:
        service = BedrockService()
        history = []

        # Text only
        for chunk in service.stream_response("What is AWS?", history):
            print(chunk, end="", flush=True)

        # With an image
        for chunk in service.stream_response(
            "What is in this image?", history, image_bytes=img_bytes, image_format="jpeg"
        ):
            print(chunk, end="", flush=True)

        # With a PDF document
        for chunk in service.stream_response(
            "Summarise this document.", history, doc_bytes=pdf_bytes, doc_name="report"
        ):
            print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        region: Optional[str] = None,
        model_id: Optional[str] = None,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        temperature: float = _DEFAULT_TEMPERATURE,
        system_prompt: Optional[str] = None,
    ):
        self.region       = region       or os.environ.get("AWS_DEFAULT_REGION", _DEFAULT_REGION)
        self.model_id     = model_id     or os.environ.get("BEDROCK_MODEL_ID",    _DEFAULT_MODEL_ID)
        self.max_tokens   = max_tokens
        self.temperature  = temperature
        self.system_prompt = system_prompt or os.environ.get(
            "BEDROCK_SYSTEM_PROMPT", _DEFAULT_SYSTEM_PROMPT
        )

        # boto3 client — uses default credentials chain:
        # 1. Env vars (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)
        # 2. ~/.aws/credentials default profile
        # 3. IAM role (EC2 instance profile / ECS task role)
        self._client = boto3.client("bedrock-runtime", region_name=self.region)
        self._active_model_id: Optional[str] = None  # resolved at first call

    # ── Public API ─────────────────────────────────────────────────────────────

    def stream_response(
        self,
        user_text: str,
        history: list[dict],
        *,
        image_bytes:  Optional[bytes] = None,
        image_format: Optional[str]   = None,   # "jpeg" | "png" | "gif" | "webp"
        doc_bytes:    Optional[bytes] = None,
        doc_name:     Optional[str]   = None,
        doc_format:   Optional[str]   = "pdf",  # "pdf" | "txt" | "html" | "md" | "csv"
    ) -> Generator[str, None, None]:
        """
        Send a message to Bedrock and yield response chunks as they arrive.

        Mutates `history` in-place — appends the new user turn and the
        complete assistant reply once streaming is done.

        Yields:
            str  — incremental text chunks from the model
        """
        # Build the current user message content blocks
        content_blocks = self._build_content_blocks(
            user_text, image_bytes, image_format, doc_bytes, doc_name, doc_format
        )

        # Append new user turn to history for the API call
        messages_for_api = history + [{"role": "user", "content": content_blocks}]

        payload = {
            "modelId":        self._resolve_model_id(),
            "messages":       messages_for_api,
            "system":         [{"text": self.system_prompt}],
            "inferenceConfig": {
                "maxTokens":   self.max_tokens,
                "temperature": self.temperature,
            },
        }

        full_reply = ""
        try:
            response = self._client.converse_stream(**payload)
            for event in response["stream"]:
                if "contentBlockDelta" in event:
                    chunk = event["contentBlockDelta"]["delta"].get("text", "")
                    if chunk:
                        full_reply += chunk
                        yield chunk
                elif "messageDone" in event or "messageStop" in event:
                    break
        except botocore.exceptions.ClientError as exc:
            err_code = exc.response["Error"]["Code"]
            if err_code == "AccessDeniedException" and self._active_model_id == self.model_id:
                # First call failed with the base model ID — retry with inference profile
                logger.warning(
                    "Access denied for %s, retrying with inference profile %s",
                    self.model_id, _FALLBACK_MODEL_ID,
                )
                self._active_model_id = _FALLBACK_MODEL_ID
                yield from self.stream_response(
                    user_text, history,
                    image_bytes=image_bytes, image_format=image_format,
                    doc_bytes=doc_bytes, doc_name=doc_name, doc_format=doc_format,
                )
                return
            error_msg = f"[Bedrock error — {err_code}]: {exc.response['Error']['Message']}"
            logger.error(error_msg)
            yield error_msg
            full_reply = error_msg
        except Exception as exc:
            error_msg = f"[Unexpected error]: {exc}"
            logger.exception(error_msg)
            yield error_msg
            full_reply = error_msg

        # Update history with both the user turn and the complete assistant reply
        # Store user turn with readable text (strip multimodal blocks for display)
        history.append({"role": "user",      "content": content_blocks})
        history.append({"role": "assistant", "content": [{"text": full_reply}]})

    def invoke_response(
        self,
        user_text: str,
        history: list[dict],
        *,
        image_bytes:  Optional[bytes] = None,
        image_format: Optional[str]   = None,
        doc_bytes:    Optional[bytes] = None,
        doc_name:     Optional[str]   = None,
        doc_format:   Optional[str]   = "pdf",
    ) -> str:
        """
        Non-streaming version of stream_response.
        Returns the full reply as a single string.
        Useful for simple tests or non-UI contexts.
        """
        return "".join(
            self.stream_response(
                user_text, history,
                image_bytes=image_bytes, image_format=image_format,
                doc_bytes=doc_bytes, doc_name=doc_name, doc_format=doc_format,
            )
        )

    def clear_history(self, history: list[dict]) -> None:
        """Clear all turns from the provided history list."""
        history.clear()

    def get_model_info(self) -> dict:
        """Return a dict with the current model configuration."""
        return {
            "model_id":      self._active_model_id or self.model_id,
            "region":        self.region,
            "max_tokens":    self.max_tokens,
            "temperature":   self.temperature,
            "streaming":     True,
        }

    # ── Private helpers ────────────────────────────────────────────────────────

    def _resolve_model_id(self) -> str:
        """Return the active model ID, defaulting to the configured one."""
        if self._active_model_id is None:
            self._active_model_id = self.model_id
        return self._active_model_id

    def _build_content_blocks(
        self,
        user_text:    str,
        image_bytes:  Optional[bytes],
        image_format: Optional[str],
        doc_bytes:    Optional[bytes],
        doc_name:     Optional[str],
        doc_format:   Optional[str],
    ) -> list[dict]:
        """
        Build the Converse API content blocks list for a user turn.

        Converse API format:
          [
            { "image": { "format": "jpeg", "source": { "bytes": <bytes> } } },
            { "document": { "format": "pdf", "name": "myfile", "source": { "bytes": <bytes> } } },
            { "text": "user question here" }
          ]

        Text block always goes last — this is the recommended ordering for
        multimodal prompts with Nova models.
        """
        blocks: list[dict] = []

        # Image block
        if image_bytes and image_format:
            fmt = image_format.lower().lstrip(".")
            # Nova Pro supports: jpeg, png, gif, webp
            if fmt == "jpg":
                fmt = "jpeg"
            blocks.append({
                "image": {
                    "format": fmt,
                    "source": {"bytes": image_bytes},
                }
            })

        # Document block
        if doc_bytes:
            name = (doc_name or "document").replace(" ", "_")[:100]
            fmt  = (doc_format or "pdf").lower().lstrip(".")
            # Nova Pro document formats: pdf, csv, doc, docx, xls, xlsx, html, txt, md
            blocks.append({
                "document": {
                    "format": fmt,
                    "name":   name,
                    "source": {"bytes": doc_bytes},
                }
            })

        # Text block (always last)
        if user_text and user_text.strip():
            blocks.append({"text": user_text.strip()})

        return blocks

    def update_settings(
        self,
        temperature:   Optional[float] = None,
        max_tokens:    Optional[int]   = None,
        system_prompt: Optional[str]   = None,
    ) -> None:
        """Dynamically update inference settings without rebuilding the client."""
        if temperature   is not None: self.temperature   = temperature
        if max_tokens    is not None: self.max_tokens    = max_tokens
        if system_prompt is not None: self.system_prompt = system_prompt


# ── Module-level convenience factory ─────────────────────────────────────────

def get_bedrock_service(
    region:        Optional[str] = None,
    model_id:      Optional[str] = None,
    max_tokens:    int            = _DEFAULT_MAX_TOKENS,
    temperature:   float          = _DEFAULT_TEMPERATURE,
    system_prompt: Optional[str]  = None,
) -> BedrockService:
    """
    Factory function — returns a BedrockService instance.
    The frontend calls this once at startup and caches it in session_state.
    """
    return BedrockService(
        region=region,
        model_id=model_id,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt,
    )
