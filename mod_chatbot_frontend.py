"""
mod_chatbot_frontend.py
────────────────────────
NovaMind AI — Production-grade multimodal chatbot powered by Amazon Bedrock.

Supports:
  • Text conversations with full context memory
  • Image upload & visual analysis (JPEG, PNG, GIF, WebP)
  • Document upload & Q&A (PDF, TXT, MD, CSV, DOCX, XLSX, HTML)
  • Streaming responses (token-by-token display)
  • Conversation export as plain text
  • Configurable model settings via sidebar

Run:
    streamlit run mod_chatbot_frontend.py
"""

import sys
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
# Ensure the project root is on sys.path so services/ and utils/ are importable
# regardless of the working directory when streamlit is invoked.
ROOT = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Service imports ───────────────────────────────────────────────────────────
from services.bedrock_service import get_bedrock_service, BedrockService
from services.document_service import DocumentResult, DocumentValidationError
from services.image_service import ImageResult, ImageValidationError
from utils.validators import (
    validate_file_upload,
    is_image_file,
    is_document_file,
    format_file_size,
    sanitize_filename,
    export_conversation_as_text,
    sanitize_user_input,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NovaMind AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://docs.aws.amazon.com/bedrock/",
        "About": "NovaMind AI — Multimodal chatbot powered by Amazon Nova Pro on AWS Bedrock.",
    },
)

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CSS / Styling
# ═════════════════════════════════════════════════════════════════════════════

