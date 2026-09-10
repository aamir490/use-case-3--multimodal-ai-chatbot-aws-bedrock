"""
mod_chatbot_frontend.py
────────────────────────
NovaMind AI — Production-grade multimodal chatbot powered by Amazon Bedrock.

Features:
  • Login page (demo authentication)
  • Model selector  — Nova Pro / Nova Lite / Claude 3.5 Sonnet
  • Token & cost counter — live running total per session
  • Prompt templates — 5 pre-built personas
  • Conversation summary button
  • AWS / Bedrock connection health check
  • Response language selector — 8 languages
  • Text, image, and document (PDF) multimodal support
  • Streaming responses (token-by-token)
  • Conversation export as plain text

Run:
    streamlit run mod_chatbot_frontend.py
"""

import sys
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Service imports ───────────────────────────────────────────────────────────
from services.bedrock_service import get_bedrock_service, BedrockService
from services.document_service import DocumentResult, DocumentValidationError
from services.image_service import ImageResult, ImageValidationError
from utils.validators import (
    validate_file_upload,
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
# CONSTANTS
# ═════════════════════════════════════════════════════════════════════════════

# ── Demo login credentials (portfolio/demo auth — not production) ─────────────
# In a real product this would be Amazon Cognito.
DEMO_USERS: dict[str, str] = {
    "admin":  "novabot123",
    "aamir":  "bedrock2026",
    "demo":   "demo1234",
}

# ── Bedrock model options ─────────────────────────────────────────────────────
MODEL_OPTIONS: dict[str, str] = {
    "Amazon Nova Pro  (Recommended)":    "amazon.nova-pro-v1:0",
    "Amazon Nova Lite (Fast & Cheap)":   "amazon.nova-lite-v1:0",
    "Claude 3.5 Sonnet (High Accuracy)": "anthropic.claude-3-5-sonnet-20241022-v2:0",
}

# ── Token pricing per model (USD per 1 000 tokens) ───────────────────────────
MODEL_PRICING: dict[str, dict[str, float]] = {
    "amazon.nova-pro-v1:0":                          {"input": 0.0008,  "output": 0.0032},
    "amazon.nova-lite-v1:0":                         {"input": 0.00006, "output": 0.00024},
    "anthropic.claude-3-5-sonnet-20241022-v2:0":     {"input": 0.003,   "output": 0.015},
}

# ── Prompt templates ──────────────────────────────────────────────────────────
PROMPT_TEMPLATES: dict[str, str] = {
    "🤖 Default Assistant": (
        "You are NovaMind, an intelligent multimodal AI assistant powered by "
        "Amazon Nova Pro on AWS Bedrock. You can understand and discuss text, "
        "images, and documents. Be helpful, accurate, and professional."
    ),
    "🧑‍💻 Code Reviewer": (
        "You are an expert software engineer and code reviewer. Analyse code "
        "for bugs, security issues, performance problems, and style. Suggest "
        "clear improvements with examples. Be precise and technical."
    ),
    "📊 Data Analyst": (
        "You are a senior data analyst. Help interpret data, explain charts, "
        "analyse spreadsheets, and provide statistical insights. Use clear "
        "language and back every claim with reasoning."
    ),
    "📝 Document Summariser": (
        "You are an expert at summarising documents. Extract key points, "
        "decisions, and action items. Format output with bullet points. "
        "Be concise — every word must add value."
    ),
    "🎓 AWS Educator": (
        "You are a certified AWS solutions architect and educator. Explain "
        "AWS services, architectures, and best practices clearly. Use "
        "real-world examples. Cover costs, security, and trade-offs."
    ),
}

# ── Language options ──────────────────────────────────────────────────────────
LANGUAGE_OPTIONS: dict[str, str] = {
    "English":  "Respond in English.",
    "Arabic":   "أجب باللغة العربية.",
    "French":   "Réponds en français.",
    "Spanish":  "Responde en español.",
    "German":   "Antworte auf Deutsch.",
    "Hindi":    "हिंदी में उत्तर दें।",
    "Japanese": "日本語で答えてください。",
    "Chinese":  "请用中文回答。",
}

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CSS / Styling
# ═════════════════════════════════════════════════════════════════════════════

def _load_logo_bytes() -> bytes | None:
    """
    Load logo as bytes. Tries multiple path strategies so it works on both
    Windows (local dev) and Linux (EC2), regardless of working directory.
    """
    candidates = [
        ROOT / "novamind_ai_logo.jpg",                          # relative to script
        Path(__file__).resolve().parent / "novamind_ai_logo.jpg",  # absolute from script
        Path.cwd() / "novamind_ai_logo.jpg",                    # cwd fallback
    ]
    for p in candidates:
        if p.exists():
            try:
                return p.read_bytes()
            except Exception:
                continue
    return None


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* ── Base ── */
        .stApp { background: #0d1117; color: #e6edf3; }
        .block-container { padding-top: 0.5rem; padding-bottom: 1rem; max-width: 1200px; }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
            border-right: 1px solid #21262d;
        }
        section[data-testid="stSidebar"] * { color: #e6edf3 !important; }
        section[data-testid="stSidebar"] .stMarkdown p { color: #c9d1d9 !important; }

        /* ── Hero header ── */
        .nm-hero {
            background: linear-gradient(135deg, #0d1b2a 0%, #1f3a5f 40%, #1f6feb 100%);
            border: 1px solid #1f6feb;
            border-radius: 16px; padding: 1.2rem 1.8rem; margin-bottom: 1.2rem;
            color: white;
            box-shadow: 0 4px 32px rgba(31,111,235,0.3), 0 0 0 1px rgba(88,166,255,0.15);
        }
        .nm-hero h1 { margin: 0 0 0.25rem 0; font-size: 1.7rem; font-weight: 800;
                      letter-spacing: -0.3px; }
        .nm-hero p  { margin: 0; opacity: 0.85; font-size: 0.9rem; }

        /* ── Token counter card ── */
        .nm-token-card {
            background: #0d1117; border: 1px solid #21262d;
            border-radius: 10px; padding: 0.65rem 1rem;
            font-size: 0.8rem; color: #8b949e; margin-top: 0.4rem;
            line-height: 1.7;
        }
        .nm-token-card .val  { color: #3fb950; font-weight: 700; }
        .nm-token-card .cost { color: #d29922; font-weight: 700; }

        /* ── Status ── */
        .nm-status-ok  { color: #3fb950; font-weight: 600; font-size: 0.84rem; }
        .nm-status-err { color: #f85149; font-weight: 600; font-size: 0.84rem; }

        /* ── Chat messages ── */
        div[data-testid="stChatMessage"] {
            padding: 0.4rem 0;
            border-radius: 12px;
        }

        /* ── Attachment pills ── */
        .nm-attachment {
            display: inline-flex; align-items: center; gap: 6px;
            background: #161b22; border: 1px solid #30363d;
            border-radius: 20px; padding: 4px 14px;
            font-size: 0.79rem; color: #8b949e; margin-bottom: 8px;
        }
        .nm-badge-image    { color: #3fb950; font-weight: 700; }
        .nm-badge-document { color: #d29922; font-weight: 700; }

        /* ── Model info card ── */
        .nm-model-card {
            background: #0d1117; border: 1px solid #21262d;
            border-radius: 10px; padding: 0.7rem 1rem;
            font-size: 0.78rem; color: #6e7681; margin-top: 0.5rem;
            line-height: 1.8;
        }
        .nm-model-card strong { color: #58a6ff; }

        /* ── Upload info ── */
        .nm-upload-info {
            background: #0d1117; border: 1px dashed #30363d;
            border-radius: 10px; padding: 0.6rem 0.9rem;
            font-size: 0.81rem; color: #8b949e; line-height: 1.6;
        }

        /* ── Document preview ── */
        .nm-preview {
            background: #0d1117; border: 1px solid #21262d;
            border-radius: 8px; padding: 0.7rem 0.9rem;
            max-height: 180px; overflow-y: auto;
            font-size: 0.77rem; color: #8b949e;
            white-space: pre-wrap; word-break: break-word;
        }

        /* ── Welcome feature cards ── */
        .nm-feat-card {
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 14px;
            padding: 1.2rem 1rem;
            text-align: center;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
            height: 100%;
        }
        .nm-feat-card:hover {
            border-color: #388bfd;
            box-shadow: 0 4px 20px rgba(31,111,235,0.2);
        }
        .nm-feat-icon  { font-size: 2.2rem; margin-bottom: 0.5rem; }
        .nm-feat-title { font-weight: 700; margin-bottom: 0.3rem; font-size: 0.95rem; }
        .nm-feat-desc  { color: #8b949e; font-size: 0.81rem; line-height: 1.5; }

        /* ── Buttons ── */
        .stButton > button {
            background: #161b22 !important;
            border: 1px solid #30363d !important;
            color: #e6edf3 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.15s ease !important;
        }
        .stButton > button:hover {
            background: #21262d !important;
            border-color: #58a6ff !important;
            color: #58a6ff !important;
        }

        /* ── Divider ── */
        hr { border-color: #21262d !important; margin: 0.6rem 0 !important; }

        /* ── Inputs ── */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: #0d1117 !important;
            border: 1px solid #30363d !important;
            color: #e6edf3 !important;
            border-radius: 8px !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #58a6ff !important;
            box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
        }

        /* ── Selectbox ── */
        .stSelectbox > div > div {
            background: #0d1117 !important;
            border: 1px solid #30363d !important;
            color: #e6edf3 !important;
            border-radius: 8px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Login / Authentication
# ═════════════════════════════════════════════════════════════════════════════

def _render_login_page() -> None:
    """Render the login page. Sets session_state.logged_in on success."""
    _inject_css()

    # ── Login-page-only CSS ───────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Full-page dark gradient background for login */
    .stApp {
        background: radial-gradient(ellipse at 20% 50%, #0d1b2a 0%, #0d1117 60%) !important;
    }
    /* Glow animation for logo */
    @keyframes logoGlow {
        0%   { box-shadow: 0 0 16px 4px rgba(31,111,235,0.35); }
        50%  { box-shadow: 0 0 32px 10px rgba(88,166,255,0.55); }
        100% { box-shadow: 0 0 16px 4px rgba(31,111,235,0.35); }
    }
    .nm-logo-wrap {
        border-radius: 20px;
        overflow: hidden;
        animation: logoGlow 3s ease-in-out infinite;
        margin-bottom: 1.2rem;
    }
    .nm-logo-wrap img { width: 100%; border-radius: 20px; display: block; }
    /* Info card */
    .nm-info-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 16px;
        padding: 1.8rem 1.6rem;
    }
    .nm-info-title {
        font-size: 1.6rem; font-weight: 800; color: #58a6ff;
        margin-bottom: 0.15rem; letter-spacing: -0.3px;
    }
    .nm-info-sub {
        font-size: 0.84rem; color: #8b949e; margin-bottom: 1.3rem;
    }
    .nm-feat-row {
        display: flex; align-items: flex-start; gap: 10px; margin-bottom: 0.8rem;
    }
    .nm-feat-icon { font-size: 1.25rem; min-width: 26px; }
    .nm-feat-body { color: #c9d1d9; font-size: 0.85rem; line-height: 1.45; }
    .nm-feat-body strong { color: #79c0ff; }
    .nm-pill {
        display: inline-block;
        background: #0d1117; border: 1px solid #30363d;
        border-radius: 20px; padding: 2px 10px;
        font-size: 0.73rem; color: #8b949e; margin: 2px 2px;
    }
    .nm-built {
        margin-top: 1.1rem; padding-top: 0.9rem;
        border-top: 1px solid #21262d;
        text-align: center;
    }
    /* Login form card */
    .nm-form-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 16px;
        padding: 2rem 1.8rem 1.4rem 1.8rem;
        box-shadow: 0 8px 40px rgba(0,0,0,0.5),
                    0 0 0 1px rgba(88,166,255,0.08);
    }
    .nm-form-title {
        text-align: center; font-size: 1.4rem; font-weight: 800;
        color: #e6edf3; margin-bottom: 0.2rem;
    }
    .nm-form-sub {
        text-align: center; color: #8b949e;
        font-size: 0.82rem; margin-bottom: 1.5rem;
    }
    .nm-cred-box {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-top: 0.5rem;
    }
    .nm-cred-row {
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 0.35rem;
    }
    .nm-cred-label { color: #8b949e; font-size: 0.78rem; }
    .nm-cred-val {
        font-family: monospace; font-size: 0.84rem; font-weight: 700;
        color: #a5d6ff; letter-spacing: 0.3px;
    }
    .nm-warning {
        color: #d29922; font-size: 0.77rem; font-weight: 600;
        text-align: center; margin-top: 0.6rem; line-height: 1.5;
    }
    .nm-cognito-note {
        color: #6e7681; font-size: 0.72rem; text-align: center;
        margin-top: 0.3rem;
    }
    </style>
    """, unsafe_allow_html=True)

    logo_bytes = _load_logo_bytes()

    st.markdown("<div style='padding-top:1.8rem;'></div>", unsafe_allow_html=True)

    left_col, gap, right_col = st.columns([1.25, 0.1, 0.85])

    # ══════════════════════════════════════════
    # LEFT — Logo + App Info
    # ══════════════════════════════════════════
    with left_col:
        # Logo with glow effect
        if logo_bytes:
            import base64
            b64 = base64.b64encode(logo_bytes).decode()
            st.markdown(
                f'<div class="nm-logo-wrap">'
                f'<img src="data:image/jpeg;base64,{b64}" alt="NovaMind AI Logo"/>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="text-align:center;font-size:5rem;margin-bottom:1rem;'
                'filter:drop-shadow(0 0 20px #1f6feb);">🤖</div>',
                unsafe_allow_html=True,
            )

        # App info card
        st.markdown("""
        <div class="nm-info-card">
          <div class="nm-info-title">NovaMind AI</div>
          <div class="nm-info-sub">Production-grade Multimodal AI Chatbot · AWS Bedrock</div>

          <div class="nm-feat-row">
            <div class="nm-feat-icon">💬</div>
            <div class="nm-feat-body">
              <strong>Text Chat</strong> — Multi-turn conversations with streaming
              responses and full context memory.
            </div>
          </div>
          <div class="nm-feat-row">
            <div class="nm-feat-icon">🖼️</div>
            <div class="nm-feat-body">
              <strong>Image Analysis</strong> — Upload JPEG, PNG, GIF or WebP.
              Ask questions, extract text, describe scenes.
            </div>
          </div>
          <div class="nm-feat-row">
            <div class="nm-feat-icon">📄</div>
            <div class="nm-feat-body">
              <strong>Document Q&amp;A</strong> — Upload PDF, DOCX, CSV, TXT and more.
              Summarise, extract data, ask specific questions.
            </div>
          </div>
          <div class="nm-feat-row">
            <div class="nm-feat-icon">🧠</div>
            <div class="nm-feat-body">
              <strong>3 AI Models</strong> — Nova Pro, Nova Lite, Claude 3.5 Sonnet.
              Switch mid-conversation.
            </div>
          </div>
          <div class="nm-feat-row">
            <div class="nm-feat-icon">🌐</div>
            <div class="nm-feat-body">
              <strong>8 Languages</strong> — English, Arabic, French, Spanish,
              German, Hindi, Japanese, Chinese.
            </div>
          </div>
          <div class="nm-feat-row">
            <div class="nm-feat-icon">📊</div>
            <div class="nm-feat-body">
              <strong>Token &amp; Cost Tracker</strong> — Live session usage with
              estimated USD cost per model.
            </div>
          </div>

          <div style="margin-top:1rem;">
            <span class="nm-pill">Amazon Bedrock</span>
            <span class="nm-pill">Amazon Nova Pro</span>
            <span class="nm-pill">Python 3.14</span>
            <span class="nm-pill">Streamlit</span>
            <span class="nm-pill">boto3</span>
            <span class="nm-pill">AWS IAM</span>
            <span class="nm-pill">Pillow</span>
            <span class="nm-pill">pypdf</span>
          </div>

          <div class="nm-built">
            <div style="font-size:0.88rem; font-weight:700; color:#c9d1d9;">
              👨‍💻 Built by <span style="color:#58a6ff;">Aamir</span>
              &nbsp;·&nbsp; AWS Generative AI Engineer
            </div>
            <div style="font-size:0.75rem; color:#6e7681; margin-top:0.25rem;">
              github.com/aamir490
              &nbsp;·&nbsp;
              use-case-3--multimodal-ai-chatbot-aws-bedrock
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # RIGHT — Login Form
    # ══════════════════════════════════════════
    with right_col:
        st.markdown("""
        <div class="nm-form-card">
          <div class="nm-form-title">🔐 Sign In</div>
          <div class="nm-form-sub">Enter your credentials to continue</div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input(
            "Username",
            placeholder="Enter username",
            key="login_username_input",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password",
            key="login_password_input",
        )

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

        if st.button("🔐  Sign In", use_container_width=True, type="primary"):
            if username.strip() == "" or password.strip() == "":
                st.error("Please enter both username and password.")
            elif username in DEMO_USERS and DEMO_USERS[username] == password:
                st.session_state.logged_in  = True
                st.session_state.login_user = username
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

        # ── Credentials box ────────────────────────────────────────────────
        st.markdown("""
        <div class="nm-cred-box">
          <div style="font-size:0.8rem; font-weight:700; color:#8b949e;
                      margin-bottom:0.5rem; letter-spacing:0.5px;">
            🔑 DEMO CREDENTIALS
          </div>
          <div class="nm-cred-row">
            <span class="nm-cred-label">Username</span>
            <span class="nm-cred-val">demo</span>
          </div>
          <div class="nm-cred-row" style="margin-bottom:0.6rem;">
            <span class="nm-cred-label">Password</span>
            <span class="nm-cred-val">demo1234</span>
          </div>
          <div class="nm-cred-row">
            <span class="nm-cred-label">Username</span>
            <span class="nm-cred-val">aamir</span>
          </div>
          <div class="nm-cred-row" style="margin-bottom:0;">
            <span class="nm-cred-label">Password</span>
            <span class="nm-cred-val">bedrock2026</span>
          </div>
        </div>
        <div class="nm-warning">
          ⚠️ Portfolio demo auth only.<br>
          Production deployment uses Amazon Cognito.
        </div>
        <div class="nm-cognito-note">
          This project was built for interview &amp; portfolio demonstration.
        </div>
        """, unsafe_allow_html=True)


def _check_login() -> bool:
    """Return True if the user is logged in, otherwise render login and return False."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in  = False
        st.session_state.login_user = ""
    return st.session_state.logged_in


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Session state initialisation
# ═════════════════════════════════════════════════════════════════════════════

def _init_session_state() -> None:
    """Initialise all session state keys with safe defaults."""
    if "bedrock_history"      not in st.session_state: st.session_state.bedrock_history      = []
    if "chat_history"         not in st.session_state: st.session_state.chat_history         = []
    if "bedrock_service"      not in st.session_state: st.session_state.bedrock_service      = None
    if "pending_image"        not in st.session_state: st.session_state.pending_image        = None
    if "pending_document"     not in st.session_state: st.session_state.pending_document     = None
    if "conversation_count"   not in st.session_state: st.session_state.conversation_count   = 0

    # Model / inference settings
    if "selected_model_label" not in st.session_state:
        st.session_state.selected_model_label = "Amazon Nova Pro  (Recommended)"
    if "temperature"          not in st.session_state: st.session_state.temperature   = 0.7
    if "max_tokens"           not in st.session_state: st.session_state.max_tokens    = 2048
    if "selected_template"    not in st.session_state:
        st.session_state.selected_template = "🤖 Default Assistant"
    if "system_prompt"        not in st.session_state:
        st.session_state.system_prompt = PROMPT_TEMPLATES["🤖 Default Assistant"]
    if "selected_language"    not in st.session_state:
        st.session_state.selected_language = "English"

    # Token / cost tracking
    if "total_input_tokens"   not in st.session_state: st.session_state.total_input_tokens  = 0
    if "total_output_tokens"  not in st.session_state: st.session_state.total_output_tokens = 0

    # UI
    if "bot_name"             not in st.session_state: st.session_state.bot_name = "NovaMind"
    if "aws_status"           not in st.session_state: st.session_state.aws_status = None


def _get_or_create_service() -> BedrockService:
    """Return the cached BedrockService, recreating if model changed."""
    model_id = MODEL_OPTIONS[st.session_state.selected_model_label]

    # Recreate if model changed or not yet created
    if st.session_state.bedrock_service is None or \
       st.session_state.bedrock_service.model_id != model_id:
        lang_instruction = LANGUAGE_OPTIONS.get(st.session_state.selected_language, "")
        full_prompt = st.session_state.system_prompt
        if lang_instruction:
            full_prompt += f"\n\n{lang_instruction}"
        st.session_state.bedrock_service = get_bedrock_service(
            model_id=model_id,
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            system_prompt=full_prompt,
        )
    return st.session_state.bedrock_service


def _update_service_settings() -> None:
    """Push current sidebar settings into the existing BedrockService."""
    svc = st.session_state.bedrock_service
    if svc:
        lang_instruction = LANGUAGE_OPTIONS.get(st.session_state.selected_language, "")
        full_prompt = st.session_state.system_prompt
        if lang_instruction:
            full_prompt += f"\n\n{lang_instruction}"
        svc.update_settings(
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            system_prompt=full_prompt,
        )


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Token & Cost helpers
# ═════════════════════════════════════════════════════════════════════════════

def _add_tokens(input_tokens: int, output_tokens: int) -> None:
    """Accumulate token counts into session totals."""
    st.session_state.total_input_tokens  += input_tokens
    st.session_state.total_output_tokens += output_tokens


def _calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for a given token count and model."""
    pricing = MODEL_PRICING.get(model_id, {"input": 0.0008, "output": 0.0032})
    return (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])


def _session_cost() -> float:
    """Return total estimated session cost in USD."""
    model_id = MODEL_OPTIONS.get(st.session_state.selected_model_label, "amazon.nova-pro-v1:0")
    return _calculate_cost(
        model_id,
        st.session_state.total_input_tokens,
        st.session_state.total_output_tokens,
    )


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — AWS Connection Check
# ═════════════════════════════════════════════════════════════════════════════

def _check_aws_connection() -> dict:
    """
    Ping Bedrock with a minimal inference call.
    Returns {"ok": bool, "model": str, "region": str, "latency_ms": int, "error": str}
    """
    import time
    try:
        import boto3
        import botocore.exceptions

        region   = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        model_id = MODEL_OPTIONS[st.session_state.selected_model_label]
        client   = boto3.client("bedrock-runtime", region_name=region)

        start = time.time()
        resp  = client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": "ping"}]}],
            inferenceConfig={"maxTokens": 5, "temperature": 0.0},
        )
        latency_ms = int((time.time() - start) * 1000)

        return {
            "ok":         True,
            "model":      model_id,
            "region":     region,
            "latency_ms": latency_ms,
            "error":      "",
        }
    except Exception as exc:
        return {
            "ok":         False,
            "model":      "",
            "region":     os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            "latency_ms": 0,
            "error":      str(exc)[:120],
        }


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Sidebar
# ═════════════════════════════════════════════════════════════════════════════

def _render_sidebar() -> None:
    with st.sidebar:

        # ── Logo + title ──────────────────────────────────────────────────────
        logo_bytes = _load_logo_bytes()
        if logo_bytes:
            st.image(logo_bytes, use_container_width=True)
        else:
            st.markdown(
                '<div style="text-align:center;font-size:3rem;margin-bottom:0.4rem;'
                'filter:drop-shadow(0 0 12px #1f6feb);">🤖</div>',
                unsafe_allow_html=True,
            )

        st.markdown("## 🤖 NovaMind AI")
        st.markdown("*Multimodal assistant — Amazon Bedrock*")
        st.markdown(
            '<div style="margin-top:4px; margin-bottom:2px; padding:6px 0 4px 0;'
            'border-top:1px solid #21262d; border-bottom:1px solid #21262d;">'
            '<span style="font-size:0.82rem; font-weight:700; color:#c9d1d9;">'
            '👨‍💻 Built by <span style="color:#58a6ff;">Aamir</span>'
            ' &nbsp;·&nbsp; AWS Generative AI Engineer</span><br>'
            f'<span style="font-size:0.72rem; color:#6e7681;">'
            f'👤 Signed in as <strong style="color:#58a6ff;">{st.session_state.login_user}</strong>'
            f'</span></div>',
            unsafe_allow_html=True,
        )

        # ── Sign out ──────────────────────────────────────────────────────────
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()

        # ── Model selector ────────────────────────────────────────────────────
        st.markdown("### 🧠 AI Model")
        prev_model = st.session_state.selected_model_label
        selected_model = st.selectbox(
            "Select model",
            options=list(MODEL_OPTIONS.keys()),
            index=list(MODEL_OPTIONS.keys()).index(st.session_state.selected_model_label),
            label_visibility="collapsed",
        )
        if selected_model != prev_model:
            st.session_state.selected_model_label = selected_model
            st.session_state.bedrock_service = None   # force recreate with new model

        # Show model pricing hint
        mid = MODEL_OPTIONS[selected_model]
        p   = MODEL_PRICING.get(mid, {})
        st.markdown(
            f'<div style="font-size:0.75rem; color:#484f58; margin-top:-4px;">'
            f'💰 ${p.get("input",0):.4f} / 1K in &nbsp;·&nbsp; ${p.get("output",0):.4f} / 1K out'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        # ── Prompt templates ──────────────────────────────────────────────────
        st.markdown("### 📋 Persona / Template")
        prev_template = st.session_state.selected_template
        selected_template = st.selectbox(
            "Choose a prompt template",
            options=list(PROMPT_TEMPLATES.keys()),
            index=list(PROMPT_TEMPLATES.keys()).index(st.session_state.selected_template),
            label_visibility="collapsed",
        )
        if selected_template != prev_template:
            st.session_state.selected_template = selected_template
            st.session_state.system_prompt     = PROMPT_TEMPLATES[selected_template]
            _update_service_settings()

        # Custom system prompt override
        with st.expander("✏️ Edit system prompt", expanded=False):
            custom_prompt = st.text_area(
                "System prompt",
                value=st.session_state.system_prompt,
                height=110,
                label_visibility="collapsed",
            )
            if st.button("Apply", use_container_width=True):
                st.session_state.system_prompt = custom_prompt
                _update_service_settings()
                st.success("Updated.")

        st.divider()

        # ── Language selector ─────────────────────────────────────────────────
        st.markdown("### 🌐 Response Language")
        prev_lang = st.session_state.selected_language
        selected_language = st.selectbox(
            "Language",
            options=list(LANGUAGE_OPTIONS.keys()),
            index=list(LANGUAGE_OPTIONS.keys()).index(st.session_state.selected_language),
            label_visibility="collapsed",
        )
        if selected_language != prev_lang:
            st.session_state.selected_language = selected_language
            _update_service_settings()

        st.divider()

        # ── Inference settings ────────────────────────────────────────────────
        st.markdown("### ⚙️ Settings")
        temperature = st.slider(
            "Temperature",
            min_value=0.0, max_value=1.0,
            value=st.session_state.temperature,
            step=0.05,
        )
        max_tokens = st.select_slider(
            "Max response tokens",
            options=[256, 512, 1024, 2048, 4096, 8192],
            value=st.session_state.max_tokens,
        )
        if temperature != st.session_state.temperature or max_tokens != st.session_state.max_tokens:
            st.session_state.temperature = temperature
            st.session_state.max_tokens  = max_tokens
            _update_service_settings()

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
            "Upload",
            type=["jpg","jpeg","png","gif","webp","pdf","txt","md","csv",
                  "doc","docx","xls","xlsx","html","htm"],
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            _handle_file_upload(uploaded_file)
        _render_pending_attachment()

        st.divider()

        # ── Conversation actions ──────────────────────────────────────────────
        st.markdown("### 💬 Conversation")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear", use_container_width=True):
                _clear_conversation()
                st.rerun()
        with col2:
            if st.button("🔄 New", use_container_width=True):
                _clear_conversation()
                st.session_state.conversation_count += 1
                st.rerun()

        # Summary button
        if st.session_state.chat_history:
            if st.button("📝 Summarise conversation", use_container_width=True):
                st.session_state._trigger_summary = True

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

        msg_count = len(st.session_state.chat_history)
        if msg_count:
            turns = msg_count // 2
            st.caption(f"💬 {msg_count} messages · {turns} turn{'s' if turns != 1 else ''}")

        st.divider()

        # ── Token & cost counter ──────────────────────────────────────────────
        st.markdown("### 📊 Token Usage")
        total_cost = _session_cost()
        st.markdown(
            f'<div class="nm-token-card">'
            f'📥 Input &nbsp; <span class="val">{st.session_state.total_input_tokens:,}</span> tokens<br>'
            f'📤 Output &nbsp;<span class="val">{st.session_state.total_output_tokens:,}</span> tokens<br>'
            f'💵 Est. cost &nbsp;<span class="cost">${total_cost:.5f}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        # ── AWS connection check ──────────────────────────────────────────────
        st.markdown("### 🔌 AWS Connection")
        if st.button("🔍 Check AWS / Bedrock", use_container_width=True):
            with st.spinner("Pinging Bedrock..."):
                st.session_state.aws_status = _check_aws_connection()

        if st.session_state.aws_status:
            s = st.session_state.aws_status
            if s["ok"]:
                st.markdown(
                    f'<p class="nm-status-ok">✅ Connected — {s["latency_ms"]} ms</p>'
                    f'<div style="font-size:0.74rem; color:#484f58;">'
                    f'Model: {s["model"]}<br>Region: {s["region"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<p class="nm-status-err">❌ Connection failed</p>'
                    f'<div style="font-size:0.74rem; color:#f85149;">{s["error"]}</div>',
                    unsafe_allow_html=True,
                )

        st.divider()

        # ── Model info card ───────────────────────────────────────────────────
        svc      = st.session_state.bedrock_service
        model_id = MODEL_OPTIONS[st.session_state.selected_model_label]
        region   = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        if svc:
            region = svc.region
        st.markdown(
            f'<div class="nm-model-card">'
            f'<strong>Model</strong> {model_id}<br>'
            f'<strong>Region</strong> {region}<br>'
            f'<strong>Temp</strong> {st.session_state.temperature} &nbsp;'
            f'<strong>MaxTok</strong> {st.session_state.max_tokens}<br>'
            f'<strong>Lang</strong> {st.session_state.selected_language}'
            f'</div>',
            unsafe_allow_html=True,
        )


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7 — File upload handlers
# ═════════════════════════════════════════════════════════════════════════════

def _handle_file_upload(uploaded_file) -> None:
    raw_bytes = uploaded_file.read()
    file_name = sanitize_filename(uploaded_file.name)
    result    = validate_file_upload(raw_bytes, file_name)

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
    img = st.session_state.pending_image
    doc = st.session_state.pending_document

    if img:
        st.markdown(
            f'<div class="nm-attachment">'
            f'🖼️ <span class="nm-badge-image">IMAGE</span> {img.file_name} · {img.size_kb} KB'
            f'</div>',
            unsafe_allow_html=True,
        )
        if img.thumbnail_bytes:
            st.image(img.thumbnail_bytes, caption=img.dimensions, use_container_width=True)
        if st.button("✕ Remove image", use_container_width=True):
            st.session_state.pending_image = None
            st.rerun()

    elif doc:
        st.markdown(
            f'<div class="nm-attachment">'
            f'📄 <span class="nm-badge-document">DOC</span> {doc.file_name} · {doc.size_kb} KB'
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
    st.session_state.bedrock_history      = []
    st.session_state.chat_history         = []
    st.session_state.pending_image        = None
    st.session_state.pending_document     = None
    st.session_state.total_input_tokens   = 0
    st.session_state.total_output_tokens  = 0
    st.session_state.bedrock_service      = None
    st.session_state.aws_status           = None


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Chat history rendering
# ═════════════════════════════════════════════════════════════════════════════

def _render_chat_history() -> None:
    for msg in st.session_state.chat_history:
        role      = msg["role"]
        text      = msg.get("text", "")
        msg_type  = msg.get("type", "text")
        file_name = msg.get("file_name", "")
        avatar    = "🧑" if role == "user" else "🤖"

        with st.chat_message(role, avatar=avatar):
            if msg_type == "image" and file_name:
                st.markdown(
                    f'<div class="nm-attachment">'
                    f'🖼️ <span class="nm-badge-image">IMAGE</span> {file_name}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
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
# SECTION 9 — AI response streaming
# ═════════════════════════════════════════════════════════════════════════════

def _stream_and_display_response(
    user_text:    str,
    service:      BedrockService,
    image_result: ImageResult   | None,
    doc_result:   DocumentResult | None,
) -> str:
    """Stream the AI response and track token usage."""
    full_response = ""

    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()
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
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)

        except Exception as exc:
            error_msg = f"⚠️ An error occurred: {exc}"
            placeholder.error(error_msg)
            full_response = error_msg

    # ── Token tracking — parse from the last bedrock_history assistant turn ──
    # BedrockService appends usage data to history after stream completes.
    # We approximate from the text length (exact counts need response metadata).
    # Rough estimate: 1 token ≈ 4 characters
    approx_in  = max(1, len(user_text) // 4)
    approx_out = max(1, len(full_response) // 4)
    _add_tokens(approx_in, approx_out)

    return full_response


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 10 — Chat input handler
# ═════════════════════════════════════════════════════════════════════════════

def _handle_user_input(user_input: str) -> None:
    service      = _get_or_create_service()
    user_text    = sanitize_user_input(user_input)
    image_result = st.session_state.pending_image
    doc_result   = st.session_state.pending_document

    # Display user message
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

    # Save user turn
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

    # Clear attachments
    st.session_state.pending_image    = None
    st.session_state.pending_document = None

    # Stream AI response
    full_response = _stream_and_display_response(
        user_text=user_text,
        service=service,
        image_result=image_result,
        doc_result=doc_result,
    )

    # Save assistant turn
    st.session_state.chat_history.append({
        "role":      "assistant",
        "text":      full_response,
        "type":      "text",
        "timestamp": datetime.now().strftime("%H:%M"),
        "avatar":    "🤖",
    })


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 11 — Conversation summary
# ═════════════════════════════════════════════════════════════════════════════

def _handle_summary() -> None:
    """Ask the model to summarise the current conversation."""
    if not st.session_state.chat_history:
        return

    service = _get_or_create_service()

    summary_prompt = (
        "Please provide a concise summary of our conversation so far. "
        "Format as:\n"
        "**Main topics discussed:**\n- ...\n\n"
        "**Key points and answers:**\n- ...\n\n"
        "**Action items / follow-ups (if any):**\n- ..."
    )

    with st.chat_message("user", avatar="🧑"):
        st.markdown("📝 *Conversation summary requested*")

    st.session_state.chat_history.append({
        "role":      "user",
        "text":      "📝 *Conversation summary requested*",
        "type":      "text",
        "timestamp": datetime.now().strftime("%H:%M"),
        "avatar":    "🧑",
    })

    # Use a fresh bedrock call (don't mutate main history)
    summary_history = list(st.session_state.bedrock_history)
    full_response   = ""

    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()
        try:
            for chunk in service.stream_response(
                user_text=summary_prompt,
                history=summary_history,
            ):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except Exception as exc:
            full_response = f"⚠️ Summary failed: {exc}"
            placeholder.error(full_response)

    # Also update the main history
    st.session_state.bedrock_history = summary_history

    st.session_state.chat_history.append({
        "role":      "assistant",
        "text":      full_response,
        "type":      "text",
        "timestamp": datetime.now().strftime("%H:%M"),
        "avatar":    "🤖",
    })


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 12 — Welcome / empty state
# ═════════════════════════════════════════════════════════════════════════════

def _render_welcome() -> None:
    st.markdown(
        '<div style="text-align:center;padding:1.8rem 0 1.2rem;color:#8b949e;'
        'font-size:0.96rem;">Ask me anything · upload an image · or attach a document</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    cards = [
        ("💬", "#58a6ff", "Text Chat",
         "Multi-turn conversations with full context memory. "
         "Follow-up questions, reasoning, and explanations."),
        ("🖼️", "#3fb950", "Image Analysis",
         "Upload JPEG, PNG, GIF, or WebP. "
         "Ask questions, extract text, describe scenes."),
        ("📄", "#d29922", "Document Q&A",
         "Upload PDF, DOCX, CSV, TXT and more. "
         "Summarise, extract data, ask specific questions."),
    ]
    for col, (icon, color, title, desc) in zip([col1, col2, col3], cards):
        with col:
            st.markdown(
                f'<div class="nm-feat-card">'
                f'<div class="nm-feat-icon">{icon}</div>'
                f'<div class="nm-feat-title" style="color:{color};">{title}</div>'
                f'<div class="nm-feat-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div style="text-align:center;margin-top:1.4rem;color:#484f58;font-size:0.78rem;">'
        'Powered by <strong style="color:#58a6ff;">Amazon Bedrock</strong> &nbsp;·&nbsp;'
        '300K token context &nbsp;·&nbsp; Streaming responses &nbsp;·&nbsp;'
        '3 AI models &nbsp;·&nbsp; 8 languages'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#6e7681;font-size:0.85rem;text-align:center;margin-bottom:0.5rem;">'
        '✨ Try one of these to get started:</p>',
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
# SECTION 13 — Main entry point
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    _inject_css()

    # ── Auth gate ─────────────────────────────────────────────────────────────
    if not _check_login():
        _render_login_page()
        return

    # ── Init state ────────────────────────────────────────────────────────────
    _init_session_state()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    _render_sidebar()

    # ── Handle summary trigger (set by sidebar button) ────────────────────────
    if st.session_state.get("_trigger_summary"):
        st.session_state._trigger_summary = False
        _handle_summary()
        st.rerun()

    # ── Hero header ───────────────────────────────────────────────────────────
    bot_name    = st.session_state.bot_name
    pending_img = st.session_state.pending_image
    pending_doc = st.session_state.pending_document
    model_label = st.session_state.selected_model_label.split("(")[0].strip()

    if pending_img:
        sub = (f"🖼️ <span style='color:#3fb950;font-weight:600;'>Image attached:</span> "
               f"<span style='color:#c9d1d9;'>{pending_img.file_name}</span> — type your question below.")
    elif pending_doc:
        sub = (f"📄 <span style='color:#d29922;font-weight:600;'>Document attached:</span> "
               f"<span style='color:#c9d1d9;'>{pending_doc.file_name}</span> — type your question below.")
    else:
        sub = (f"<span style='opacity:0.75;'>{model_label}</span>"
               f" &nbsp;·&nbsp; <span style='opacity:0.75;'>{st.session_state.selected_language}</span>"
               f" &nbsp;·&nbsp; <span style='opacity:0.75;'>AWS Bedrock</span>"
               f" &nbsp;·&nbsp; <span style='opacity:0.6;font-size:0.82rem;'>"
               f"👤 {st.session_state.login_user}</span>")

    st.markdown(
        f"""<div class="nm-hero">
            <h1>🤖 {bot_name} AI</h1>
            <p>{sub}</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Chat area ─────────────────────────────────────────────────────────────
    if st.session_state.chat_history:
        _render_chat_history()
    else:
        _render_welcome()

    # ── Chat input ────────────────────────────────────────────────────────────
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
