# Interview Guide — NovaMind AI Multimodal Chatbot

> This document is built entirely from the actual source code, architecture, and implementation of this project.
> Every answer reflects what is **actually implemented**. Labels are used throughout:
> - ✅ **Implemented** — exists in the code right now
> - 🔄 **Partially implemented** — foundation exists, not complete
> - 🔮 **Future improvement** — planned, not yet built

---

## 1. Project Elevator Pitch

### 30-Second Explanation

"I built a multimodal AI chatbot called NovaMind, powered by Amazon Nova Pro on AWS Bedrock.
It allows users to have natural conversations via text, upload and analyse images,
and ask questions about PDF and office documents — all through a single streaming chat interface
built with Python and Streamlit. The architecture uses a clean service layer that is completely
separate from the UI, making each component independently testable and maintainable."

---

### 1-Minute Explanation

"NovaMind AI is a multimodal chatbot application I built using Amazon Bedrock as the AI backbone.
The frontend is a Streamlit web app that gives users a ChatGPT-style chat interface with streaming
responses. Under the hood, I structured the project into three layers: a presentation layer in
Streamlit, a service layer in Python that handles all Bedrock API calls and file processing,
and a utilities layer for validation and sanitisation.

The AI model is Amazon Nova Pro, which natively supports text, images, and documents in a single
Converse API call. This means a user can upload a PDF and immediately ask questions about it —
no chunking, no vector store, no RAG pipeline needed for single-document use cases.

The project includes a diagnostic script that verifies AWS credentials, region, model access,
and runs live tests against Bedrock before the app starts. Everything is designed with security
in mind: no hard-coded credentials, file validation at multiple layers, and input sanitisation
before anything reaches the model."

---

### 2-Minute Explanation

"NovaMind AI is a production-oriented multimodal chatbot built on AWS. Let me walk you through
the key components.

The **frontend** is built with Streamlit and provides a dark-themed chat interface that streams
responses token by token — similar to how ChatGPT works. The sidebar lets users configure
the assistant name, temperature, max tokens, and system prompt live during a conversation.
Users can attach images or documents before typing their question.

The **service layer** is where the real work happens. I have three services:
BedrockService manages all Bedrock API communication using boto3's converse_stream() method.
It builds structured content blocks — the Converse API's format for combining text, image,
and document inputs in a single request. ImageService validates and processes uploaded images
using Pillow: it checks magic bytes to prevent spoofed files, fixes EXIF orientation, converts
RGBA to RGB for JPEG compatibility, and generates 400×400 thumbnails for the sidebar preview.
DocumentService validates PDFs and office files, checks the %PDF magic header for integrity,
and uses pypdf to extract a text preview of the first three pages.

The **AI model** is Amazon Nova Pro — model ID amazon.nova-pro-v1:0. I chose it because it
natively supports text, images, and documents in the Bedrock Converse API, has a 300,000
token context window, supports streaming, and costs $0.80 per million input tokens.
The application automatically falls back to the cross-region inference profile
us.amazon.nova-pro-v1:0 if access is denied on the base model ID.

For **security**, no credentials are hard-coded anywhere. The app uses boto3's default
credential chain — environment variables, then the AWS config file, then an IAM role on EC2.
File uploads are validated at three levels: extension allowlist, file size limits, and magic
byte integrity checks. User input is sanitised with a 10,000 character limit, and filenames
are sanitised to prevent path traversal attacks."

---

### 5-Minute Deep Technical Explanation

"Let me walk you through the architecture and key technical decisions in detail.

**Architecture Overview**

The project follows a three-layer architecture. The presentation layer is mod_chatbot_frontend.py,
a Streamlit application. The service layer consists of three Python classes: BedrockService,
ImageService, and DocumentService — all completely UI-agnostic, with no Streamlit imports.
The utility layer in utils/validators.py provides shared helpers for file dispatch, sanitisation,
and conversation export.

**Why this separation matters:** Streamlit reruns the entire script on every user interaction.
If business logic were mixed into the frontend, it would re-execute unnecessarily and be
impossible to test in isolation. By keeping services in a separate layer, I can call them
from a CLI or test suite without a running Streamlit server.

**Session State Architecture**

I maintain two separate state objects in Streamlit's session_state. First, bedrock_history —
a list of raw Converse API message dicts that grows with every conversation turn and is sent
to Bedrock on every request. Second, chat_history — a lightweight display list that stores
role, text, type, timestamp, and attachment metadata for re-rendering the UI.

This separation is important because the Bedrock history contains raw binary bytes
for image and document blocks, which are too large to use for UI display. Keeping them
separate also means I can clear the UI history without affecting the API state if needed.

**Streaming Implementation**

The BedrockService calls boto3's converse_stream() which returns a streaming event iterator.
I iterate over contentBlockDelta events, extract the text delta, yield it as a generator,
and accumulate it into a full_reply string. The frontend uses an st.empty() placeholder
that updates on every chunk with a ▌ cursor appended, then removes the cursor on completion.
This gives a smooth real-time typing effect.

**Converse API Content Blocks**

The Bedrock Converse API organises a user message as a list of content blocks. For a multimodal
request, the structure is: optional image block with format and raw bytes, optional document
block with format, name, and raw bytes, and a text block last. Nova Pro's documentation
recommends placing the text block last in multimodal prompts, which is what the
_build_content_blocks() method enforces.

**File Validation Pipeline**

For images, validation runs in four stages: empty-file check, size check against a 5 MB limit,
extension allowlist check, and magic-byte check. For JPEG that means \xff\xd8\xff, for PNG
\x89PNG\r\n\x1a\n, for WebP a two-part check verifying RIFF at offset 0 and WEBP at offset 8
with a minimum-length guard. After validation, Pillow processes the image: it applies EXIF
auto-rotation to fix orientation from mobile cameras, converts RGBA or palette-mode images
to RGB for JPEG compatibility, and generates a 400×400 thumbnail for the sidebar.

For documents, the validation pipeline checks size against 4.5 MB — the Bedrock Converse API
limit per document block — checks the extension against a supported list, and then checks
content integrity. For PDFs that means verifying the %PDF magic header and a startxref or
%%EOF marker near the end. For DOCX and XLSX it checks for the PK\x03\x04 OOXML magic bytes.
Then pypdf extracts a text preview from the first three pages for display in the sidebar.

**Model Selection Rationale**

I chose Amazon Nova Pro over alternatives for several reasons. It is the AWS-native model,
which strengthens the portfolio narrative for AWS-focused roles. It already had model access
granted in the account from the previous project iteration. It supports the full set of
modalities needed: text, images, and documents natively via the Converse API. Its 300K token
context window is more than sufficient for single-document Q&A and long conversations.
And at $0.80 per million input tokens, it is dramatically cheaper than Claude 3.5 Sonnet
at approximately $3.00 per million, which matters for a demo-heavy portfolio project.

**What is not implemented**

I want to be transparent about what is not yet in the codebase. There is no RAG pipeline —
documents are sent directly as bytes, which works perfectly for files under 4.5 MB but would
not scale to a large document corpus. There is no persistent conversation storage — history
lives in Streamlit session state and resets when the browser tab closes. There is no
authentication — the app is single-user with no login system. There is no CloudWatch monitoring.
These are all noted as future improvements, not weaknesses to hide."

---

## 2. How to Explain the Architecture

### Verbal Architecture Explanation (for whiteboard or verbal interview)

"The architecture has three layers. At the top is the Streamlit frontend running on port 8501.
When a user types a message or uploads a file, the frontend calls into the service layer.
The service layer validates the file, builds a structured Converse API request,
and calls Amazon Bedrock via boto3. Bedrock streams the response back event by event,
and the frontend renders each chunk in real time. There is no Lambda, no API Gateway,
no S3 — Streamlit handles its own HTTP server and the AI inference is fully serverless via Bedrock."

---

### Complete Request Flows

#### Text Request Flow ✅ Implemented

```
1. User types a message in st.chat_input()
2. _handle_user_input(user_input) is called
3. sanitize_user_input() strips whitespace, enforces 10K char limit
4. _get_or_create_service() returns the cached BedrockService instance
5. BedrockService._build_content_blocks() → [{"text": "user message"}]
6. messages_for_api = bedrock_history + [{"role":"user","content":blocks}]
7. boto3 bedrock-runtime.converse_stream(modelId, messages, system, inferenceConfig)
8. Stream events arrive → contentBlockDelta.delta.text yielded
9. st.empty().markdown(chunk + "▌") — typing cursor updates live
10. Full response assembled → placeholder.markdown(full_response)
11. bedrock_history updated: +user turn +assistant turn
12. chat_history updated for UI display
```

#### Image Request Flow ✅ Implemented

```
1. User uploads image via st.file_uploader() in sidebar
2. _handle_file_upload() reads raw bytes, sanitizes filename
3. validate_file_upload() routes to ImageService.process()
4. ImageService: empty check → size check (≤5MB) → extension check
   → magic byte check (e.g. \xff\xd8\xff for JPEG)
   → Pillow: EXIF rotation → RGBA→RGB conversion → 400×400 thumbnail
5. ImageResult stored in st.session_state.pending_image
6. Thumbnail displayed in sidebar
7. User types question and submits
8. image_result captured from session state, pending_image cleared
9. BedrockService._build_content_blocks():
   → [{"image":{"format":"jpeg","source":{"bytes":raw_bytes}}}, {"text":"question"}]
10. converse_stream() called with image + text blocks
11. Nova Pro analyses the image and streams a response
12. Image thumbnail re-rendered in chat history as attachment pill
```

#### Document / PDF Request Flow ✅ Implemented

```
1. User uploads PDF via st.file_uploader() in sidebar
2. _handle_file_upload() reads raw bytes, sanitizes filename
3. validate_file_upload() routes to DocumentService.process()
4. DocumentService: empty check → size check (≤4.5MB) → extension check
   → magic byte check (%PDF header + %%EOF/startxref marker)
   → pypdf: page count + text preview (first 3 pages, ≤600 chars)
5. DocumentResult stored in st.session_state.pending_document
6. Preview text shown in sidebar expander
7. User types question and submits
8. doc_result captured, pending_document cleared
9. BedrockService._build_content_blocks():
   → [{"document":{"format":"pdf","name":"filename","source":{"bytes":raw_bytes}}}, {"text":"question"}]
10. converse_stream() called — Nova Pro reads the full PDF and streams answer
11. Document pill shown in chat history
```

#### RAG Request Flow 🔮 Not implemented

RAG is not implemented in this project. Direct document understanding via the Bedrock
Converse API document block is used instead. This is appropriate because:
- Nova Pro supports PDFs up to 4.5 MB natively — no chunking needed
- For a single-document Q&A use case, direct understanding is simpler and cheaper
- RAG would be the right approach for: a corpus of many documents, docs >4.5 MB,
  or semantic retrieval across a knowledge base

If asked: "My approach for adding RAG would be Amazon Bedrock Knowledge Bases,
which provides a managed vector store backed by OpenSearch Serverless. I would use
the Amazon Nova Multimodal Embeddings model for indexing."

---

## 3. Amazon Bedrock — Deep Dive

### What is Amazon Bedrock?

Amazon Bedrock is a fully managed AWS service that provides API access to foundation models
from multiple providers — Amazon, Anthropic, Meta, Mistral, and others — without requiring
you to manage any GPU infrastructure. You pay per token processed and only when the API is called.

### Why Bedrock instead of OpenAI API or hosting an open-source LLM?