def _inject_css() -> None:
    """Inject custom CSS for the ChatGPT-style interface."""
    st.markdown(
        """
        <style>
        /* ── App background ── */
        .stApp { background: #0d1117; color: #e6edf3; }

        /* ── Remove default top padding ── */
        .block-container { padding-top: 0.8rem; padding-bottom: 1rem; }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {
            background: #161b22;
            border-right: 1px solid #30363d;
        }
        section[data-testid="stSidebar"] * { color: #e6edf3 !important; }

        /* ── Hero header ── */
        .nm-hero {
            background: linear-gradient(135deg, #1f6feb 0%, #388bfd 50%, #58a6ff 100%);
            border-radius: 14px;
            padding: 1rem 1.4rem;
            margin-bottom: 1rem;
            color: white;
            box-shadow: 0 4px 24px rgba(31,111,235,0.35);
        }
        .nm-hero h1 { margin: 0 0 0.2rem 0; font-size: 1.6rem; font-weight: 700; }
        .nm-hero p  { margin: 0; opacity: 0.85; font-size: 0.92rem; }

        /* ── Chat messages ── */
        div[data-testid="stChatMessage"] { padding: 0.3rem 0; }

        /* ── File attachment pill ── */
        .nm-attachment {
            display: inline-flex; align-items: center; gap: 6px;
            background: #21262d; border: 1px solid #30363d;
            border-radius: 20px; padding: 4px 12px;
            font-size: 0.8rem; color: #8b949e; margin-bottom: 6px;
        }

        /* ── Status badge ── */
        .nm-badge-image    { color: #3fb950; font-weight: 600; }
        .nm-badge-document { color: #d29922; font-weight: 600; }
        .nm-badge-text     { color: #58a6ff; font-weight: 600; }

        /* ── Model info card ── */
        .nm-model-card {
            background: #161b22; border: 1px solid #30363d;
            border-radius: 10px; padding: 0.7rem 1rem;
            font-size: 0.8rem; color: #8b949e; margin-top: 0.5rem;
        }
        .nm-model-card strong { color: #58a6ff; }

        /* ── Upload info box ── */
        .nm-upload-info {
            background: #0d1117; border: 1px dashed #30363d;
            border-radius: 10px; padding: 0.6rem 0.9rem;
            font-size: 0.82rem; color: #8b949e;
        }

        /* ── Scrollable preview ── */
        .nm-preview {
            background: #161b22; border: 1px solid #30363d;
            border-radius: 8px; padding: 0.6rem 0.8rem;
            max-height: 180px; overflow-y: auto;
            font-size: 0.78rem; color: #8b949e;
            white-space: pre-wrap; word-break: break-word;
        }

        /* ── Streamlit button overrides ── */
        .stButton > button {
            background: #21262d; border: 1px solid #30363d;
            color: #e6edf3; border-radius: 8px;
            transition: background 0.15s ease;
        }
        .stButton > button:hover { background: #30363d; border-color: #58a6ff; }

        /* ── Divider ── */
        hr { border-color: #30363d !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Session state initialisation
# ═════════════════════════════════════════════════════════════════════════════

def _init_session_state() -> None:
    """Initialise all session state keys with safe defaults."""

    # Bedrock conversation history — list of Converse API message dicts
    if "bedrock_history" not in st.session_state:
        st.session_state.bedrock_history = []

    # UI chat history — list of display dicts
    # Each dict: {"role", "text", "type", "file_name", "timestamp", "avatar"}
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Cached BedrockService instance
    if "bedrock_service" not in st.session_state:
        st.session_state.bedrock_service = None

    # Pending file upload state — set when user uploads a file
    # Cleared after the file is sent with a message
    if "pending_image"    not in st.session_state:
        st.session_state.pending_image    = None  # ImageResult
    if "pending_document" not in st.session_state:
        st.session_state.pending_document = None  # DocumentResult

    # Model settings (sidebar controls)
    if "temperature"   not in st.session_state: st.session_state.temperature   = 0.7
    if "max_tokens"    not in st.session_state: st.session_state.max_tokens    = 2048
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = (
            "You are NovaMind, an intelligent multimodal AI assistant powered by "
            "Amazon Nova Pro on AWS Bedrock. You can understand and discuss text, "
            "images, and documents. Be helpful, accurate, and professional."
        )

    # UI state
    if "bot_name"          not in st.session_state: st.session_state.bot_name          = "NovaMind"
    if "show_model_info"   not in st.session_state: st.session_state.show_model_info   = True
    if "conversation_count" not in st.session_state: st.session_state.conversation_count = 0


def _get_or_create_service() -> BedrockService:
    """Return the cached BedrockService, creating it if needed."""
    if st.session_state.bedrock_service is None:
        st.session_state.bedrock_service = get_bedrock_service(
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            system_prompt=st.session_state.system_prompt,
        )
    return st.session_state.bedrock_service


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Sidebar
# ═════════════════════════════════════════════════════════════════════════════

def _render_sidebar() -> None:
    """Render the full sidebar: settings, file upload, model info, actions."""
    with st.sidebar:
        st.markdown("## 🤖 NovaMind AI")
        st.markdown("*Multimodal assistant — Amazon Bedrock*")
        st.divider()

        # ── Bot name ──────────────────────────────────────────────────────────
        st.markdown("### ⚙️ Settings")
        bot_name = st.text_input(
            "Assistant name",
            value=st.session_state.bot_name,
            max_chars=30,
            help="Displayed in chat bubbles and the header.",
        )
        st.session_state.bot_name = bot_name or "NovaMind"

        # ── Temperature ───────────────────────────────────────────────────────
        temperature = st.slider(
            "Temperature",
            min_value=0.0, max_value=1.0,
            value=st.session_state.temperature,
            step=0.05,
            help="Higher = more creative. Lower = more focused and deterministic.",
        )

        # ── Max tokens ────────────────────────────────────────────────────────
        max_tokens = st.select_slider(
            "Max response tokens",
            options=[256, 512, 1024, 2048, 4096, 8192],
            value=st.session_state.max_tokens,
            help="Maximum length of each AI response.",
        )

        # ── System prompt ─────────────────────────────────────────────────────
        with st.expander("🧠 System prompt", expanded=False):
            system_prompt = st.text_area(
                "Persona / instructions",
                value=st.session_state.system_prompt,
                height=130,
                help="Defines the AI's personality and behaviour.",
            )
            if st.button("Apply system prompt", use_container_width=True):
                st.session_state.system_prompt = system_prompt
                if st.session_state.bedrock_service:
                    st.session_state.bedrock_service.update_settings(
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt,
                    )
                st.success("System prompt updated.")

        # Apply temperature/token changes whenever they move
        if (temperature != st.session_state.temperature or
                max_tokens != st.session_state.max_tokens):
            st.session_state.temperature = temperature
            st.session_state.max_tokens  = max_tokens
            if st.session_state.bedrock_service:
                st.session_state.bedrock_service.update_settings(
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

        st.divider()

        # ── File upload ───────────────────────────────────────────────────────
        st.markdown("### 📎 Attach a File")
        st.markdown(
            '<div class="nm-upload-info">'
            "📷 <b>Images:</b> JPEG, PNG, GIF, WebP (max 5 MB)<br>"
            "📄 <b>Documents:</b> PDF, TXT, MD, CSV, DOCX, XLSX, HTML (max 4.5 MB)"
            "</div>",
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Upload image or document",
            type=[
                "jpg", "jpeg", "png", "gif", "webp",
                "pdf", "txt", "md", "csv",
                "doc", "docx", "xls", "xlsx", "html", "htm",
            ],
            help="Attach a file to discuss with the AI. Then type your question below.",
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            _handle_file_upload(uploaded_file)

        # Show currently pending attachment
        _render_pending_attachment()

        st.divider()

        # ── Conversation actions ──────────────────────────────────────────────
        st.markdown("### 💬 Conversation")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear", use_container_width=True, help="Clear conversation"):
                _clear_conversation()
                st.rerun()
        with col2:
            if st.button("🔄 New", use_container_width=True, help="Start a new conversation"):
                _clear_conversation()
                st.session_state.conversation_count += 1
                st.rerun()

        # Download transcript
        if st.session_state.chat_history:
            transcript = export_conversation_as_text(
                st.session_state.chat_history,
                bot_name=st.session_state.bot_name,
            )
            st.download_button(
                label="⬇️ Download transcript",
                data=transcript,
                file_name=f"novabot_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # Message count badge
        msg_count = len(st.session_state.chat_history)
        if msg_count:
            turns = msg_count // 2
            st.caption(f"💬 {msg_count} messages · {turns} turn{'s' if turns != 1 else ''}")

        st.divider()

        # ── Model info card ───────────────────────────────────────────────────
        if st.session_state.show_model_info:
            svc = st.session_state.bedrock_service
            model_id = svc.model_id if svc else "amazon.nova-pro-v1:0"
            region   = svc.region   if svc else os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
            st.markdown(
                f'<div class="nm-model-card">'
                f'<strong>Model</strong> {model_id}<br>'
                f'<strong>Region</strong> {region}<br>'
                f'<strong>Temp</strong> {st.session_state.temperature} &nbsp;'
                f'<strong>MaxTok</strong> {st.session_state.max_tokens}'
                f'</div>',
                unsafe_allow_html=True,
            )


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — File upload handlers
# ═════════════════════════════════════════════════════════════════════════════

def _handle_file_upload(uploaded_file) -> None:
    """
    Process a Streamlit UploadedFile object through the validation pipeline.
    Sets st.session_state.pending_image or .pending_document on success.
    Shows an error in the sidebar on failure.
    """
    raw_bytes = uploaded_file.read()
    file_name = sanitize_filename(uploaded_file.name)

    result = validate_file_upload(raw_bytes, file_name)

    if isinstance(result, (ImageValidationError, DocumentValidationError)):
        st.error(f"❌ {result.error_message}")
        return

    if isinstance(result, ImageResult):
        st.session_state.pending_image    = result
        st.session_state.pending_document = None
        st.success(f"✅ Image ready: **{result.file_name}** ({result.size_kb} KB)")

    elif isinstance(result, DocumentResult):
        st.session_state.pending_document = result
        st.session_state.pending_image    = None
        label = f"{result.format_label}: **{result.file_name}** ({result.size_kb} KB)"
        if result.page_count:
            label += f" · {result.page_count} page{'s' if result.page_count != 1 else ''}"
        st.success(f"✅ Document ready: {label}")


def _render_pending_attachment() -> None:
    """Show a preview of the currently attached file in the sidebar."""
    img = st.session_state.pending_image
    doc = st.session_state.pending_document

    if img:
        st.markdown(
            f'<div class="nm-attachment">'
            f'🖼️ <span class="nm-badge-image">IMAGE</span> '
            f'{img.file_name} · {img.size_kb} KB'
            f'</div>',
            unsafe_allow_html=True,
        )
        # Show thumbnail if Pillow generated one
        if img.thumbnail_bytes:
            st.image(img.thumbnail_bytes, caption=img.dimensions, use_container_width=True)
        if st.button("✕ Remove image", use_container_width=True):
            st.session_state.pending_image = None
            st.rerun()

    elif doc:
        st.markdown(
            f'<div class="nm-attachment">'
            f'📄 <span class="nm-badge-document">DOC</span> '
            f'{doc.file_name} · {doc.size_kb} KB'
            f'</div>',
            unsafe_allow_html=True,
        )
        if doc.preview_text:
            with st.expander("Preview extracted text", expanded=False):
                st.markdown(
                    f'<div class="nm-preview">{doc.preview_text}</div>',
                    unsafe_allow_html=True,
                )
        if st.button("✕ Remove document", use_container_width=True):
            st.session_state.pending_document = None
            st.rerun()


def _clear_conversation() -> None:
    """Reset all conversation state."""
    st.session_state.bedrock_history  = []
    st.session_state.chat_history     = []
    st.session_state.pending_image    = None
    st.session_state.pending_document = None
    # Recreate service to reset any model fallback state
    st.session_state.bedrock_service  = None


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Chat history rendering
# ═════════════════════════════════════════════════════════════════════════════

def _render_chat_history() -> None:
    """Re-render all previous messages from session state."""
    for msg in st.session_state.chat_history:
        role      = msg["role"]
        text      = msg.get("text", "")
        msg_type  = msg.get("type", "text")
        file_name = msg.get("file_name", "")
        avatar    = "🧑" if role == "user" else "🤖"

        with st.chat_message(role, avatar=avatar):
            # Attachment pill above the text
            if msg_type == "image" and file_name:
                st.markdown(
                    f'<div class="nm-attachment">'
                    f'🖼️ <span class="nm-badge-image">IMAGE</span> {file_name}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                # Re-render thumbnail if stored
                if msg.get("thumbnail_bytes"):
                    st.image(msg["thumbnail_bytes"], width=280)

            elif msg_type == "document" and file_name:
                st.markdown(
                    f'<div class="nm-attachment">'
                    f'📄 <span class="nm-badge-document">DOCUMENT</span> {file_name}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            if text:
                st.markdown(text)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6 — AI response streaming
# ═════════════════════════════════════════════════════════════════════════════

def _stream_and_display_response(
    user_text:    str,
    service:      BedrockService,
    image_result: ImageResult  | None,
    doc_result:   DocumentResult | None,
) -> str:
    """
    Call BedrockService.stream_response() and display chunks in real time
    inside a st.chat_message("assistant") bubble.

    Returns the full assembled response text.
    """
    full_response = ""

    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()

        # Build kwargs for stream_response
        kwargs: dict = {}
        if image_result:
            kwargs["image_bytes"]  = image_result.raw_bytes
            kwargs["image_format"] = image_result.img_format
        if doc_result:
            kwargs["doc_bytes"]  = doc_result.raw_bytes
            kwargs["doc_name"]   = doc_result.display_name
            kwargs["doc_format"] = doc_result.doc_format

        try:
            for chunk in service.stream_response(
                user_text=user_text,
                history=st.session_state.bedrock_history,
                **kwargs,
            ):
                full_response += chunk
                placeholder.markdown(full_response + "▌")  # typing cursor

            placeholder.markdown(full_response)  # final render without cursor

        except Exception as exc:
            error_msg = f"⚠️ An error occurred: {exc}"
            placeholder.error(error_msg)
            full_response = error_msg

    return full_response


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Main chat input handler
# ═════════════════════════════════════════════════════════════════════════════

def _handle_user_input(user_input: str) -> None:
    """
    Process a submitted chat message:
      1. Display the user message (with attachment pill if applicable)
      2. Capture any pending attachment
      3. Stream the AI response
      4. Save both turns to chat_history
      5. Clear the pending attachment
    """
    service = _get_or_create_service()

    # Sanitise input
    user_text = sanitize_user_input(user_input)

    # Capture and immediately clear pending attachment
    # (so re-runs don't re-send the same file)
    image_result = st.session_state.pending_image
    doc_result   = st.session_state.pending_document

    # ── 1. Display user message ───────────────────────────────────────────────
    with st.chat_message("user", avatar="🧑"):
        if image_result:
            st.markdown(
                f'<div class="nm-attachment">'
                f'🖼️ <span class="nm-badge-image">IMAGE</span> {image_result.file_name}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if image_result.thumbnail_bytes:
                st.image(image_result.thumbnail_bytes, width=280)
        elif doc_result:
            st.markdown(
                f'<div class="nm-attachment">'
                f'📄 <span class="nm-badge-document">DOCUMENT</span> {doc_result.file_name}'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown(user_text)

    # ── 2. Save user turn to UI history ──────────────────────────────────────
    user_msg: dict = {
        "role":      "user",
        "text":      user_text,
        "timestamp": datetime.now().strftime("%H:%M"),
        "avatar":    "🧑",
    }
    if image_result:
        user_msg["type"]            = "image"
        user_msg["file_name"]       = image_result.file_name
        user_msg["thumbnail_bytes"] = image_result.thumbnail_bytes
    elif doc_result:
        user_msg["type"]      = "document"
        user_msg["file_name"] = doc_result.file_name
    else:
        user_msg["type"] = "text"

    st.session_state.chat_history.append(user_msg)

    # ── 3. Clear pending attachments immediately ──────────────────────────────
    st.session_state.pending_image    = None
    st.session_state.pending_document = None

    # ── 4. Stream AI response ─────────────────────────────────────────────────
    full_response = _stream_and_display_response(
        user_text=user_text,
        service=service,
        image_result=image_result,
        doc_result=doc_result,
    )

    # ── 5. Save assistant turn to UI history ──────────────────────────────────
    st.session_state.chat_history.append({
        "role":      "assistant",
        "text":      full_response,
        "type":      "text",
        "timestamp": datetime.now().strftime("%H:%M"),
        "avatar":    "🤖",
    })


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Welcome / empty state
# ═════════════════════════════════════════════════════════════════════════════

def _render_welcome() -> None:
    """Show capability cards when the conversation is empty."""
    st.markdown(
        """
        <div style="text-align:center; padding: 1.5rem 0 1rem 0; color: #8b949e;">
            <p style="font-size:0.95rem;">
                Ask me anything, upload an image to analyse, or attach a PDF to explore.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div style="background:#161b22; border:1px solid #30363d; border-radius:12px;
                        padding:1rem; text-align:center;">
              <div style="font-size:2rem;">💬</div>
              <div style="color:#58a6ff; font-weight:600; margin:0.4rem 0;">Text Chat</div>
              <div style="color:#8b949e; font-size:0.82rem;">
                Multi-turn conversations with full context memory.
                Follow-up questions, reasoning, explanations.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style="background:#161b22; border:1px solid #30363d; border-radius:12px;
                        padding:1rem; text-align:center;">
              <div style="font-size:2rem;">🖼️</div>
              <div style="color:#3fb950; font-weight:600; margin:0.4rem 0;">Image Analysis</div>
              <div style="color:#8b949e; font-size:0.82rem;">
                Upload JPEG, PNG, GIF, or WebP. Ask questions about
                what the model sees, extract text, describe scenes.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div style="background:#161b22; border:1px solid #30363d; border-radius:12px;
                        padding:1rem; text-align:center;">
              <div style="font-size:2rem;">📄</div>
              <div style="color:#d29922; font-weight:600; margin:0.4rem 0;">Document Q&A</div>
              <div style="color:#8b949e; font-size:0.82rem;">
                Upload PDF, DOCX, CSV, TXT and more.
                Summarise, extract data, ask specific questions.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="text-align:center; margin-top:1.2rem; color:#484f58; font-size:0.78rem;">
            Powered by <strong style="color:#58a6ff;">Amazon Nova Pro</strong> on
            <strong style="color:#ff9900;">AWS Bedrock</strong> &nbsp;|&nbsp;
            300K token context &nbsp;|&nbsp; Streaming responses
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Suggested prompts
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#8b949e; font-size:0.85rem; text-align:center;">Try one of these:</p>',
        unsafe_allow_html=True,
    )

    suggestions = [
        "What is Amazon Bedrock and how does it work?",
        "Explain the difference between RAG and fine-tuning.",
        "What AWS services would you use for a serverless AI app?",
    ]

    cols = st.columns(len(suggestions))
    for col, suggestion in zip(cols, suggestions):
        with col:
            if st.button(suggestion, use_container_width=True):
                _handle_user_input(suggestion)
                st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 9 — Main app entry point
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Main Streamlit application entry point."""

    # Inject CSS first (before any other rendering)
    _inject_css()

    # Initialise session state
    _init_session_state()

    # Render sidebar (settings + file upload + controls)
    _render_sidebar()

    # ── Hero header ───────────────────────────────────────────────────────────
    bot_name = st.session_state.bot_name
    pending_img = st.session_state.pending_image
    pending_doc = st.session_state.pending_document

    # Build header sub-line based on what's attached
    if pending_img:
        sub = (
            f"🖼️ <span style='color:#3fb950;'>Image attached:</span> "
            f"{pending_img.file_name} — type your question below."
        )
    elif pending_doc:
        sub = (
            f"📄 <span style='color:#d29922;'>Document attached:</span> "
            f"{pending_doc.file_name} — type your question below."
        )
    else:
        sub = "Your smart assistant for text, images, and documents. Powered by AWS Bedrock."

    st.markdown(
        f"""
        <div class="nm-hero">
            <h1>🤖 {bot_name} AI</h1>
            <p>{sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Chat history ──────────────────────────────────────────────────────────
    if st.session_state.chat_history:
        _render_chat_history()
    else:
        _render_welcome()

    # ── Chat input ────────────────────────────────────────────────────────────
    # Contextual placeholder text
    if pending_img:
        placeholder = f"Ask {bot_name} about the attached image..."
    elif pending_doc:
        placeholder = f"Ask {bot_name} about the attached document..."
    else:
        placeholder = f"Ask {bot_name} anything..."

    user_input = st.chat_input(placeholder)

    if user_input:
        _handle_user_input(user_input)
        st.rerun()


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
