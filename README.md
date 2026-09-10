# NovaMind AI — Multimodal Chatbot on Amazon Bedrock

NovaMind AI is a Streamlit application for chatting with a foundation model, asking questions about an uploaded image, or analysing one uploaded document in the same conversation. It calls Amazon Bedrock with Python and uses the Converse and ConverseStream APIs.

> **Portfolio note:** the sign-in UI is a demo only. Its sample credentials are in source code and are not production authentication.

## What it can do

- Multi-turn text chat for the active browser session, with streamed responses.
- Image analysis for JPEG, PNG, GIF, and WebP files up to 5 MB.
- Direct Q&A over one PDF, TXT, Markdown, HTML, CSV, DOC/DOCX, or XLS/XLSX file up to 4.5 MB.
- Select Nova Pro, Nova Lite, or Claude 3.5 Sonnet; tune temperature and maximum output tokens.
- Choose a persona, edit the system prompt, and request responses in eight languages.
- Preview attachments, summarise the conversation, download a text transcript, clear the session, and check Bedrock connectivity.
- Show an **estimated** session token/cost total. It is based on text length, not authoritative Bedrock usage metadata.

## Screenshots

### Demo sign-in

| Sign-in experience | Alternate capture |
| --- | --- |
| ![NovaMind AI demo login](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%20loginpage.png) | ![NovaMind AI demo login alternative](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%20loginpage%20screenshort.png) |

### Chat and capabilities

| Welcome dashboard | Text conversation |
| --- | --- |
| ![NovaMind AI welcome dashboard](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%20dashboard.png) | ![NovaMind AI text answer](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%201.png) |

| Document Q&A | Image analysis |
| --- | --- |
| ![NovaMind AI document Q&A](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%202.png) | ![NovaMind AI image analysis](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%203.png) |

| Code-review persona | Code explanation |
| --- | --- |
| ![NovaMind AI code review](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%205.png) | ![NovaMind AI code explanation](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%204.png) |

## Architecture at a glance

~~~text
Browser → Streamlit UI → validation/service layer → boto3 → Amazon Bedrock
                   ↑              ↓
           session histories   attachment bytes
~~~

The UI uses separate histories: chat_history stores lightweight information for display/export, while bedrock_history stores Converse API messages that may include binary attachment bytes. The repository does not persist them. See [architecture.md](architecture.md) for the complete design.

## Repository map

~~~text
mod_chatbot_frontend.py       Streamlit UI, session workflow, and controls
services/bedrock_service.py   Bedrock Converse/ConverseStream integration
services/image_service.py     Image validation, orientation, thumbnails
services/document_service.py  Document validation and previews
utils/validators.py           Dispatch, sanitisation, transcript utility
scripts/bedrock_model_access_check.py  AWS/Bedrock diagnostic
project-pic/                  Screenshots shown above
~~~

## Services and libraries

| Component | Purpose |
| --- | --- |
| Amazon Bedrock Runtime | Runs model inference through Converse and ConverseStream. |
| Amazon Bedrock | Model discovery/access context for the diagnostic tool. |
| AWS IAM | Authorises the caller to invoke Bedrock. |
| AWS STS | Verifies the active AWS identity in the diagnostic tool. |
| Streamlit | Browser UI, uploads, download, and per-session state. |
| boto3 | Python AWS SDK. |
| Pillow / pypdf | Image handling and PDF preview extraction. |

The current app intentionally has no database, object storage, API Gateway, Lambda, or vector store. This keeps a focused, single-session prototype simple; it is not a production claim that those services are unnecessary.

## Run locally

Requirements: Python 3.9+, AWS credentials with Bedrock Runtime access, Bedrock model access enabled, and a supported region (the code defaults to us-east-1).

~~~powershell
pip install -r requirements_new.txt
python scripts/bedrock_model_access_check.py
streamlit run mod_chatbot_frontend.py
~~~

Open http://localhost:8501. Credentials come from the standard AWS provider chain: environment variables, a local AWS profile, or an attached IAM role. Never put access keys in source code.

| Variable | Default | Purpose |
| --- | --- | --- |
| AWS_DEFAULT_REGION | us-east-1 | Bedrock Runtime region. |
| BEDROCK_MODEL_ID | amazon.nova-pro-v1:0 | Service default model. |
| BEDROCK_SYSTEM_PROMPT | Built-in NovaMind prompt | Service default instruction. |

## Security and operating boundaries

- Uploads are checked for extension, size, and basic file signatures; filenames are sanitised.
- Images are opened for thumbnail/orientation handling; documents receive lightweight integrity checks and previews where possible.
- Attachment bytes live in session memory and are sent to Bedrock for the request; this code does not create permanent storage for them.
- Generated output is Markdown from a model, not verified advice.
- Replace demo login with Cognito/OIDC, remove hard-coded samples, and enforce HTTPS before public deployment.
- A Nova Pro cross-region fallback is attempted on an initial AccessDeniedException; verify the model/profile permissions for the deployment region.

## Make it more powerful

1. Add Cognito/OIDC, least-privilege IAM roles, HTTPS, WAF/rate limits, and central secret management.
2. Containerise Streamlit behind an ALB; add health checks, CloudWatch telemetry, and structured error logging.
3. Persist conversations/metadata in DynamoDB or Aurora; apply retention and deletion policies.
4. Place large uploads in encrypted S3, scan them, and use asynchronous processing.
5. Add RAG for a multi-document corpus: ingestion, chunking, embeddings, metadata filtering, retrieval, citations, and evaluation.
6. Capture exact Bedrock usage metadata, enforce per-user quotas, and route models by quality/cost needs.
7. Add tests, content safety/guardrails, prompt-injection protections, accessibility checks, and load tests.

## Interview preparation

[interview.md](interview.md) contains five ready-to-say project stories, AWS service explanations, design trade-offs, and interview questions with answers.

## More documentation

- [architecture.md](architecture.md) — components, request flows, data lifecycle, security, and production evolution.
- [interview.md](interview.md) — interview storytelling and Q&A.
- [deployment.md](deployment.md), [troubleshooting.md](troubleshooting.md), and [model_selection.md](model_selection.md) — supporting guides.