| Factor | Bedrock | OpenAI API | Self-hosted LLM |
|---|---|---|---|
| AWS integration | Native IAM, VPC, CloudWatch | External vendor | Depends on setup |
| Infrastructure | Zero — fully managed | Zero | Requires GPU servers |
| Cost model | Pay per token | Pay per token | Fixed GPU cost + ops |
| Data residency | Stays in your AWS account | Sent to OpenAI | Stays on your infra |
| Portfolio signal | AWS engineer narrative | Generic | ML engineer narrative |
| Multimodal (text+image+doc) | ✅ Nova Pro supports natively | ✅ GPT-4o | Depends on model |

For a portfolio project targeting AWS Generative AI roles, Bedrock is the correct choice
because it keeps the entire stack within AWS and demonstrates knowledge of AWS-native services.

### Model Used

**Model ID:** `amazon.nova-pro-v1:0`
**Fallback:** `us.amazon.nova-pro-v1:0` (cross-region inference profile)

The model is called via the **Converse API** using boto3:
```python
boto3.client("bedrock-runtime").converse_stream(
    modelId="amazon.nova-pro-v1:0",
    messages=[...],
    system=[{"text": "system prompt"}],
    inferenceConfig={"maxTokens": 2048, "temperature": 0.7}
)
```

### Converse API vs InvokeModel API

This project uses the **Converse API** (not InvokeModel). The Converse API provides:
- Unified interface across all models (same code works with Nova, Claude, Llama)
- Native multi-turn conversation support with a messages array
- Native system prompt support
- Native streaming via converse_stream()
- Native multimodal content blocks (image, document, text)

InvokeModel is model-specific and requires knowing each model's unique JSON schema.
Converse is the correct choice for production applications.

### Authentication — How Bedrock Credentials Work

boto3 uses a credential chain in this order:
1. `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` environment variables
2. `~/.aws/credentials` — configured via `aws configure`
3. EC2 IAM Instance Role — no credentials needed on the server at all

The application never stores credentials in code. On EC2, an IAM role with
`AmazonBedrockFullAccess` is attached to the instance, so boto3 automatically retrieves
short-lived credentials from the EC2 instance metadata service.

### Model Auto-Fallback

If Bedrock returns `AccessDeniedException` on the first call with `amazon.nova-pro-v1:0`,
the BedrockService automatically retries with `us.amazon.nova-pro-v1:0` — the cross-region
inference profile. This handles cases where the base model is not available in the specific
region but the cross-region profile works. This logic is in `bedrock_service.py`
in the `stream_response()` method.

---

## 4. Multimodal AI — How Each Modality Works

### Text ✅ Implemented

- **Input:** User types in `st.chat_input()`. Sanitised to 10,000 chars max.
- **Processing:** `_build_content_blocks()` creates `[{"text": "message"}]`
- **Model interaction:** Full conversation history + new message sent via `converse_stream()`
- **Output:** Streamed token by token, rendered with `▌` cursor, finalised on completion
- **Memory:** Each turn appended to `bedrock_history` as user+assistant message pair
- **Limitation:** History is session-scoped only — no persistence across browser sessions

### Image ✅ Implemented

- **Input:** JPEG, PNG, GIF, or WebP, max 5 MB, uploaded via sidebar file uploader
- **Processing:** `ImageService.process()` — magic bytes, EXIF rotation, RGBA→RGB, thumbnail
- **Model interaction:** Image block + text block sent in a single Converse API call:
  `{"image": {"format": "jpeg", "source": {"bytes": raw_bytes}}}`
- **Output:** Model describes, analyses, or answers questions about the image
- **Thumbnail:** 400×400 px PNG displayed in sidebar and chat history
- **Limitation:** One image per message. No video support (Nova Pro supports video but it
  is not exposed in this UI).

### Document / PDF ✅ Implemented

- **Input:** PDF, DOCX, CSV, TXT, MD, HTML, XLS, XLSX — max 4.5 MB
- **Processing:** `DocumentService.process()` — magic bytes, size check, pypdf preview
- **Model interaction:** Document block + text block in a single Converse API call:
  `{"document": {"format": "pdf", "name": "filename", "source": {"bytes": raw_bytes}}}`
- **Output:** Model reads the full document content and answers questions about it
- **Preview:** First 3 pages of text extracted by pypdf, shown in sidebar expander
- **Limitation:** One document per message. Documents must be under 4.5 MB for the Bedrock
  Converse API limit. Scanned/image-only PDFs cannot be text-extracted by pypdf but the
  model itself can still analyse them because it has vision capability.

---

## 5. Architecture: Why Each Technology Was Chosen

### Streamlit — Why not React or Flask?

**Decision:** Streamlit ✅
**Alternative considered:** React + Flask REST API

Streamlit allows building a full interactive web application in pure Python with no HTML,
CSS framework, or JavaScript knowledge required. For a portfolio project demonstrating
AI engineering, not frontend engineering, Streamlit is the correct tool.
`st.chat_message()`, `st.chat_input()`, `st.file_uploader()`, and `st.empty()` for streaming
are all first-class primitives that make the chatbot UI straightforward to implement correctly.

**Professional answer:** "I selected Streamlit because it allowed me to build a production-quality
chat interface in Python without introducing JavaScript dependencies. For a project whose primary
demonstration value is the AI integration and AWS architecture, not the frontend, Streamlit was
the right level of abstraction."

### boto3 over LangChain for Bedrock calls — Why?

**Decision:** Direct boto3 `converse_stream()` ✅
**Alternative:** LangChain `ChatBedrockConverse` (used in the original project)

The new `services/bedrock_service.py` calls Bedrock directly via boto3 for three reasons:
1. Full control over the exact Converse API payload — including image blocks and document blocks,
   which LangChain's abstraction layer does not expose cleanly for all formats
2. Native streaming control — accessing the raw event stream directly
3. Fewer layers of abstraction = easier to debug and explain in an interview

LangChain is still in `requirements_new.txt` for compatibility with any future extension work.

### Direct document bytes — Why not S3 + presigned URLs?

**Decision:** Send document raw bytes directly in the Converse API request ✅
**Alternative:** Upload to S3, pass S3 URI to Bedrock

For files under 4.5 MB, sending bytes directly is simpler (no S3 bucket to create or manage),
faster (no extra upload round trip), cheaper (no S3 storage or GET request costs), and
requires fewer IAM permissions. S3 integration would be the right choice if files needed to
be persisted across sessions or reused across multiple API calls.

### No Lambda / No API Gateway — Why?

**Decision:** Streamlit serves its own HTTP ✅
**Alternative:** API Gateway → Lambda → Bedrock

Streamlit is a long-running server process. Lambda functions have a 15-minute maximum
execution timeout and are designed for short-lived, event-driven compute. Putting a Streamlit
app inside Lambda would require complex hacks (Mangum adapter, response chunking) and would
still not work correctly for streaming responses. The correct compute for a Streamlit app
is EC2 (for persistent hosting) or a container (ECS/Fargate).

Lambda would be the right choice if the frontend were a React SPA calling a REST API,
with Bedrock called from within the Lambda function.

### No DynamoDB — Why?

**Decision:** Session state only ✅
**Alternative:** DynamoDB for persistent conversation history

For a portfolio demo with single-user access, Streamlit session state is sufficient.
DynamoDB would be needed for: persisting conversations across browser sessions, supporting
multiple simultaneous users with isolated histories, or building a conversation retrieval feature.

---

## 6. Security Design

### What is actually implemented ✅

**No hard-coded credentials:** Every secret is loaded through boto3's credential chain.
The code never contains `AWS_ACCESS_KEY_ID = "..."`.

**Environment variable support:** `bedrock_service.py` reads `AWS_DEFAULT_REGION`,
`BEDROCK_MODEL_ID`, and `BEDROCK_SYSTEM_PROMPT` from environment variables with safe defaults.
`.env.example` documents all variables. `.gitignore` blocks `.env` from being committed.

**File validation — three layers:**
1. Extension allowlist (only known safe extensions accepted)
2. File size limits (5 MB images, 4.5 MB documents)
3. Magic byte / content integrity checks (prevents spoofed files with wrong extensions)

**Path traversal protection:** `sanitize_filename()` in `utils/validators.py` uses
`Path(filename).name` to strip all directory components, then normalises unicode with NFKC,
replaces special characters with underscores, and enforces a 100-character length limit.
This prevents attacks like `../../../../etc/passwd.pdf`.

**Input sanitisation:** `sanitize_user_input()` strips whitespace and truncates inputs
to 10,000 characters with a truncation notice appended.

**No file persistence:** Uploaded files are held in memory as bytes in `session_state`.
They are never written to disk permanently.

### What is not implemented 🔮

- No HTTPS on EC2 (would require nginx + certbot or ALB + ACM)
- No authentication or access control
- No rate limiting on uploads or API calls
- No Bedrock Guardrails for content filtering

### IAM Least Privilege — What permissions does this app actually need?

