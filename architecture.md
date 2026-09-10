# Architecture — NovaMind AI

## Scope

NovaMind AI is a **single active Streamlit-session** multimodal assistant. A user can send text, attach one image, or attach one document and ask a question about it. The current repository does not provide durable user identity, persistent history, a document corpus, asynchronous jobs, or an API for other systems.

## Current architecture

~~~text
┌─────────────────────┐
│ Browser             │
└─────────┬───────────┘
          │ HTTP / Streamlit session
┌─────────▼─────────────────────────────────────────────────────┐
│ mod_chatbot_frontend.py                                        │
│ demo login · controls · upload UI · chat display · streaming   │
│ chat_history (UI) · bedrock_history (API payload/context)      │
└─────────┬─────────────────────────────────────────────────────┘
          │ Python calls / in-memory content
┌─────────▼─────────────────────────────────────────────────────┐
│ services + utilities                                           │
│ validators → routing/sanitisation                              │
│ image service → checks/orientation/thumbnail                   │
│ document service → checks/preview                              │
│ Bedrock service → Converse message construction/streaming      │
└─────────┬─────────────────────────────────────────────────────┘
          │ boto3: bedrock-runtime Converse / ConverseStream
┌─────────▼─────────────────────────────────────────────────────┐
│ AWS: Amazon Bedrock Runtime → selected foundation model        │
│ IAM → permission; STS + Bedrock control plane → diagnostics    │
└───────────────────────────────────────────────────────────────┘
~~~

## Components

| Component | Responsibility | Key detail |
| --- | --- | --- |
| mod_chatbot_frontend.py | UI, session state, upload workflow, stream rendering. | Uses Streamlit session state; data disappears when the session/app restarts. |
| BedrockService | Builds content blocks and calls Bedrock. | ConverseStream yields text deltas for the UI. |
| ImageService | Validates image input and creates thumbnails. | JPEG/PNG/GIF/WebP; 5 MB limit. |
| DocumentService | Validates documents and creates previews. | PDF/TXT/MD/HTML/CSV/DOC/DOCX/XLS/XLSX; 4.5 MB limit. |
| validators.py | Upload routing, filename/input cleaning, export helper. | Sanitises filename/path components. |
| Diagnostic script | Tests Python/AWS/Bedrock readiness. | Uses STS and Bedrock APIs outside normal chat flow. |

## Request flows

### Text

~~~text
Prompt → trim/cap input → prepare service with selected controls
       → prior API history + text content block → ConverseStream
       → Streamlit updates one placeholder per text delta
       → completed turns recorded in display and API histories
~~~

The selected model, temperature, response limit, persona/custom system prompt, and language instruction are applied to the service.

### Image and document

~~~text
Upload → extension/size/signature validation → UI preview → pending attachment
Question + attachment bytes → Bedrock content block + question text → streamed answer
~~~

Images receive thumbnail generation and EXIF orientation handling. PDFs/text files can receive a preview. The attachment source bytes—not only the preview—are passed to the model. This is **direct single-document Q&A**, not RAG: no chunks, embeddings, vector database, retrieval, or citation pipeline exists.

### Other actions

- **Summary:** makes a fresh summarisation request over a copied API history.
- **Export:** creates a plain-text transcript from UI history in memory.
- **Connection check:** sends a small non-streaming ping request; it can incur model usage.

## State and data lifecycle

| Data | Location | Lifetime | Persistent? |
| --- | --- | --- | --- |
| Controls and login flag | Streamlit session state | Browser session | No |
| UI transcript | chat_history | Browser session | No |
| Bedrock API context and attachment bytes | bedrock_history | Browser session | No |
| Pending image/document | Session state | Until remove/send | No |
| Downloaded transcript | User device | User-controlled | Not stored by app |

This low-storage approach keeps the demo simple but prevents shared/recoverable/searchable conversations.

## Models and fallback

| UI choice | Model ID |
| --- | --- |
| Amazon Nova Pro | amazon.nova-pro-v1:0 |
| Amazon Nova Lite | amazon.nova-lite-v1:0 |
| Claude 3.5 Sonnet | anthropic.claude-3-5-sonnet-20241022-v2:0 |

The service default is Nova Pro in us-east-1. If its initial call gets AccessDeniedException, it retries with us.amazon.nova-pro-v1:0, a Nova Pro cross-region inference profile. A production version should configure fallbacks per selected model and region so model substitution is always intentional.

## Security and cost

Current safeguards: default AWS credential chain (no credentials hard-coded in the service), filename sanitisation, upload size/extension/signature checks, and in-memory attachment processing.

Production work still required: replace demo login with Cognito/OIDC, add TLS, least-privilege roles, Secrets Manager, WAF/rate limits, audit logging, retention rules, guardrails/content safety, prompt-injection defences, encrypted object storage/scanning, and data classification.

The on-screen token/cost counter is an approximation based on character count. For operational cost control, capture Bedrock response usage metadata, model ID, latency, errors, request size, and tenant/user identifiers where appropriate.

## Production evolution

~~~text
Internet → CloudFront/WAF → ALB → ECS/Fargate (containerised Streamlit)
                                      ├─ Cognito (identity)
                                      ├─ Bedrock Runtime (inference)
                                      ├─ S3 + scanning (uploads)
                                      ├─ DynamoDB/Aurora (history and metadata)
                                      ├─ Knowledge Base/vector store (RAG, if needed)
                                      └─ CloudWatch + tracing (operations)
~~~

Use direct attachments for a small single-file question. Add RAG when the requirement becomes a large, durable, filterable document collection with retrieval and citations.

## Design trade-offs

| Decision | Why it fits now | Change when… |
| --- | --- | --- |
| Streamlit monolith | Fast interactive prototype, small code surface. | APIs, high availability, or independent services are needed. |
| Direct document bytes | Simple one-file Q&A; no retrieval failure. | Documents are many/large or require citations. |
| Session memory | Low complexity and no app-managed persistence. | History, compliance, sharing, or scale is required. |
| Bedrock managed models | No GPU/model-hosting operations. | Add routing/evaluations, not necessarily self-hosting. |

For a spoken walkthrough and interview Q&A, see [interview.md](interview.md).
