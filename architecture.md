# Architecture — NovaMind AI Multimodal Chatbot

## 1. Overview

NovaMind AI is a **multimodal conversational AI application** that processes text, images, and documents through a single unified interface. The architecture follows a clean layered design: a Streamlit frontend, a service layer for business logic, and Amazon Bedrock as the AI inference backend.

The application is intentionally **not over-engineered**. Services that add cost or complexity without adding value (Lambda, API Gateway, S3, DynamoDB) are excluded. The AI inference itself is fully serverless via Bedrock.

---

## 2. High-Level Architecture

```
╔════════════════════════════════════════════════════════════════╗
║                    USER (Browser)                              ║
╚══════════════════════════╦═════════════════════════════════════╝
                           ║  HTTP (port 8501)
╔══════════════════════════╩═════════════════════════════════════╗
║               PRESENTATION LAYER                               ║
║          mod_chatbot_frontend.py  (Streamlit)                  ║
║                                                                ║
║  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐ ║
║  │  Sidebar    │  │  Chat area   │  │  Welcome / empty      │ ║
║  │  Settings   │  │  History     │  │  state with prompts   │ ║
║  │  File upload│  │  Streaming   │  │  Capability cards     │ ║
║  │  Controls   │  │  bubbles     │  └───────────────────────┘ ║
║  └─────────────┘  └──────────────┘                            ║
╚══════════════════════════╦═════════════════════════════════════╝
                           ║  Python function calls
╔══════════════════════════╩═════════════════════════════════════╗
║                  SERVICE LAYER                                 ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐  ║
║  │  services/bedrock_service.py  (BedrockService)           │  ║
║  │  · Builds Converse API message payloads                  │  ║
║  │  · Manages conversation history (list of role/content)   │  ║
║  │  · Calls converse_stream() — yields text chunks          │  ║
║  │  · Auto-fallback: model ID → inference profile           │  ║
║  └──────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  ┌─────────────────────────┐  ┌─────────────────────────────┐  ║
║  │ services/image_         │  │ services/document_          │  ║
║  │ service.py              │  │ service.py                  │  ║
║  │ · Extension check       │  │ · Extension check           │  ║
║  │ · Size check (5 MB)     │  │ · Size check (4.5 MB)       │  ║
║  │ · Magic byte check      │  │ · Magic byte check          │  ║
║  │ · EXIF rotation fix     │  │ · PDF integrity check       │  ║
║  │ · RGBA→RGB conversion   │  │ · pypdf text preview        │  ║
║  │ · Thumbnail generation  │  │ · Page count extraction     │  ║
║  └─────────────────────────┘  └─────────────────────────────┘  ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐  ║
║  │  utils/validators.py                                     │  ║
║  │  · validate_file_upload() dispatcher                     │  ║
║  │  · sanitize_filename() — path traversal protection       │  ║
║  │  · sanitize_user_input() — input length guard            │  ║
║  │  · export_conversation_as_text()                         │  ║
║  └──────────────────────────────────────────────────────────┘  ║
╚══════════════════════════╦═════════════════════════════════════╝
                           ║  boto3  converse_stream()
╔══════════════════════════╩═════════════════════════════════════╗
║                    AWS BEDROCK                                 ║
║                                                                ║
║  Model:   amazon.nova-pro-v1:0                                 ║
║  API:     Converse / ConverseStream                            ║
║  Region:  us-east-1                                            ║
║  Fallback: us.amazon.nova-pro-v1:0 (cross-region profile)      ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 3. Layer Details

### 3.1 Presentation Layer — `mod_chatbot_frontend.py`

**Technology:** Streamlit 1.35+

Streamlit reruns the entire script on every user interaction. The frontend manages two separate state objects:

| State key | Type | Purpose |
|---|---|---|
| `bedrock_history` | `list[dict]` | Raw Converse API message history sent to Bedrock |
| `chat_history` | `list[dict]` | Display-only UI history (role, text, attachment metadata) |
| `pending_image` | `ImageResult \| None` | Attached image waiting to be sent |
| `pending_document` | `DocumentResult \| None` | Attached document waiting to be sent |
| `bedrock_service` | `BedrockService \| None` | Cached service instance |

**Why two separate histories?**
The Bedrock history stores raw API content blocks (including binary bytes) — these can be very large and are not suitable for re-rendering in the UI. The chat history stores lightweight display metadata only.

**Streaming:** `st.empty()` is used as a placeholder that is updated on every chunk with a `▌` cursor appended, then replaced with the final text once streaming completes.

---

### 3.2 Service Layer — `services/`

**Design principle:** All services are UI-agnostic. No Streamlit imports. They can be called from a CLI, a test, or a different frontend without modification.

#### `bedrock_service.py` — BedrockService

The core orchestrator. Key methods:

- `stream_response()` — builds content blocks, calls `converse_stream()`, yields text chunks, updates history
- `invoke_response()` — non-streaming wrapper (for testing)
- `_build_content_blocks()` — constructs the Converse API content array:
  ```
  [image_block?, document_block?, text_block]
  ```
  Text always goes last — recommended ordering for Nova multimodal prompts.
- `_resolve_model_id()` — returns current active model ID (switches to inference profile on first AccessDeniedException)

**Credential chain (in order):**
1. `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` environment variables
2. `~/.aws/credentials` default profile
3. EC2 IAM Instance Role (recommended for production)

#### `document_service.py` — DocumentService

Validates and prepares document files. Returns `DocumentResult` (success) or `DocumentValidationError` (failure).

Validation pipeline:
1. Empty file check
2. Size check (≤ 4.5 MB per Bedrock limit)
3. Extension allowlist check
4. Magic byte / content integrity check (PDF: `%PDF` header; OOXML: `PK\x03\x04`)
5. Text preview extraction via `pypdf` (optional)

#### `image_service.py` — ImageService

Validates and prepares image files. Returns `ImageResult` or `ImageValidationError`.

Validation pipeline:
1. Empty file check
2. Size check (≤ 5 MB)
3. Extension allowlist check
4. Magic byte check (JPEG: `\xff\xd8\xff`; PNG: `\x89PNG`; GIF: `GIF89a`; WebP: `RIFF....WEBP`)
5. Pillow processing: EXIF auto-rotation, RGBA→RGB for JPEG, 400×400 thumbnail

---

### 3.3 AWS Bedrock — Converse API

The **Converse API** provides a unified, model-agnostic interface for multi-turn conversations. It handles:

- System prompts
- Multi-turn message history
- Multimodal content blocks (text, image, document)
- Streaming via `ConverseStream`

**Content block structure for a multimodal request:**
```python
{
  "role": "user",
  "content": [
    {
      "image": {
        "format": "jpeg",
        "source": {"bytes": <raw_image_bytes>}
      }
    },
    {
      "document": {
        "format": "pdf",
        "name": "my_document",
        "source": {"bytes": <raw_pdf_bytes>}
      }
    },
    {
      "text": "What does this document say about the items in the image?"
    }
  ]
}
```

**Why direct bytes instead of S3 URIs?**
For files under 4.5 MB (documents) / 5 MB (images), sending raw bytes is simpler, cheaper, and requires no S3 bucket setup. S3 URI references are only beneficial for very large files or when files need to be reused across many requests.

---

## 4. Data Flows

### 4.1 Text-Only Conversation

```
User types message
       ↓