Minimum required IAM permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
    "bedrock:ListFoundationModels"
  ],
  "Resource": "*"
}
```
`AmazonBedrockFullAccess` is used for convenience in EC2 deployment guidance,
but for production the minimum policy above is the correct approach.

---

## 7. Cost Optimization

### What actually generates charges

**Amazon Bedrock (Nova Pro)** is the only billable component:
- $0.80 per million input tokens
- $3.20 per million output tokens
- No charge when the app is idle — strictly pay-per-request

**EC2** (if deployed): ~$8/month for t3.micro. Free tier eligible (t2.micro, 12 months).

**Everything else in this project generates zero AWS charges** because S3, Lambda,
API Gateway, DynamoDB, and CloudWatch are not used.

### Cost control decisions made in the design

1. **No S3** → no storage costs for uploaded files
2. **No DynamoDB** → no per-request costs for conversation history
3. **No always-on Lambda** → no unnecessary compute
4. **max_tokens default 2048** → limits output token costs. User can reduce to 256 or 512
   in the sidebar for even lower costs during demos
5. **Session-scoped history** → history clears when the session ends, preventing unbounded
   context growth that would increase input token costs over a very long session
6. **Direct bytes over S3 URIs** → no S3 GET request costs per inference call

### Practical cost estimate

A 30-minute active demo session with 20 interactions (mix of text, image, PDF):
- Estimated input tokens: ~50,000
- Estimated output tokens: ~15,000
- Estimated cost: ~$0.04 + ~$0.05 = **~$0.09 total**

---

## 8. Challenges and Solutions

### Challenge 1 — WebP magic byte validation edge case ✅ Actually occurred and fixed

**Problem:** A 4-byte buffer containing only `RIFF` passed the WebP magic byte check
even though it was clearly not a valid WebP file, because the original code checked
`file_bytes[8:12]` without first verifying the buffer was at least 12 bytes long.

**Root cause:** Python silently returns an empty bytes object when you slice beyond the
buffer length, so `b"RIFF"[8:12]` returns `b""` instead of raising an error.
The comparison `b"" == b"WEBP"` is False, which should have rejected the file —
but the surrounding logic was structured incorrectly, allowing it through.

**Solution:** Added an explicit `len(file_bytes) < 12` guard before the offset-8 check
in `_check_magic_bytes()` in `services/image_service.py`. Also refactored the WebP check
as a special case separate from the general magic byte loop.

**Interview explanation:** "During testing, I found that a 4-byte RIFF buffer was slipping
through my WebP validation. Python's slice operator doesn't raise an IndexError on out-of-bounds
slices — it just returns empty bytes. So my `file_bytes[8:12] == b'WEBP'` check was producing
False as expected, but the logic that handled that False was wrong. I fixed it by adding an
explicit minimum-length guard before attempting any offset-based check."

---

### Challenge 2 — Two separate history objects required ⚡ Potential interview discussion

**Problem:** Streamlit reruns the entire script on every user interaction. If the AI conversation
history contained raw binary bytes from image and document blocks, and was used for UI rendering,
it would be extremely slow and could cause memory issues.

**Solution:** Maintain two separate state objects: `bedrock_history` contains raw Converse API
message dicts (including binary bytes) and is only sent to Bedrock. `chat_history` contains
lightweight display dicts (role, text, timestamp, file_name, thumbnail_bytes) and is only
used for UI rendering. They are kept in sync but never mixed.

**Interview explanation:** "I quickly realised that using one shared history object for both
the API call and the UI display would be a problem. The Bedrock history can contain raw image
bytes — potentially megabytes — that would be re-rendered on every Streamlit rerun.
I separated the concerns: the API history is purpose-built for Bedrock, and the display history
is purpose-built for the UI. Each is optimised for its specific use case."

---

### Challenge 3 — Streaming with Streamlit's rerun model ⚡ Potential interview discussion

**Problem:** Streamlit's programming model reruns the script on every interaction.
If you try to update a UI element from inside a streaming loop, you need to be careful
about how Streamlit handles partial renders.

**Solution:** Use `st.empty()` as a placeholder inside a `with st.chat_message()` block.
Update the placeholder's markdown content on every chunk with a `▌` cursor appended.
When the stream ends, update the placeholder one final time without the cursor.
This gives a smooth typing animation without triggering a full Streamlit rerun on each chunk.

**Interview explanation:** "Streamlit's execution model means the whole script reruns on
every interaction. To get smooth streaming, I use `st.empty()` as a single updatable slot
inside the assistant chat bubble. Each token chunk calls `placeholder.markdown(accumulated + '▌')`.
The `▌` character acts as a typing cursor. When streaming completes, I do a final
`placeholder.markdown(full_text)` to remove it. This is the standard Streamlit streaming pattern."

---

### Challenge 4 — sys.path for service imports ✅ Actually solved in code

**Problem:** When Streamlit runs `mod_chatbot_frontend.py`, the working directory may not
be the project root, so `from services.bedrock_service import ...` would fail with
`ModuleNotFoundError`.

**Solution:** At the top of `mod_chatbot_frontend.py`, resolve the script's own location
using `Path(__file__).parent.resolve()` and prepend it to `sys.path` if not already present.
This guarantees imports work regardless of the directory Streamlit was launched from.

---

## 9. Important Design Decisions

| Decision | Chosen | Alternative | Why alternative rejected |
|---|---|---|---|
| AI provider | Amazon Bedrock | OpenAI API | Data stays in AWS account; stronger AWS portfolio signal; IAM-native auth |
| Model | Amazon Nova Pro | Claude 3.5 Sonnet | 3-5× cheaper; already enabled; sufficient for demo; AWS-native |
| Frontend | Streamlit | React + Flask | Pure Python; faster to build; appropriate for AI demo projects |
| API calls | boto3 converse_stream() | LangChain ChatBedrockConverse | Direct control over multimodal content blocks; cleaner streaming |
| Document processing | Direct bytes via Converse API | RAG / vector store | No chunking overhead; simpler; cheaper; sufficient for ≤4.5MB files |
| File storage | In-memory bytes only | S3 | No persistence needed; no S3 cost; fewer IAM permissions required |
| Compute | EC2 (Streamlit server) | Lambda + API Gateway | Streamlit is long-running; Lambda's 15-min limit incompatible |
| History persistence | Session state only | DynamoDB | Single-user portfolio demo; no cross-session retrieval needed |
| Credentials | Default credential chain | Hard-coded keys | Security best practice; IAM role works on EC2 with zero config |

---

## 10. Interview Questions and Answers

### Beginner Questions

**Q: What does this project do?**
**A:** It is a multimodal AI chatbot that lets users have text conversations, upload and analyse images, and ask questions about PDF and document files. It streams responses in real time like ChatGPT. The AI is powered by Amazon Nova Pro on AWS Bedrock.
**Interviewer testing:** Basic comprehension.
**Follow-up:** What does multimodal mean? **A:** It means the model can accept multiple types of input — text, images, and documents — in a single request, rather than being limited to text only.

---

**Q: What is Streamlit?**
**A:** Streamlit is a Python library for building interactive web applications. It runs a web server and re-executes the Python script on every user interaction, rebuilding the UI state from scratch each time. It is widely used for AI and data science demos because it requires no HTML or JavaScript.
**Interviewer testing:** Frontend knowledge.
**Follow-up:** Why does Streamlit rerun the whole script? **A:** It is Streamlit's execution model — it treats every user action as a fresh script execution, relying on `session_state` to persist data between reruns.

---

**Q: What is Amazon Bedrock?**
**A:** Amazon Bedrock is a fully managed AWS service that provides API access to large language models from multiple providers — Amazon, Anthropic, Meta, Mistral, and others — without you needing to manage any GPU servers or model infrastructure. You pay per token only when you make a request.
**Interviewer testing:** AWS knowledge.
**Follow-up:** How is it different from SageMaker? **A:** SageMaker is for training and deploying your own models. Bedrock is for using pre-built foundation models as an API service. No training or deployment management needed with Bedrock.

---

**Q: What Python version does this project use?**
**A:** Python 3.14.6, running in a virtual environment at `.venv/`. The code uses modern Python features including `from __future__ import annotations` for deferred type evaluation, `match`-compatible union types in function signatures, and dataclasses.
**Interviewer testing:** Python knowledge.

---

**Q: How do you run this project?**
**A:** Activate the virtual environment with `.\.venv\Scripts\Activate.ps1`, install dependencies with `pip install -r requirements_new.txt`, verify AWS access with `python scripts/bedrock_model_access_check.py`, then run `streamlit run mod_chatbot_frontend.py`. The app opens at `http://localhost:8501`.

---

**Q: How does the chatbot remember previous messages?**
**A:** Conversation history is stored in `st.session_state.bedrock_history` — a Python list of Converse API message dictionaries. Every turn appends a user message dict and an assistant message dict. The full history is sent to Bedrock on every request, so the model always has the complete conversation context.
**Follow-up:** What happens if the conversation gets very long? **A:** Nova Pro has a 300,000 token context window, so very long conversations would eventually approach that limit. The current implementation does not implement automatic truncation — that would be a future improvement.

---

**Q: How is the file uploaded to the AI?**
**A:** Files are never stored on disk permanently. The raw bytes are read from the Streamlit `UploadedFile` object into memory, validated, and then sent directly as a bytes value inside the Bedrock Converse API content block. When the user clicks "Remove" or starts a new conversation, the bytes are cleared from session state.

---

**Q: What is the system prompt?**
**A:** The system prompt is a set of instructions sent to the model at the start of every conversation that defines the assistant's persona and behaviour. In this project it defaults to: "You are NovaMind, an intelligent multimodal AI assistant powered by Amazon Nova Pro on AWS Bedrock..." Users can edit it live in the sidebar's system prompt expander.

---

**Q: Can users download the conversation?**
**A:** Yes. The sidebar has a "Download transcript" button that appears once there are messages in the conversation. It calls `export_conversation_as_text()` in `utils/validators.py`, which formats the chat history as plain text and serves it as a `.txt` file download via `st.download_button()`.

---

**Q: How is temperature controlled?**
**A:** There is a temperature slider in the sidebar ranging from 0.0 to 1.0 in 0.05 steps. When the user moves it, `BedrockService.update_settings()` is called, which updates the `self.temperature` attribute. The new value is passed to Bedrock in `inferenceConfig.temperature` on the next request. Default is 0.7.

---

**Q: What files does the project contain?**
**A:** `mod_chatbot_frontend.py` is the main Streamlit app. `services/bedrock_service.py` handles all Bedrock API calls. `services/document_service.py` processes document uploads. `services/image_service.py` processes image uploads. `utils/validators.py` provides shared helpers. `scripts/bedrock_model_access_check.py` is a diagnostic tool. Documentation is in `README.md`, `architecture.md`, `deployment.md`, `cleanup.md`, `model_selection.md`, and `troubleshooting.md`.

---

**Q: Is any data stored in AWS?**
**A:** No. This project does not create any AWS storage resources. No S3 buckets, no DynamoDB tables. Files are sent directly as bytes to Bedrock and are not persisted anywhere in AWS. The only AWS service that receives data is Amazon Bedrock for inference.

---

**Q: How do you handle errors from Bedrock?**
**A:** `BedrockService.stream_response()` has a `try/except` block that catches `botocore.exceptions.ClientError`. If the error code is `AccessDeniedException` and it is the first attempt, it automatically retries with the cross-region inference profile. For other errors, it yields a user-visible error message like `[Bedrock error — ThrottlingException]: ...` instead of raising an exception. The frontend also has a catch-all `except Exception` that displays the error in the chat bubble with a `⚠️` prefix.

---

**Q: What is a virtual environment and why use one?**
**A:** A virtual environment is an isolated Python installation that keeps project dependencies separate from the system Python. This prevents version conflicts between projects. This project uses `.venv/` created with `python -m venv .venv`.

---

**Q: How do you configure AWS credentials for local development?**
**A:** Run `aws configure` and provide your AWS Access Key ID, Secret Access Key, default region (us-east-1), and output format (json). boto3 reads these from `~/.aws/credentials` automatically. For EC2 deployment, an IAM role is attached to the instance instead — no credentials file needed at all.

---

### Intermediate Questions

**Q: Why did you build a service layer instead of putting all logic in the frontend?**
**A:** Streamlit reruns the entire script on every user interaction. If business logic like Bedrock API calls and file processing were mixed into the frontend, they would be harder to test, harder to reason about, and would run inside Streamlit's rerun context unnecessarily. The service layer — `services/bedrock_service.py`, `services/document_service.py`, `services/image_service.py` — has no Streamlit imports and can be called from a CLI, a test suite, or a different frontend without any changes.
**Follow-up:** How would you test the service layer? **A:** Each service class is independently instantiable. `DocumentService().process(b"%PDF...", "test.pdf")` can be called in pytest without a running Streamlit server. The smoke tests in the project root already demonstrate this pattern.

---

**Q: Explain the Bedrock Converse API content block format.**
**A:** The Converse API represents each user message as a list of typed content blocks. A text-only message is `[{"text": "hello"}]`. An image message is `[{"image": {"format": "jpeg", "source": {"bytes": raw_bytes}}}, {"text": "what is this?"}]`. A document message is `[{"document": {"format": "pdf", "name": "myfile", "source": {"bytes": pdf_bytes}}}, {"text": "summarise this"}]`. The text block always goes last — this is the recommended ordering in Nova Pro's documentation. The `_build_content_blocks()` method in `BedrockService` enforces this ordering.
**Follow-up:** Can you send both an image and a document in the same message? **A:** The Converse API supports it structurally, but the current UI only allows one attachment per message — either a pending image or a pending document, not both simultaneously. Supporting both would require a UI change.

---

**Q: How does streaming work technically?**
**A:** `boto3.client("bedrock-runtime").converse_stream()` returns a response object with a `stream` key containing an event iterator. Each event is a dictionary. We check for `contentBlockDelta` events and extract `event["contentBlockDelta"]["delta"].get("text", "")`. These chunks are yielded from `stream_response()` as a Python generator. The frontend iterates the generator, accumulates text, and calls `placeholder.markdown(accumulated + "▌")` on each chunk. This updates the UI in place without a full Streamlit rerun.

---

**Q: What is the difference between bedrock_history and chat_history?**
**A:** `bedrock_history` is the raw Converse API message history — a list of `{"role": ..., "content": [...content_blocks...]}` dicts, where content blocks may contain binary bytes for images and documents. It is sent to Bedrock on every request. `chat_history` is the display history — a list of lightweight dicts with role, text, type, timestamp, filename, and thumbnail bytes. It is used exclusively for re-rendering the UI on each Streamlit rerun. They are updated in sync after each turn but serve completely different purposes.

---

**Q: How does file validation work at multiple layers?**
**A:** Layer 1 is the extension allowlist — only known safe extensions are accepted (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` for images; `.pdf`, `.txt`, `.md`, `.html`, `.csv`, `.doc`, `.docx`, `.xls`, `.xlsx` for documents). Layer 2 is file size — images max 5 MB, documents max 4.5 MB matching the Bedrock Converse API limit. Layer 3 is magic bytes / content integrity — the actual file header bytes are checked against known signatures to prevent a user renaming a malicious file with a safe extension. For PDFs that is `%PDF` at offset 0, for JPEG `\xff\xd8\xff`, for WebP `RIFF` at 0 and `WEBP` at offset 8.

---

**Q: Why is pypdf an optional dependency?**
**A:** The PDF preview feature (showing the first 3 pages of text in the sidebar) requires pypdf. However, the core PDF analysis feature — sending the PDF to Bedrock and getting answers — works without it, because the raw bytes are sent directly to Bedrock regardless. Making pypdf optional means the app degrades gracefully: if pypdf is not installed, PDF files still work, they just show a message instead of a text preview. This is a deliberate design choice documented in `document_service.py`.

---

**Q: How does the cross-region inference fallback work?**
**A:** When `stream_response()` first calls Bedrock, it uses `self.model_id` which defaults to `amazon.nova-pro-v1:0`. If Bedrock returns `AccessDeniedException` AND this is the first attempt (checked by comparing `self._active_model_id == self.model_id`), it sets `self._active_model_id = "us.amazon.nova-pro-v1:0"` and recursively calls `stream_response()` again with all the same parameters. On the retry, `_resolve_model_id()` returns the inference profile. If the retry also fails, the error is propagated to the caller as a visible error message.

---

**Q: What is path traversal and how is it prevented here?**
**A:** Path traversal is an attack where a user uploads a file with a name like `../../../../etc/passwd.txt` hoping it will be written to a dangerous location on the server. In `sanitize_filename()` in `utils/validators.py`, the first operation is `Path(filename).name`, which strips all directory components and returns only the final filename component. This completely eliminates path traversal risk. Then unicode is NFKC-normalised, special characters are replaced with underscores, and the result is truncated to 100 characters.

---

**Q: How is conversation context managed for long sessions?**
**A:** Currently, the full conversation history is sent to Bedrock on every request. Nova Pro's 300K token context window supports approximately 200,000–250,000 words of context before truncation becomes an issue. For typical demo sessions, this is more than sufficient. For production use with very long sessions, the right approach would be to implement a sliding window (keep only the last N turns) or conversation summarisation (summarise older turns into a single context block). Neither is currently implemented — it is noted as a future improvement.

---

**Q: How do you handle EXIF orientation in uploaded images?**
**A:** Mobile phone cameras often save images with a rotation flag in the EXIF metadata rather than physically rotating the pixel data. Without correction, an image taken in portrait mode might appear sideways. `ImageService._process_with_pillow()` calls `ImageOps.exif_transpose(img)` from Pillow, which reads the EXIF orientation tag and physically rotates/flips the pixel data to match. This ensures the image the model sees matches what the user intended.

---

**Q: Why do you maintain a BedrockService instance in session_state?**
**A:** The boto3 client creation (`boto3.client("bedrock-runtime", ...)`) involves setting up connection pools and credential resolution — it is not free. If we created a new client on every Streamlit rerun, it would add unnecessary latency. Caching the `BedrockService` instance in `st.session_state.bedrock_service` means the client is created once per browser session and reused for all subsequent requests. It is reset to `None` when the user clicks "Clear" or "New conversation".

---

**Q: Explain the dataclass design for ImageResult and DocumentResult.**
**A:** Both result types use Python `@dataclass`. `ImageResult` stores: `file_name`, `file_size`, `img_format` (the Bedrock format string like "jpeg"), `raw_bytes` (sent to Bedrock), `thumbnail_bytes` (400×400 PNG for UI), `width`, `height`, `is_valid`, and `error_message`. `DocumentResult` stores: `file_name`, `file_size`, `doc_format`, `raw_bytes`, `preview_text`, `page_count`, `is_valid`, `error_message`. Both have an `is_valid` flag so the caller can check `result.is_valid` instead of catching exceptions. On failure, separate `ImageValidationError` and `DocumentValidationError` dataclasses are returned — same `is_valid=False` pattern, no exception propagation to the UI layer.

---

**Q: What is the inferenceConfig in the Bedrock Converse API call?**
**A:** `inferenceConfig` is the dictionary that controls the model's generation behaviour. In this project it contains `maxTokens` (maximum number of tokens in the response — configurable 256 to 8192 via sidebar) and `temperature` (randomness — 0.0 to 1.0 via sidebar). These are passed in every `converse_stream()` call and updated live via `BedrockService.update_settings()`.

---

**Q: How would you add a second model (like Claude) to this project?**
**A:** The `BedrockService` already supports this — the `model_id` parameter in `get_bedrock_service()` can be set to any Bedrock model ID that supports the Converse API. I would add a model selector dropdown in the sidebar that calls `BedrockService.update_settings()` with the chosen model ID, or recreates the service with the new model ID. The content block format (text, image, document) is the same across Nova and Claude models since they both use the Converse API.

---

**Q: What does the bedrock_model_access_check.py script do?**
**A:** It runs 10 sequential checks: Python version ≥3.9, required packages installed, AWS credentials valid via `sts.get_caller_identity()`, region supports Nova Pro, Bedrock service reachable via `list_foundation_models()`, Nova and Claude model IDs in the model list, live text inference test with actual token count reporting, image capability test using a programmatically generated 1×1 PNG, document capability test using a minimal PDF, and streaming test via `converse_stream()`. Results are printed with green ✔ or red ✘ symbols and a final pass/fail summary. It is the first thing to run before starting the app.

---

**Q: How does the thumbnail generation work?**
**A:** After Pillow opens the uploaded image, a copy is made with `img.copy()`. `thumb.thumbnail((400, 400), Image.LANCZOS)` resizes it to fit within 400×400 pixels while preserving aspect ratio (LANCZOS is high-quality downsampling). The thumbnail is always saved as PNG regardless of the original format — PNG is lossless and appropriate for UI display. If the mode is RGBA or palette-based, it is converted to RGBA first. The result is stored as bytes in `ImageResult.thumbnail_bytes` and displayed via `st.image()` in the sidebar and in chat history.

---

### Advanced Questions

**Q: How would you scale this to 10,000 concurrent users?**
**A:** The current architecture — a single Streamlit process on one EC2 instance — cannot handle 10,000 concurrent users. For that scale I would: (1) Replace Streamlit with a React frontend and a proper REST or WebSocket API, (2) Put the AI logic in AWS Lambda functions (one per request, not the Streamlit server), (3) Use API Gateway for routing and throttling, (4) Store conversation history per user in DynamoDB with TTL for automatic expiry, (5) Use Amazon Cognito for user authentication and session isolation, (6) Configure Bedrock quotas and request-level throttling, (7) Add CloudWatch metrics and alarms for latency and error rates. The current architecture is appropriate for a demo or internal tool with a handful of users.

---

**Q: How would you implement RAG for large document collections?**
**A:** I would use Amazon Bedrock Knowledge Bases. The pipeline would be: upload documents to S3, trigger a Knowledge Base sync which uses Amazon Titan Embeddings or Nova Multimodal Embeddings to chunk and embed the documents, store embeddings in a vector store backed by OpenSearch Serverless or Amazon Aurora pgvector. At query time, embed the user's question, retrieve the top-K relevant chunks via similarity search, inject them into the Bedrock prompt as context, and call Nova Pro for the answer. This is appropriate when: documents exceed 4.5 MB, you have many documents to search across, or you need semantic retrieval rather than full-document understanding.

---

**Q: How do you handle hallucinations?**
**A:** The current implementation does not have explicit hallucination mitigation. The system prompt instructs the model to say so clearly when it is unsure, which is a basic guardrail. For production, I would implement: (1) Bedrock Guardrails for configurable content and factual filters, (2) For document Q&A, instructing the model to cite specific passages from the document, (3) For high-stakes use cases, a verification step where key factual claims are checked against source material, (4) Temperature set to 0.0–0.2 for factual tasks to reduce randomness. I am transparent that this is a known limitation of the current implementation.

---

**Q: What are the bottlenecks in this architecture?**
**A:** Three main bottlenecks: (1) **Bedrock latency** — Nova Pro's first token typically arrives in 1-3 seconds. Streaming mitigates this perceptually but doesn't eliminate it. (2) **Single Streamlit process** — Streamlit's GIL means requests are processed serially. Multiple simultaneous users would queue behind each other. (3) **In-memory file handling** — for large files near the 4.5 MB limit, the entire file sits in Python process memory during processing and the API call. For the demo use case these are all acceptable trade-offs.

---

**Q: How would you implement persistent conversation history?**
**A:** Replace `st.session_state.bedrock_history` with DynamoDB storage. Each conversation gets a UUID. Each turn is a DynamoDB item: `{conversation_id, turn_number, role, content, timestamp}`. On session start, check for an existing `conversation_id` in browser local storage (via Streamlit's query params or a cookie). Load the history from DynamoDB and reconstruct it. On each new turn, write to DynamoDB before calling Bedrock. For cost control, add a TTL attribute to auto-expire conversations after 30 days.

---

**Q: How would you add user authentication?**
**A:** Use Amazon Cognito. Create a User Pool for user management (sign-up, sign-in, MFA). Use Cognito's hosted UI or a custom login page. After authentication, Cognito issues JWT tokens. The Streamlit app validates the token on each request. For the simplest approach, use `streamlit-cognito-auth` or `streamlit-authenticator` libraries. Each authenticated user gets their own isolated conversation history in DynamoDB keyed by their Cognito user ID.

---

**Q: How would you monitor this in production?**
**A:** Add structured logging using Python's `logging` module with a CloudWatch Logs handler via `boto3`. Log: request start time, model ID used, input token count, output token count, file type (if any), file size (if any), latency to first token, total latency, any errors. Create CloudWatch dashboards for: average latency, token consumption rate, error rate, Bedrock throttling events. Set alarms for: error rate > 1%, latency p99 > 10 seconds, Bedrock throttling > 5 per minute.

---

**Q: How would you implement CI/CD for this project?**
**A:** A GitHub Actions workflow triggered on push to main: (1) Run `python -m py_compile` on all Python files, (2) Run the smoke tests in `__smoke_test_tmp.py` style (without AWS calls — mock boto3), (3) Build a Docker image, (4) Push to ECR, (5) Deploy to ECS Fargate or update the EC2 instance via AWS Systems Manager Run Command. The diagnostic script `bedrock_model_access_check.py` could be run as a post-deploy smoke test using an IAM role in the CI environment.

---

**Q: Why use a generator (yield) for streaming instead of a callback?**
**A:** Generators are the natural Python idiom for lazy sequences — values produced one at a time. `stream_response()` is a generator function that yields text chunks. The caller (the frontend) controls the iteration pace. This is clean, composable, and testable: `"".join(service.stream_response(...))` gives the full response without any UI code. A callback pattern would couple the service layer to the caller's specific notification mechanism and make testing harder.

---

**Q: How does the system prompt affect the model's behaviour?**
**A:** The system prompt is passed as the `system` parameter in the Converse API call: `system=[{"text": "You are NovaMind..."}]`. It is separate from the conversation history and is not a user turn — it is a privileged instruction that the model treats as a framing constraint. The default prompt establishes: the assistant's name (NovaMind), its capabilities (text, images, documents), its tone (helpful, accurate, professional), and a truthfulness instruction (say so clearly if unsure). Users can override it entirely in the sidebar, which is useful for testing different personas.

---

**Q: What happens if a PDF is scanned (image-only, no selectable text)?**
**A:** `pypdf.PdfReader.extract_text()` returns an empty string for scanned PDFs because there is no embedded text to extract. The sidebar preview shows: "PDF text could not be extracted — may be scanned/image-based. The AI will still analyse it." Importantly, the PDF is still sent to Bedrock as raw bytes. Amazon Nova Pro has vision capabilities and can read text from scanned documents through its image understanding — it processes the PDF pages as rendered images internally. This is documented in the `document_service.py` code.

---

**Q: How would you implement conversation summarisation to handle very long sessions?**
**A:** When `bedrock_history` exceeds a configurable token threshold (e.g. 200,000 tokens), trigger a summarisation step: send the oldest N turns to Nova Pro with a prompt like "Summarise this conversation in under 500 tokens, preserving all key facts and context." Replace those N turns in `bedrock_history` with a single synthetic system or user turn containing the summary. This keeps the active context window reasonable while preserving semantic continuity. pypdf's character count and an approximate tokens-per-character ratio could estimate when to trigger this.

---

**Q: What is the difference between temperature 0.0 and 1.0 in practice?**
**A:** Temperature controls the randomness of token sampling. At temperature 0.0, the model always picks the highest-probability next token — responses are deterministic, focused, and consistent. At temperature 1.0, probability is distributed more evenly across plausible tokens — responses are more creative, varied, and sometimes less accurate. For factual Q&A (like "what does this PDF say?"), low temperature (0.0–0.3) is appropriate. For creative tasks or open-ended conversation, medium temperature (0.5–0.8) works better. The sidebar default is 0.7, which is a good general-purpose balance.

---

**Q: How would you evaluate the quality of model responses?**
**A:** For this portfolio project, evaluation is manual. For production I would implement: (1) LLM-as-judge — use a second Nova Pro call to rate response relevance and accuracy on a 1-5 scale, (2) For document Q&A specifically, compare model answers against known ground truth for a test set of documents, (3) Use AWS Bedrock Evaluations (the managed evaluation service) for automated metrics like ROUGE, BLEU, and semantic similarity, (4) Log thumbs up/down feedback from users and track it in CloudWatch.

---

### AWS Questions

**Q: What is an IAM role and why is it better than access keys for EC2?**
**A:** An IAM role is an identity with permissions policies that can be assumed by AWS services — like an EC2 instance — without requiring stored credentials. When an IAM role is attached to an EC2 instance, the instance metadata service provides automatically rotated, short-lived credentials to any process running on it. boto3 picks these up automatically via the credential chain. This is better than access keys because: there are no long-lived secrets to rotate or accidentally leak; credentials auto-expire and auto-renew; if the EC2 instance is compromised, the attacker can only use credentials until the next auto-rotation (typically 6 hours).

---

**Q: What is the AWS credential chain and what order does boto3 use?**
**A:** boto3 checks for credentials in this order: (1) explicit parameters passed to `boto3.client()`, (2) `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables, (3) AWS config file — `~/.aws/credentials` default profile, (4) Instance metadata service — EC2 IAM role, ECS task role, Lambda execution role. This project relies on options 2 and 3 for local development and option 4 for EC2 deployment. No credentials are ever passed explicitly in code.

---

**Q: What is a cross-region inference profile and when would you use it?**
**A:** A cross-region inference profile (like `us.amazon.nova-pro-v1:0`) routes requests to the model across multiple AWS regions in the same geographic area. This provides: higher throughput limits (combines capacity from multiple regions), better resilience (if one region has capacity issues, requests route to another), and often better availability for new models that are rolling out regionally. You use the inference profile when: you are in a region where the base model is not directly available, you need higher throughput than a single region can provide, or you want automatic failover. The trade-off is slightly higher latency variability.

---

**Q: What is the difference between Bedrock InvokeModel and Converse?**
**A:** `InvokeModel` is the older, model-specific API. Each model has a unique request/response JSON schema — you need to know Anthropic's schema for Claude, Amazon's schema for Nova, etc. `Converse` is the unified API that works the same way for all supported models. It handles: system prompts, multi-turn history, multimodal content blocks, streaming via `ConverseStream`. This project uses `converse_stream()` exclusively because it is the correct production pattern — same code works whether the underlying model is Nova Pro, Nova Lite, or Claude.

---

**Q: How would you use CloudWatch with this project?**
**A:** I would add a `CloudWatchLogsHandler` to the Python logger, creating a log group `/novabot/application` with log streams per EC2 instance. Key metrics to publish as custom CloudWatch metrics via `boto3.client("cloudwatch").put_metric_data()`: `BedrockLatencyMs`, `InputTokensCount`, `OutputTokensCount`, `FileUploadCount`, `ErrorCount`. I would create a CloudWatch dashboard showing these metrics over time and set alarms for error rate and high latency. Currently, Python's standard logging goes to the terminal only — CloudWatch is noted as a future improvement.

---

**Q: What IAM permissions does this application actually need?**
**A:** Minimum: `bedrock:InvokeModelWithResponseStream` on `arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0`, and `bedrock:ListFoundationModels` for the diagnostic script. In practice, `AmazonBedrockFullAccess` is used for the EC2 role in the deployment guide for simplicity. For a production environment, I would scope it to only the specific model ARNs being used.

---

**Q: What is an EC2 instance profile?**
**A:** An instance profile is the container that holds an IAM role and attaches it to an EC2 instance. When you create a role for EC2 in the IAM console, AWS automatically creates an instance profile with the same name. When you attach the role to an EC2 instance in the console ("Modify IAM Role"), you are actually attaching the instance profile. boto3 on that instance then gets credentials from `http://169.254.169.254/latest/meta-data/iam/security-credentials/role-name` — the instance metadata service.

---

**Q: Why us-east-1 specifically?**
**A:** `us-east-1` (US East N. Virginia) is the primary AWS region for Amazon Nova Pro — it was the first region to receive Nova model support and consistently has the most complete model availability. It also has the highest Bedrock quotas and is where AWS rolls out new model capabilities first. The cross-region inference profile `us.amazon.nova-pro-v1:0` uses us-east-1 as one of its target regions. For a portfolio project, us-east-1 is always a safe choice for Bedrock work.

---

**Q: How would you deploy this with containers instead of EC2?**
**A:** Create a `Dockerfile` based on `python:3.12-slim`, copy the project files, install requirements, expose port 8501, and set the entrypoint to `streamlit run mod_chatbot_frontend.py --server.address 0.0.0.0`. Push the image to Amazon ECR. Deploy to ECS Fargate — a serverless container runtime where you pay only for the CPU and memory used while the container is running. Attach an ECS task role (equivalent to EC2 instance profile) so the container gets Bedrock credentials automatically. Put an Application Load Balancer in front for HTTPS termination.

---

**Q: How does Bedrock pricing work — what am I actually paying for?**
**A:** Bedrock charges per token — a token is roughly 0.75 words of English text. For Nova Pro: $0.80 per million input tokens (everything sent to the model: system prompt + history + user message + image/document content) and $3.20 per million output tokens (the model's response). Image and document inputs are also tokenised internally by the model and count against input tokens — a typical image might be 800-1200 tokens. There are no minimum charges, no per-hour fees, no data transfer costs for Bedrock API calls within the same region. You pay only when an API call is made.

---

**Q: What is the Bedrock model access process?**
**A:** Foundation models in Bedrock are not automatically accessible — you must request access for each model in each region separately. In the AWS Console: Bedrock → Model access → Manage model access → select the models → Save. For Amazon models (Nova family), access is typically granted immediately. For third-party models (Anthropic, Meta), some require a brief review. The `bedrock_model_access_check.py` script tests this by attempting a live inference call and reporting the result.

---

**Q: What would happen if Bedrock was temporarily unavailable?**
**A:** The `converse_stream()` call would raise a `botocore.exceptions.ClientError` with an error code like `ServiceUnavailableException` or `ThrottlingException`. The `stream_response()` method catches this, logs it, and yields a user-visible error message to the frontend. The streaming generator yields the error string, and `_stream_and_display_response()` in the frontend renders it in the assistant chat bubble. The conversation history is not corrupted — the failed turn is not appended because `full_reply` contains the error message which is appended, but this is recoverable by retrying.

---

**Q: How would you implement Bedrock Guardrails?**
**A:** Create a Guardrail in the Bedrock console with policies for: content filtering (hate speech, violence, profanity), topic denial (block off-topic subjects), sensitive information (PII detection), grounding (for RAG — ensure responses are grounded in provided context). Then pass `guardrailConfig={"guardrailId": "...", "guardrailVersion": "1"}` in the `converse_stream()` call. If the guardrail triggers, Bedrock returns a `guardrailResult` event in the stream instead of content. Currently not implemented — noted as a future improvement.

---

**Q: How does Amazon Nova Pro compare to Nova Lite for this use case?**
**A:** Nova Pro and Nova Lite support the same modalities (text, image, document, video) and have the same 300K token context window. The key differences: Nova Pro has stronger reasoning and instruction-following quality — better for document Q&A where precise answers matter. Nova Lite is roughly 13× cheaper ($0.06/M vs $0.80/M input) — better for high-volume, cost-sensitive applications where speed and cost matter more than accuracy. For a portfolio demo where response quality is important for impression, Nova Pro is the right choice. For a production app processing thousands of documents, Nova Lite would be worth evaluating.

---

### Generative AI Questions

**Q: What is a foundation model?**
**A:** A foundation model is a large neural network trained on a massive, broad dataset (text, code, images) using self-supervised learning. It is "foundational" because it is general-purpose — the same model can be applied to many tasks through prompting or fine-tuning without being retrained from scratch. Examples: Amazon Nova Pro, Anthropic Claude, Meta Llama. Amazon Bedrock provides API access to foundation models without requiring you to train or host them yourself.

---

**Q: What is the difference between a foundation model and a fine-tuned model?**
**A:** A foundation model is general-purpose — trained on broad data. A fine-tuned model starts from a foundation model and is further trained on a specific, narrower dataset to improve performance on particular tasks or to adopt a specific tone/style. Amazon Nova Pro supports fine-tuning via Amazon Bedrock. This project uses the base foundation model — fine-tuning is noted as a future improvement.

---

**Q: What is prompt engineering and does this project use it?**
**A:** Prompt engineering is the practice of crafting input text to guide a model's output. This project uses it in two places: (1) The system prompt in `bedrock_service.py` defines the assistant's persona, capabilities, and tone, (2) The multimodal content block ordering (image/document before text) is itself a form of prompt engineering — Nova Pro's documentation recommends placing contextual content before the question for better results. The sidebar's system prompt editor lets users do live prompt engineering during conversations.

---

**Q: What is RAG and why is it not in this project?**
**A:** RAG (Retrieval-Augmented Generation) is a technique where relevant documents are retrieved from a vector store and injected into the model's prompt as context, rather than the model relying on its training data alone. It is not implemented here because Nova Pro's native document understanding (sending the full document as bytes in the Converse API) is sufficient for the use case — single-document Q&A with files under 4.5 MB. RAG would be needed for: a corpus of many documents, documents over 4.5 MB, or when you need to retrieve the most relevant passages from a large knowledge base rather than sending the whole document.

---

**Q: What is a context window and why does it matter?**
**A:** The context window is the maximum number of tokens a model can process in a single request — including system prompt, conversation history, any attached documents/images, and the response. Nova Pro's context window is 300,000 tokens (approximately 225,000 words). It matters because: all of the conversation history is sent on every request, so a long conversation grows the input token count; a PDF document counts against the context window; the larger the context, the more expensive the request and the slower the first-token latency.

---

**Q: What is temperature in language models?**
**A:** Temperature is a parameter that controls the randomness of token selection during generation. Mathematically, it scales the logits before the softmax — higher temperature flattens the probability distribution (more randomness), lower temperature sharpens it (more deterministic). In this project it is configurable from 0.0 to 1.0 via the sidebar slider. Default is 0.7.

---

**Q: What is the difference between max_tokens and context window?**
**A:** The context window is the total token budget for the entire request (input + output). `max_tokens` specifically limits the length of the model's output response. In this project, `max_tokens` defaults to 2048 and can be set to 256, 512, 1024, 2048, 4096, or 8192 via the sidebar. If `max_tokens` is 2048 and the input uses 5000 tokens, the model can generate up to 2048 tokens in response, and the total round-trip is 7048 tokens — well within Nova Pro's 300K context window.

---

**Q: How does the Converse API handle multi-turn conversations?**
**A:** Each request to the Converse API includes the full `messages` array — all previous turns plus the new one. The API is stateless: it does not remember previous requests. The application is responsible for maintaining and passing the history. In this project, `bedrock_history` is the list that grows with each turn and is passed as `messages` on every `converse_stream()` call. The format is: `[{"role":"user","content":[...]}, {"role":"assistant","content":[...]}, ...]` alternating.

---

**Q: What is the difference between system prompt and user message?**
**A:** The system prompt (passed as the `system` parameter) is processed by the model as privileged framing instructions — it shapes how the model interprets and responds to all user messages. It is not part of the conversation turns. The user message is part of the `messages` array with `role: "user"`. The model sees the system prompt as background context, not as something the user said. Changing the system prompt does not add to the conversation history.

---

**Q: How does the model process an image vs a document?**
**A:** For images, Nova Pro encodes the raw image bytes using its vision encoder — it "sees" the image and builds an internal representation that is then attended to alongside the text prompt. For documents, the model processes the document's text content (similar to how it processes text, but with document structure awareness). For scanned PDFs (image-only), Nova Pro applies its vision capability to read the rendered pages. Both are handled via the Converse API content blocks — the model's internal processing differs, but the API interface is the same.

---

**Q: What are embeddings and are they used in this project?**
**A:** Embeddings are numerical vector representations of text (or images) that capture semantic meaning. Similar concepts have similar vectors. They are the foundation of RAG systems — documents are embedded and stored in a vector database, then at query time the user's question is embedded and the closest document vectors are retrieved. This project does NOT use embeddings. Direct document bytes are sent to Nova Pro instead. If I were to add RAG, I would use Amazon Nova Multimodal Embeddings (`amazon.nova-multimodal-embeddings-v1:0`) for both text and image embeddings.

---

**Q: What is streaming in the context of LLMs?**
**A:** Without streaming, the API waits until the model generates the complete response, then returns it all at once — users stare at a blank screen for several seconds. With streaming (`ConverseStream`), the API sends each generated token as soon as it is produced. Users see the response appear word by word, which feels much more responsive. The `converse_stream()` method in boto3 returns an iterator of events; `contentBlockDelta` events contain individual text chunks. The frontend accumulates these into a full response while updating the UI on each chunk.

---

### Amazon Bedrock Specific Questions

**Q: What model ID does this project use and why that exact string?**
**A:** `amazon.nova-pro-v1:0`. Breaking it down: `amazon` is the provider namespace. `nova-pro` is the model family and tier. `v1` is the major version. `:0` is the minor version (0 = base model, as opposed to fine-tuned variants which get higher numbers). The fallback is `us.amazon.nova-pro-v1:0` — the `us.` prefix identifies this as the US cross-region inference profile rather than a single-region model.

---

**Q: What document formats does Nova Pro's Converse API support?**
**A:** PDF, CSV, DOC, DOCX, XLS, XLSX, HTML, TXT, and MD. This project supports all of them. The format is passed as a string in the document block: `{"document": {"format": "pdf", "name": "...", "source": {"bytes": ...}}}`. The `document_service.py` maps file extensions to these format strings in the `SUPPORTED_DOC_FORMATS` dictionary.

---

**Q: What is the maximum document size for the Bedrock Converse API?**
**A:** 4.5 MB per document block. This project enforces this limit in `DocumentService` with a hard check before processing. The limit exists because document content is tokenised and sent as part of the context window — larger documents consume more tokens and increase latency. For Nova Pro and Claude 4+, the 4.5 MB restriction does not apply to PDF format specifically, but this project uses 4.5 MB as a conservative safe limit.

---

**Q: How is streaming handled at the boto3 level?**
**A:** `bedrock_runtime.converse_stream()` returns a response dict with a `stream` key containing an `EventStream` object. Iterating over it yields event dicts. Each event has exactly one key indicating its type. For streaming text: `contentBlockDelta` → `delta` → `text`. The generator in `stream_response()` checks `if "contentBlockDelta" in event` and extracts `event["contentBlockDelta"]["delta"].get("text", "")`. The `get()` with a default handles non-text deltas (like tool use blocks) gracefully.

---

**Q: What is Bedrock model access and how do you enable it?**
**A:** Bedrock model access is per-account, per-region gating on foundation models. Even if your IAM policy allows `bedrock:InvokeModel`, you will get `AccessDeniedException` if model access has not been explicitly granted in the Bedrock console. To enable: AWS Console → Bedrock → Model access → Manage model access → tick the model → Save changes. For Amazon models like Nova Pro, access is granted immediately. The diagnostic script tests this with a live inference call.

---

**Q: What is the system parameter in the Converse API?**
**A:** The `system` parameter is a list of system content blocks: `[{"text": "You are a helpful assistant."}]`. It is separate from the `messages` array and is processed as privileged context that frames the entire conversation. Not all Bedrock models support the `system` parameter — Nova Pro and Claude do. The Converse API documentation lists which models support system prompts in the model features table.

---

**Q: Can you send multiple images in one request?**
**A:** The Converse API supports multiple content blocks per message, so technically yes — you could include multiple image blocks. This project's UI only exposes one pending image at a time (one file uploader, one attachment slot per message). Extending it to multiple images would require changing the session state model and the file uploader to support multiple simultaneous attachments.

---

**Q: What happens when the model hits the max_tokens limit mid-response?**
**A:** The model stops generating at `max_tokens` tokens, even if the response is not complete. The streaming event will include a `messageStop` event with `stopReason: "max_tokens"`. In the current implementation, `stream_response()` breaks on `messageStop` events and appends whatever was generated. The response may be truncated. The solution is to increase `max_tokens` — the sidebar allows up to 8192 tokens.

---

**Q: How does the inference profile route requests differently from the base model ID?**
**A:** The base model ID `amazon.nova-pro-v1:0` routes only to the specified region (e.g., us-east-1). The inference profile `us.amazon.nova-pro-v1:0` routes to a pool of US regions — us-east-1, us-east-2, us-west-2 — and dynamically selects the region with available capacity. This provides higher throughput and resilience. The response time may vary slightly depending on which region handles the request, but the model behaviour and output are identical.

---

### Python Questions

**Q: Why use dataclasses for ImageResult and DocumentResult instead of dicts?**
**A:** Dataclasses provide named attributes with type hints, which makes the code self-documenting and IDE-friendly. `result.is_valid` is clearer than `result["is_valid"]`. They also allow computed properties — `result.size_kb`, `result.format_label`, `result.display_name` — which would require helper functions if using plain dicts. The `is_valid` flag pattern avoids exception propagation to the UI layer, which simplifies error handling in the frontend.

---

**Q: What does `from __future__ import annotations` do?**
**A:** It enables PEP 563 postponed evaluation of annotations — type hints are stored as strings rather than being evaluated at class definition time. This allows forward references (using a class name in a type hint before the class is defined) and avoids `NameError` on circular imports. It is standard in Python 3.10+ style code and was used here for compatibility across Python 3.9–3.14.

---

**Q: How does the Python generator pattern work in stream_response()?**
**A:** `stream_response()` contains `yield chunk` statements, which makes it a generator function. Calling it returns a generator object — no code executes yet. The caller iterates it with `for chunk in service.stream_response(...)`, which resumes execution from the last `yield` point each time. The `try/except` block inside the generator catches boto3 exceptions and `yield`s error strings — so the caller always gets a string, never an exception. `invoke_response()` uses `"".join(service.stream_response(...))` to collect the full result without streaming.

---

**Q: What is `Path(__file__).parent.resolve()` doing?**
**A:** `__file__` is the absolute path of the currently executing Python file. `.parent` goes up one directory level. `.resolve()` makes the path absolute and resolves any symlinks. The result is the directory containing `mod_chatbot_frontend.py` — the project root. This is prepended to `sys.path` so that `from services.bedrock_service import ...` works regardless of what directory Streamlit was launched from.

---

**Q: Why use `Optional[str]` vs `str | None`?**
**A:** Both mean the same thing — the value can be a string or None. `Optional[str]` is the Python 3.9 and earlier style from `typing`. `str | None` is the Python 3.10+ union syntax. This project uses `Optional` from `typing` for broad compatibility across Python 3.9–3.14, even though the environment runs 3.14. `from __future__ import annotations` makes both syntaxes safe in all supported versions.

---

**Q: What is `unicodedata.normalize("NFKC", filename)` doing?**
**A:** NFKC (Compatibility Decomposition, followed by Canonical Composition) normalises unicode characters to their canonical forms. This prevents attacks where unicode lookalike characters (e.g., a Cyrillic letter that looks like Latin `a`) are used in filenames to bypass extension checks. It also normalises half-width and full-width characters. Applied before the regex-based sanitisation in `sanitize_filename()`.

---

### Security Questions

**Q: How do you ensure no AWS credentials end up in the Git repository?**
**A:** Three layers: (1) `.env` and `.env.*` are in `.gitignore` — they are never tracked. (2) No credentials appear anywhere in Python source code — only `os.environ.get()` calls with environment variable names. (3) `.env.example` contains only placeholder strings like `AKIAIOSFODNN7EXAMPLE` — never real values. The diagnostic script prints a masked account ID (first 4 and last 4 digits only) and the IAM ARN, but never the actual credentials.

---

**Q: What is magic byte validation and why is it important?**
**A:** File extensions are controlled by the user and can be changed trivially. A malicious user could name a PHP script `photo.jpg`. Magic bytes are the first few bytes of a file that identify its actual format — they are set by the file creation tool and cannot be changed without corrupting the file structure. For JPEG: `\xff\xd8\xff`. For PDF: `%PDF`. Checking magic bytes ensures the file content actually matches the declared extension, preventing extension-spoofing attacks.

---

**Q: What security risks are NOT mitigated in this project?**
**A:** Being transparent: (1) No HTTPS — traffic between the browser and Streamlit is unencrypted HTTP (would need nginx + SSL or ALB + ACM for HTTPS). (2) No authentication — anyone who can reach port 8501 can use the application. (3) No rate limiting — a user could upload files and make Bedrock calls in rapid succession. (4) No Bedrock Guardrails — the model could potentially be prompted into harmful outputs. (5) No WAF (Web Application Firewall). These are all appropriate trade-offs for a portfolio demo but would need addressing for a production deployment.

---

**Q: How would you secure this application for production?**
**A:** Step by step: (1) Add Amazon Cognito for user authentication — only authenticated users can access the app. (2) Put an Application Load Balancer in front with AWS ACM SSL certificate for HTTPS. (3) Add Bedrock Guardrails for content filtering. (4) Add rate limiting using ALB rules or a WAF. (5) Scope IAM permissions to the minimum required — specific model ARNs only. (6) Enable VPC endpoints for Bedrock so traffic never leaves the AWS network. (7) Enable CloudWatch logging with sensitive data masking.

---

## 11. Hard Questions — Professional Answers

**Q: Why did you choose this model specifically?**
**A:** "I chose Amazon Nova Pro (`amazon.nova-pro-v1:0`) for three reasons that I can defend technically. First, it natively supports all three modalities I needed — text, images, and documents — in a single Converse API call, which eliminated the need for separate models or complex orchestration. Second, it already had model access granted in the AWS account from the prior iteration of this project, meaning zero onboarding friction for the demo. Third, at $0.80 per million input tokens, it is approximately four times cheaper than Claude 3.5 Sonnet for equivalent capability on this use case. The 300K token context window is more than sufficient for single-document Q&A. I would switch to Nova Premier for more complex reasoning tasks, or to Nova Lite if I needed to process high volumes at lower cost."

---

**Q: Why Bedrock instead of just calling the OpenAI API?**
**A:** "The primary reason is AWS integration and the portfolio narrative. Bedrock uses IAM for authentication, which means zero credentials to manage on EC2 — the instance role handles it automatically. Data stays within my AWS account and never leaves to a third-party vendor, which matters for enterprise use cases. Bedrock also provides a unified Converse API that works identically across Nova, Claude, Llama, and Mistral — if I want to switch models later, I change one string. OpenAI's API is vendor-locked and requires managing API keys as secrets. For an AWS-focused portfolio, using Bedrock is architecturally correct."

---

**Q: What happens if Bedrock is unavailable?**
**A:** "The `converse_stream()` call raises a `botocore.exceptions.ClientError`. My `stream_response()` method catches this, logs it, and yields a user-friendly error message into the streaming response. The error appears in the chat bubble as `[Bedrock error — ServiceUnavailableException]: ...`. The conversation state is not corrupted. For `ThrottlingException` specifically — which happens when request rate exceeds quotas — the correct production response would be to implement exponential backoff with jitter and retry up to 3 times before surfacing the error. That is currently not implemented but is straightforward to add."

---

**Q: How do you handle large PDFs?**
**A:** "Currently, documents are limited to 4.5 MB — the Bedrock Converse API limit per document block. Enforced in `DocumentService` before any processing happens. For documents larger than 4.5 MB, the application returns a clear validation error explaining the size limit. If I needed to support larger documents, I would implement a RAG pipeline: extract text with pypdf (or Amazon Textract for scanned PDFs), chunk into overlapping segments, embed with Amazon Nova Multimodal Embeddings, store in a Bedrock Knowledge Base backed by OpenSearch Serverless, and retrieve relevant chunks at query time."

---

**Q: How do you control AWS costs?**
**A:** "I made several deliberate cost-control decisions. I use the sidebar max_tokens slider — the default is 2048, but users can drop to 256 for simple questions, which reduces output token costs by 8×. The session-scoped history means history clears between sessions, preventing context from growing unboundedly (which would increase input costs). I chose not to use S3, DynamoDB, Lambda, or API Gateway — none of them are needed and all of them add per-request costs. The only variable cost is Bedrock — $0.80 per million input tokens, $3.20 per million output tokens. A full day of active demo usage typically costs under $1.00."

---

**Q: How do you prevent unauthorised access?**
**A:** "Currently, the application has no authentication — it is a single-user portfolio demo, and anyone who can reach port 8501 can use it. I am transparent about this limitation. For a production deployment, I would add Amazon Cognito: create a User Pool, add the `streamlit-authenticator` library for the login flow, validate JWT tokens from Cognito on each session, and key all conversation history by the authenticated user's ID. The EC2 security group restricts port 8501 access to specific IPs during development — it is only opened to 0.0.0.0/0 for public demo purposes."

---

**Q: How would you scale this to 10,000 users?**
**A:** "The current architecture cannot scale to 10,000 concurrent users as-is. Here is my scaling roadmap: Replace Streamlit with a React SPA calling a REST API. Move the Bedrock calls into AWS Lambda functions — stateless, auto-scaling, event-driven. Put API Gateway in front for routing, throttling, and API key management. Store conversation history in DynamoDB with per-user partition keys and TTL. Add Cognito for user management. Use ECS Fargate for any compute that needs persistent connection handling. Enable Bedrock provisioned throughput if consistent high-volume throughput is needed. Add CloudFront in front of the frontend for global edge caching."

---

**Q: What would you change if this became a production product?**
**A:** "Five things in priority order: (1) Authentication via Cognito — security is non-negotiable for production. (2) HTTPS via ALB + ACM — all traffic must be encrypted. (3) Persistent conversation history in DynamoDB — users expect their history to survive a browser refresh. (4) Structured logging to CloudWatch — you cannot operate a production service you cannot observe. (5) Bedrock Guardrails for content filtering — prevent the model from producing harmful outputs. After those, I would add rate limiting, automated testing in CI/CD, and a multi-model selector so users can choose between Nova Pro, Nova Lite, and Claude based on their needs."

---

**Q: What are the current limitations of this implementation?**
**A:** "I can list the main ones honestly. History is session-scoped only — it clears when the browser tab closes. There is no authentication — anyone with network access can use the app. No HTTPS. Documents are limited to 4.5 MB — no support for large files. No RAG for multi-document retrieval. No CloudWatch monitoring or alerting. No automated testing — the smoke tests are manual scripts rather than a proper pytest suite. No Bedrock Guardrails for content safety. Single-user architecture — multiple simultaneous users share one Streamlit process. I designed these as intentional scope boundaries for a portfolio project, not as oversights, and I have documented each one as a prioritised future improvement."

---

## 12. Live Demo Script

### Before the Interview
```
1. Start the app:  streamlit run mod_chatbot_frontend.py
2. Verify it opens at http://localhost:8501
3. Have ready: one test image (a chart or diagram works well), one test PDF
4. Have the architecture.md open for reference
```

### Demo Sequence

**Step 1 — Open the app and explain the UI** (30 seconds)
- What I do: Point to the dark-themed chat interface, the sidebar controls, the file uploader
- What I say: "This is NovaMind AI — the frontend is Streamlit, the backend calls Amazon Nova Pro on AWS Bedrock. On the left you can see the settings sidebar where you can adjust temperature, response length, and the system prompt. The file uploader accepts images and documents. Let me show you all three modalities."

**Step 2 — Text conversation with follow-up** (1 minute)
- What I do: Type "What is Amazon Bedrock and how does it differ from SageMaker?" then follow up with "Which would you choose for a chatbot like this one?"
- What I say: "Notice the streaming — responses appear word by word, just like ChatGPT. The model remembers the conversation context so I can ask follow-up questions without repeating myself. That is the bedrock_history list being sent with every request."

**Step 3 — Image analysis** (1 minute)
- What I do: Upload a diagram or screenshot, then ask "What does this image show? Describe it in detail."
- What I say: "I uploaded a JPEG image. Behind the scenes, ImageService validated the file, checked the magic bytes, fixed EXIF orientation with Pillow, and generated the thumbnail you see in the sidebar. The raw bytes were sent to Nova Pro as an image content block alongside my text question. The model used its vision encoder to analyse it."

**Step 4 — Document Q&A** (1 minute)
- What I do: Upload a PDF (one from the docs folder works well), then ask "What are the main topics in this document?" then follow up with "Summarise the key points in three bullets."
- What I say: "This is the direct document understanding feature. The PDF is validated by DocumentService — magic bytes checked, size verified against the 4.5 MB limit, pypdf extracts the preview you see in the sidebar. The raw bytes go to Nova Pro as a document block. No chunking, no vector store, no RAG — the model reads the whole document in one shot. This works beautifully for documents under 4.5 MB."

**Step 5 — Show model settings** (30 seconds)
- What I do: Move the temperature slider, change max tokens, open the system prompt expander
- What I say: "These settings update the BedrockService in real time — the next message uses the new values. Temperature controls randomness, max tokens controls response length. The system prompt is the persona instruction — I can completely change how the assistant behaves mid-conversation."

**Step 6 — Download transcript** (15 seconds)
- What I do: Click "Download transcript"
- What I say: "The conversation export calls `export_conversation_as_text()` in the utils layer. It formats the history as a plain text transcript — useful for documentation or follow-up."

**Step 7 — Architecture explanation** (1-2 minutes)
- What I do: Optionally draw on whiteboard or point to the README architecture diagram
- What I say: "Three layers. Top: Streamlit frontend — mod_chatbot_frontend.py — 9 sections, completely separate from business logic. Middle: service layer — BedrockService handles Bedrock API, ImageService handles image validation and Pillow processing, DocumentService handles document validation and PDF preview. Bottom: AWS Bedrock — amazon.nova-pro-v1:0, called via boto3 converse_stream(). No Lambda, no API Gateway, no S3 — they are not needed for this architecture."

---

## 13. Whiteboard Architecture

### Mermaid Diagram

```mermaid
graph TD
    A[User Browser :8501] --> B[mod_chatbot_frontend.py<br/>Streamlit]
    B --> C[services/bedrock_service.py<br/>BedrockService]
    B --> D[services/image_service.py<br/>ImageService + Pillow]
    B --> E[services/document_service.py<br/>DocumentService + pypdf]
    B --> F[utils/validators.py<br/>Validation + Sanitisation]
    C --> G[AWS Bedrock<br/>amazon.nova-pro-v1:0<br/>converse_stream]
    G --> C
    C --> B
    D --> B
    E --> B
```

### How to Draw This in 2 Minutes on a Whiteboard

```
Draw three horizontal bands:

┌──────────────────────────────────────────┐
│  BROWSER  →  Streamlit :8501             │  ← "The UI layer. Pure Python.
│              mod_chatbot_frontend.py     │     Streaming responses via st.empty()"
└──────────────────────┬───────────────────┘
                       │ Python calls
┌──────────────────────▼───────────────────┐
│  SERVICE LAYER                           │  ← "No Streamlit here.
│  BedrockService │ ImageService │ DocSvc  │     Independently testable.
│  utils/validators.py                     │     Handles all AI + file logic."
└──────────────────────┬───────────────────┘
                       │ boto3 converse_stream()
┌──────────────────────▼───────────────────┐
│  AWS BEDROCK                             │  ← "Serverless AI.
│  amazon.nova-pro-v1:0                   │     Pay per token.
│  us-east-1                              │     300K context."
└──────────────────────────────────────────┘
```

Say: "User sends a message. Streamlit captures it and calls BedrockService.
BedrockService builds the Converse API payload — text, image block, document block —
and calls converse_stream(). Bedrock returns a stream of token events.
Each event is yielded from the generator and rendered in real time by the frontend."

---

## 14. Resume Bullets

### Project Title
**NovaMind AI — Multimodal Generative AI Chatbot on AWS Bedrock**

### 5 Resume Bullets (choose 3-4 for your resume)

- Designed and implemented a multimodal AI chatbot using Amazon Bedrock (Nova Pro) supporting text, image, and document Q&A with real-time streaming responses via the Converse API
- Architected a layered Python service design (BedrockService, ImageService, DocumentService) decoupled from the Streamlit frontend, enabling independent testability and extensibility
- Implemented multi-layer file security: extension allowlist, magic-byte integrity checks, EXIF auto-correction, path traversal prevention, and input sanitisation across image and document upload pipelines
- Deployed on AWS EC2 with IAM instance role authentication — zero hard-coded credentials; all secrets managed through boto3's default credential chain
- Authored production-quality documentation including architecture design, deployment guide, cost analysis, model selection rationale, and troubleshooting runbook

### Technology Keywords
Python 3.14 · Streamlit · boto3 · Amazon Bedrock · Amazon Nova Pro · Converse API · Pillow · pypdf · AWS IAM · EC2 · Streaming AI

### Architecture Keywords
Layered architecture · Service layer pattern · Stateless services · Session state management · Token streaming · Multimodal content blocks · Direct document understanding

### Generative AI Keywords
Multimodal AI · Foundation models · Large language models · Streaming inference · Converse API · System prompts · Context window management · Token-level streaming

### AWS Keywords
Amazon Bedrock · Amazon Nova Pro · AWS IAM · EC2 IAM role · boto3 · Cross-region inference · AWS credential chain · us-east-1

---

## 15. Professional Language Upgrades

Replace weak statements with these professional versions:

| Weak | Professional |
|---|---|
| "I used Streamlit because it's easy" | "I selected Streamlit to accelerate development of the chat interface in pure Python, appropriate for a project whose primary value is the AI integration, not the frontend" |
| "I used Bedrock because it's AWS" | "I selected Amazon Bedrock because it provides IAM-native authentication, data residency within my AWS account, and a unified Converse API that works across multiple foundation models without vendor lock-in" |
| "I picked Nova Pro because it supports images" | "I selected Amazon Nova Pro because it natively supports text, image, and document modalities in a single Converse API call with a 300K token context window, at $0.80/M input tokens — the best balance of capability and cost for this use case" |
| "No Lambda because it was too hard" | "I did not use Lambda because Streamlit is a long-running server process that is architecturally incompatible with Lambda's stateless, short-lived execution model" |
| "I validate files so bad things don't happen" | "I implemented three-layer file validation — extension allowlist, size limits, and magic-byte integrity checks — to prevent extension-spoofing attacks and ensure file content matches the declared format" |
| "I don't store files to save money" | "Files are held in memory as bytes and sent directly to Bedrock, eliminating S3 storage costs and reducing the required IAM permission surface" |
| "The chatbot remembers things" | "Conversation context is maintained as a Converse API message history that grows with each turn and is included in every request, providing the model with full conversational context within Nova Pro's 300K token window" |
| "I added streaming so it looks faster" | "I implemented token-level streaming via boto3's `converse_stream()`, using Python generators and `st.empty()` placeholders to update the UI incrementally — reducing perceived latency from seconds to near-instant" |
| "I sanitise filenames so nothing bad happens" | "Filename sanitisation uses `Path.name` for path traversal prevention, NFKC unicode normalisation to neutralise lookalike characters, and regex-based replacement of special characters — hardening against known filename-based attack vectors" |
| "I used IAM so I don't have to store passwords" | "On EC2, an IAM instance role provides automatically rotated, short-lived credentials via the instance metadata service, eliminating the need for any stored secrets and following AWS security best practices" |
| "The app has a dark theme" | "The UI uses custom CSS injected via `st.markdown()` with a dark GitHub-style colour palette — background `#0d1117`, sidebar `#161b22` — providing a professional aesthetic consistent with developer tooling" |
| "I wrote tests" | "I implemented smoke tests validating the full service layer without AWS calls — BedrockService factory, DocumentService validation guards, ImageService magic-byte checks, and utils helpers — verifiable with Python exit code 0" |
| "I documented everything" | "I authored six production documentation files: README.md, architecture.md, deployment.md, cleanup.md, model_selection.md, and troubleshooting.md — covering architecture rationale, step-by-step deployment, cost analysis, and model comparison" |
| "Temperature controls how random it is" | "Temperature is a logit-scaling parameter that controls the entropy of the token probability distribution — lower values produce more deterministic, focused responses; higher values increase diversity and creativity" |
| "It falls back if it doesn't work" | "The BedrockService implements automatic fallback from the base model ID to the cross-region inference profile `us.amazon.nova-pro-v1:0` on `AccessDeniedException`, providing resilience against regional access configuration issues" |
| "Pillow fixes rotated photos" | "ImageService applies `ImageOps.exif_transpose()` from Pillow to correct EXIF orientation metadata — a common issue with mobile camera uploads where rotation is encoded as metadata rather than pixel rotation" |
| "I check the file header" | "Magic byte validation reads the first 12 bytes of each uploaded file and compares against known format signatures — `\xff\xd8\xff` for JPEG, `\x89PNG\r\n\x1a\n` for PNG, and a two-part RIFF+WEBP check for WebP — preventing extension-spoofing attacks" |
| "pypdf is optional" | "pypdf is an optional dependency that enables PDF text preview in the sidebar. The core PDF analysis capability — sending document bytes to Bedrock — works independently, providing graceful degradation when pypdf is absent" |
| "I made it configurable" | "Model inference parameters — temperature (0.0–1.0), max tokens (256–8192), and system prompt — are dynamically adjustable via the sidebar without restarting the application, implemented through `BedrockService.update_settings()`" |

---

## 16. What NOT to Say

### Claims to avoid

- ❌ "This is fully serverless" — The Streamlit app requires a persistent server. Bedrock is serverless; the application layer is not.
- ❌ "I implemented RAG" — There is no RAG pipeline. Say "direct document understanding via Bedrock's native document support."
- ❌ "It uses Lambda/API Gateway" — These services are not in the project.
- ❌ "It's production-ready" — It lacks authentication, HTTPS, monitoring, and rate limiting.
- ❌ "It handles unlimited file sizes" — Hard limit is 4.5 MB for documents, 5 MB for images.
- ❌ "It persists conversations" — History is session-scoped only.
- ❌ "It supports multiple concurrent users at scale" — Single Streamlit process, single-user architecture.
- ❌ "I trained the model" — You are using a pre-trained foundation model via API.
- ❌ "I fine-tuned Nova Pro" — Fine-tuning is noted as a future improvement, not implemented.

### When you don't know the answer

Use these phrases:
- "I haven't implemented that yet, but my approach would be..."
- "That is a current limitation. The trade-off I made was... and the production solution would be..."
- "I chose to scope that out for this iteration. If I were building this for production, I would..."
- "That is a great question. In my current implementation, X is handled by Y. If you are asking about Z, I would need to add..."
- "I am not certain of the exact figure, but my understanding is... I would verify that before making a decision."

### Terminology to use carefully

- **"Serverless"** — Only Bedrock is serverless in this project. Say "serverless AI inference" not "serverless application."
- **"Microservices"** — The service layer is not microservices. It is a layered monolith. Say "service layer" or "layered architecture."
- **"Real-time"** — Streaming is near-real-time. Don't say sub-millisecond or instant.
- **"Enterprise-grade"** — Accurate for the architecture patterns; not accurate for the security posture (no auth, no HTTPS).

---

## 17. Current Limitations and Future Improvements

### Current Limitations ✅ Honest

| Area | Limitation |
|---|---|
| Authentication | None — anyone with network access can use the app |
| HTTPS | HTTP only — no SSL/TLS encryption |
| History persistence | Session-scoped only — clears on browser close |
| File size | Documents max 4.5 MB, images max 5 MB |
| Concurrent users | Single Streamlit process — not designed for concurrent access |
| Monitoring | Terminal logging only — no CloudWatch |
| RAG | Not implemented — single documents only |
| Context management | No automatic truncation or summarisation |
| Error recovery | No retry logic with backoff for Bedrock throttling |
| Testing | Smoke tests only — no pytest suite, no mocking |

### Future Improvements by Priority

**Priority 1 — Security (before any public deployment)**
- Amazon Cognito authentication
- HTTPS via ALB + ACM certificate
- Bedrock Guardrails for content filtering
- Scope IAM to minimum permissions

**Priority 2 — Production readiness**
- CloudWatch structured logging and metrics
- DynamoDB persistent conversation history
- Exponential backoff for Bedrock throttling
- Automated pytest suite with boto3 mocking

**Priority 3 — Feature enhancements**
- RAG pipeline via Bedrock Knowledge Bases for multi-document retrieval
- Multi-model selector (Nova Pro / Nova Lite / Claude)
- Automatic context truncation / conversation summarisation
- Docker containerisation for ECS/Fargate deployment
- AWS CDK infrastructure-as-code

---

## 18. Pre-Interview Study Checklist

### Must understand before any interview

- [ ] What Amazon Bedrock is and how it differs from SageMaker and OpenAI API
- [ ] Amazon Nova Pro: model ID, modalities, context window, pricing
- [ ] The Converse API: messages format, system prompt, content blocks, streaming events
- [ ] How streaming works: converse_stream(), generator pattern, contentBlockDelta events
- [ ] Credential chain: env vars → ~/.aws/credentials → IAM role
- [ ] IAM: least privilege, instance roles, policies vs permissions
- [ ] Why Streamlit reruns the script and how session_state solves it
- [ ] The two-history design: bedrock_history vs chat_history and why they are separate
- [ ] Magic byte validation: what it prevents and how JPEG/PNG/WebP/PDF are checked
- [ ] Path traversal: what it is and how Path().name prevents it
- [ ] Direct document understanding vs RAG: when each is appropriate
- [ ] Temperature: what it does technically (logit scaling)
- [ ] max_tokens vs context window: the difference
- [ ] Why Lambda was NOT used (Streamlit is long-running, incompatible with Lambda)
- [ ] Why S3 was NOT used (files sent as bytes, no persistence needed)
- [ ] The WebP bug that was found and fixed during testing (minimum-length guard)
- [ ] EC2 IAM instance profile: how boto3 gets credentials automatically
- [ ] Cross-region inference profile: what us.amazon.nova-pro-v1:0 does
- [ ] Cost: what generates charges and approximately how much for a demo session
- [ ] The 10 checks in bedrock_model_access_check.py and what each verifies

### Recommended study order

1. Read `services/bedrock_service.py` completely — the `stream_response()` and `_build_content_blocks()` methods are the core of the project
2. Read `mod_chatbot_frontend.py` sections 2, 6, and 7 — session state, streaming display, and input handling
3. Read this document's "5-Minute Deep Technical Explanation" and practice saying it out loud
4. Run `python scripts/bedrock_model_access_check.py` and make sure all 10 checks pass
5. Run `streamlit run mod_chatbot_frontend.py` and demo all three modalities yourself
6. Read sections 11 and 12 — hard questions and the demo script
7. Practice the whiteboard explanation from section 13