st.chat_input() captures text
       ↓
sanitize_user_input()
       ↓
BedrockService.stream_response(user_text, history)
       ↓
_build_content_blocks() → [{"text": "..."}]
       ↓
bedrock_runtime.converse_stream(modelId, messages, system, inferenceConfig)
       ↓
Stream events → yield text chunks → st.empty().markdown(chunk + "▌")
       ↓
Final render → history updated → session state saved
```

### 4.2 Image Analysis

```
User uploads image (sidebar file_uploader)
       ↓
ImageService.process(bytes, filename)
  → extension check → size check → magic bytes → Pillow processing
       ↓
ImageResult stored in st.session_state.pending_image
Thumbnail displayed in sidebar
       ↓
User types question → submit
       ↓
BedrockService.stream_response(
    user_text,
    history,
    image_bytes=result.raw_bytes,
    image_format=result.img_format
)
       ↓
_build_content_blocks() → [image_block, text_block]
       ↓
converse_stream() → streaming response
       ↓
pending_image cleared → history updated
```

### 4.3 Document Q&A

```
User uploads PDF/DOCX/etc (sidebar file_uploader)
       ↓
DocumentService.process(bytes, filename)
  → extension check → size check → magic bytes → pypdf preview
       ↓
DocumentResult stored in st.session_state.pending_document
Preview text shown in sidebar expander
       ↓
User types question → submit
       ↓
BedrockService.stream_response(
    user_text,
    history,
    doc_bytes=result.raw_bytes,
    doc_name=result.display_name,
    doc_format=result.doc_format
)
       ↓
_build_content_blocks() → [document_block, text_block]
       ↓
converse_stream() → streaming response
       ↓
pending_document cleared → history updated
```

---

## 5. Memory and Context Management

Conversation history is stored as a plain Python list in `st.session_state.bedrock_history`. Each turn appends two items:

```python
[
  {"role": "user",      "content": [{"text": "What is AWS?"}]},
  {"role": "assistant", "content": [{"text": "AWS is Amazon Web Services..."}]},
  {"role": "user",      "content": [image_block, {"text": "What is in this image?"}]},
  {"role": "assistant", "content": [{"text": "The image shows..."}]},
]
```

The full history is sent to Bedrock on every request. Nova Pro's 300K token context window supports very long conversations before truncation becomes a concern.

**Session scope:** History lives for the duration of the browser session. Closing the tab or clicking "New" resets it. For persistent history across sessions, DynamoDB would be the appropriate addition (noted as a future improvement).

---

## 6. AWS Services — Decisions

| Service | Decision | Reason |
|---|---|---|
| **Amazon Bedrock** | ✅ Used | Core AI inference — Nova Pro multimodal |
| **AWS IAM** | ✅ Used | Credentials for Bedrock access |
| **Amazon S3** | ❌ Not used | Files sent as bytes directly — no persistence needed |
| **AWS Lambda** | ❌ Not used | Streamlit is long-running — Lambda's execution model is incompatible |
| **API Gateway** | ❌ Not used | Streamlit handles its own HTTP server |
| **DynamoDB** | ❌ Not used | Session-scoped memory is sufficient for demo/portfolio |
| **Cognito** | ❌ Not used | No multi-user auth required for portfolio demo |
| **CloudWatch** | ⚡ Optional | Python logging can be directed to CloudWatch via boto3 handler |

---

## 7. Security Architecture

| Concern | Mitigation |
|---|---|
| Credential exposure | No keys in source code; uses default credential chain |
| Secret in Git | `.env` in `.gitignore`; `.env.example` has placeholders only |
| Malicious file upload | Extension + magic byte validation in service layer |
| Path traversal | `sanitize_filename()` strips path separators, normalises unicode |
| Oversized uploads | Hard limits: 5 MB images, 4.5 MB documents |
| Prompt injection | User input sanitised; model-level safety is Nova Pro's guardrails |
| Broad IAM permissions | Minimum required: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream` |

---

## 8. Scalability Considerations

The current architecture is appropriate for:
- Personal portfolio demonstration
- Single-user or low-concurrency usage
- Interview showcases

For production multi-user scale, the following additions would be needed:
- **Load balancer** in front of multiple EC2 instances (or containerise with ECS)
- **DynamoDB** for persistent, per-user conversation history
- **S3** for large file storage (files > 4.5 MB, or shared across requests)
- **Cognito** for user authentication and session isolation
- **Bedrock Guardrails** for content filtering at scale
- **CloudWatch** metrics and alarms for operational monitoring
