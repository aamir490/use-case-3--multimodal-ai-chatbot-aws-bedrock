# NovaMind AI — Multimodal AI Chatbot on Amazon Bedrock

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Python%20AI%20App-red?logo=streamlit)
![Amazon Bedrock](https://img.shields.io/badge/Amazon%20Bedrock-Multimodal%20AI-orange?logo=amazon-aws)
![boto3](https://img.shields.io/badge/boto3-AWS%20SDK-yellow?logo=amazon-aws)

**NovaMind AI** is a portfolio-focused multimodal Generative AI chatbot built with **Python, Streamlit, boto3, and Amazon Bedrock**.

It provides a single conversational interface for working with **text, images, and documents**, while supporting streaming responses, multi-turn conversation context, model selection, personas, multilingual responses, and configurable inference settings.

> 👨‍💻 **Built by Aamir**
> AWS Generative AI Engineer | Agentic AI | MLOps | DevOps

---

## 🎯 Project Overview

Users often need AI assistance with more than plain text. They may want to:

* ask a technical question,
* analyze an AWS error screenshot,
* summarize a document,
* ask follow-up questions about uploaded content,
* review or explain code.

NovaMind AI brings these workflows into one multimodal conversational application.

The application is intentionally designed as a **layered Python application rather than an unnecessarily complex distributed architecture**. Streamlit handles the UI and application workflow, while dedicated Python modules handle validation, image processing, document processing, and Amazon Bedrock integration.

### Core flow

```text
User
  ↓
Browser
  ↓
Streamlit Application
  ↓
Validation / Processing Services
  ↓
Bedrock Service
  ↓
boto3
  ↓
AWS IAM Authorization
  ↓
Amazon Bedrock
  ↓
Selected Foundation Model
  ↓
Streaming Response
  ↓
Streamlit
  ↓
User
```

---

## ✨ Key Features

| Feature                       | Description                                                          |
| ----------------------------- | -------------------------------------------------------------------- |
| 💬 **Text Chat**              | Multi-turn Generative AI conversations with streaming responses      |
| 🖼️ **Image Analysis**        | Upload supported images and ask questions about their content        |
| 📄 **Document Q&A**           | Upload supported documents and ask questions directly about them     |
| 🧠 **Multiple Models**        | Select between configured Amazon Nova and Claude model options       |
| 🌊 **Streaming Responses**    | Model responses are displayed progressively in the UI                |
| 📋 **Personas**               | Built-in system-instruction presets for different interaction styles |
| 🌐 **Multilingual Responses** | Multiple selectable response languages                               |
| ⚙️ **Inference Controls**     | Configure settings such as temperature and maximum output            |
| 💭 **Conversation Context**   | Application-managed history enables follow-up questions              |
| 📝 **Conversation Summary**   | Generate a structured summary of the conversation                    |
| ⬇️ **Transcript Export**      | Export readable conversation history                                 |
| 🔌 **Bedrock Check**          | Diagnostic functionality for checking AWS/Bedrock connectivity       |
| 📊 **Usage Awareness**        | Approximate session-level usage and cost indicators                  |
| 🔐 **Demo Sign-In**           | Demonstration authentication flow; not production authentication     |

> **Important:** The current authentication mechanism is intended for demonstration purposes. A public production deployment would require real identity management.

---

## 📸 Screenshots

### Demo Sign-In

| Sign-In Experience                                                                          | Alternate Capture                                                                                                     |
| ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| ![NovaMind AI demo login](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%20loginpage.png) | ![NovaMind AI demo login alternative](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%20loginpage%20screenshort.png) |

### Chat & Multimodal Capabilities

| Welcome Dashboard                                                                                  | Text Conversation                                                                    |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| ![NovaMind AI welcome dashboard](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%20dashboard.png) | ![NovaMind AI text answer](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%201.png) |

| Document Q&A                                                                           | Image Analysis                                                                          |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| ![NovaMind AI document Q\&A](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%202.png) | ![NovaMind AI image analysis](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%203.png) |

| Code Review Persona                                                                  | Code Explanation                                                                          |
| ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| ![NovaMind AI code review](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%205.png) | ![NovaMind AI code explanation](project-pic/NovaMind%20AI%20Multimodal%20Chatbot%204.png) |

---

# 🏗️ Current Architecture

## Architecture Diagram

![NovaMind AI Architecture](project-pic/architecture.jpg)

> **The existing architecture diagram is intentionally preserved as-is.**

The current implementation follows a **layered monolith**.

```text
Browser
   ↓
Streamlit UI / Application
   ↓
Validation & Service Layer
   ↓
boto3
   ↓
Amazon Bedrock Runtime
   ↓
Foundation Model
```

The browser communicates with the Streamlit application. The Python process—not the browser—makes AWS requests.

Inside the application, responsibilities are separated into modules for:

* validation,
* image processing,
* document processing,
* Bedrock communication,
* conversation/session management.

The application currently has **no separate React frontend or REST API backend**.

---

# 🔄 Application Request Flow

Consider a user who uploads an AWS error screenshot and asks:

> **“Why am I getting this error?”**

The request follows this flow:

```text
User
 │
 │ Upload screenshot + question
 ▼
Streamlit
 │
 ▼
Input Validation
 │
 ▼
Image Processing
 │
 ▼
bedrock_service.py
 │
 ├── System Instructions
 ├── Previous Conversation Context
 ├── Image
 ├── User Question
 └── Inference Settings
 │
 ▼
boto3
 │
 ▼
AWS IAM Authorization
 │
 ▼
Amazon Bedrock Runtime
 │
 ▼
Selected Foundation Model
 │
 ▼
Streaming Response
 │
 ▼
Streamlit
 │
 ▼
User
```

The Python application handles **validation, preparation, request construction, session state, and presentation**.

The selected foundation model handles the actual **multimodal understanding and response generation**.

---

# 📁 Repository Structure

```text
.
├── mod_chatbot_frontend.py
│   └── Streamlit UI, session workflow, uploads and controls
│
├── services/
│   ├── bedrock_service.py
│   │   └── Amazon Bedrock request and streaming integration
│   │
│   ├── image_service.py
│   │   └── Image validation and preparation
│   │
│   └── document_service.py
│       └── Document validation and preview processing
│
├── utils/
│   └── validators.py
│       └── Validation, sanitization and utility logic
│
├── scripts/
│   └── bedrock_model_access_check.py
│       └── AWS / Bedrock diagnostic checks
│
├── project-pic/
│   └── Architecture diagram and project screenshots
│
├── architecture.md
├── deployment.md
├── troubleshooting.md
├── model_selection.md
└── interview.md
```

---

# 🧩 Technology Stack

## Application Technologies

| Technology             | Role                                         |
| ---------------------- | -------------------------------------------- |
| **Python**             | Core application language                    |
| **Streamlit**          | UI and application server                    |
| **boto3 / botocore**   | Python AWS SDK and AWS communication         |
| **Pillow**             | Image processing                             |
| **pypdf**              | Local PDF-related processing/preview support |
| **Python dataclasses** | Structured internal application data         |

## AWS Services

| AWS Service                | Current Role                                            |
| -------------------------- | ------------------------------------------------------- |
| **Amazon Bedrock Runtime** | Multimodal foundation-model inference                   |
| **Amazon Bedrock**         | Model-related AWS functionality                         |
| **AWS IAM**                | Authorization for AWS API calls                         |
| **AWS STS**                | Identity-related diagnostics                            |
| **Amazon EC2**             | Documented hosting target for the Streamlit application |

The current core architecture does **not require** S3, Lambda, API Gateway, DynamoDB, Cognito, Kubernetes, or a vector database.

---

# 🤖 Amazon Bedrock Integration

NovaMind uses **boto3** to communicate with Amazon Bedrock Runtime.

Conceptually:

```text
NovaMind
   ↓
bedrock_service.py
   ↓
boto3
   ↓
Amazon Bedrock Runtime
   ↓
Foundation Model
```

A request can contain:

```text
System Instructions
        +
Previous Conversation Context
        +
Current User Message
        +
Optional Image / Document
        +
Inference Settings
```

The project uses Bedrock's conversation-style APIs, including streaming for normal chat interactions.

Amazon Bedrock provides the **managed model-serving layer**. NovaMind does not download or host the foundation-model weights itself.

---

# 🧠 Model Selection

The application exposes configured model choices including:

* Amazon Nova Pro
* Amazon Nova Lite
* Claude 3.5 Sonnet

Model availability and supported capabilities depend on the configured AWS environment and Bedrock access.

The application also contains fallback behaviour around model invocation. For a production version, fallback behaviour should be made fully explicit so that the requested model, actual model used, fallback reason, and outcome are observable.

---

# 📄 Document Q&A — Direct Prompting, Not RAG

An important architecture decision is that the current project **does not use Retrieval-Augmented Generation (RAG).**

Current document flow:

```text
User uploads document
        ↓
Validation
        ↓
Document preparation
        ↓
Document included in Bedrock request
        ↓
Foundation model
        ↓
Answer
```

The current application does not implement:

```text
Chunking
   ↓
Embeddings
   ↓
Vector Database
   ↓
Semantic Retrieval
   ↓
Retrieved Context
```

Direct document prompting keeps the architecture simple for the current use case: **a user uploads a document and asks questions about that document**.

A RAG architecture would become useful if the requirement evolved toward searching across a large, persistent knowledge base or many documents.

---

# 💭 Conversation History

NovaMind maintains two forms of history.

### `chat_history`

Used primarily for:

* displaying the conversation,
* readable transcript/export functionality.

### `bedrock_history`

Used for:

* structured model messages,
* conversation context,
* attachment-aware model interactions.

Conceptually:

```text
Question 1
Answer 1
Question 2
Answer 2
Question 3
        ↓
Previous context + Question 3
        ↓
Amazon Bedrock
```

The current application manages this history in Streamlit session state.

Amazon Bedrock is therefore **not being used as a persistent conversation database**.

The current implementation also does not provide durable cross-session conversation persistence.

---

# ☁️ AWS Deployment

The repository documents **Amazon EC2** as the deployment target for the Streamlit application.

> The repository contains the EC2 deployment procedure. Deployment status should be treated separately from the documented architecture.

Conceptually:

```text
Source Code
    ↓
EC2
    ↓
Python Runtime
    ↓
Virtual Environment
    ↓
Dependencies
    ↓
Streamlit Process
    ↓
Port 8501
    ↓
Browser
```

Amazon Bedrock remains separate:

```text
EC2
 │
 │ boto3
 ▼
Amazon Bedrock
 │
 ▼
Foundation Model
```

EC2 hosts the **application**.

Bedrock provides the **managed AI inference**.

---

## Run Locally

### Requirements

* compatible Python runtime,
* AWS credentials or AWS identity with required Bedrock permissions,
* appropriate Bedrock model access,
* configured AWS region.

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements_new.txt

# Run diagnostic checks
python scripts/bedrock_model_access_check.py

# Start NovaMind
streamlit run mod_chatbot_frontend.py
```

Then open:

```text
http://localhost:8501
```

---

## Documented EC2 Deployment

```bash
git clone https://github.com/aamir490/use-case-3--multimodal-ai-chatbot-aws-bedrock.git

cd use-case-3--multimodal-ai-chatbot-aws-bedrock

python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements_new.txt

nohup streamlit run mod_chatbot_frontend.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  > nohup.out 2>&1 &
```

The current documented deployment is intentionally simple and largely manual.

A production deployment should improve process supervision, HTTPS, release automation, staging, monitoring, and rollback.

See [`deployment.md`](deployment.md) for the project's detailed deployment guide.

---

# 🔐 Security Model

Security should be understood at two different levels.

## 1. User Authentication

```text
Who is using NovaMind?
```

The current application uses **demo authentication**.

It should **not** be considered production authentication.

A production deployment should integrate a proper identity system.

## 2. AWS Authorization

```text
Is NovaMind allowed to invoke Bedrock?
```

The Python application uses boto3 with standard AWS credential mechanisms.

For an AWS-hosted deployment, role-based credentials are preferable to storing long-lived access keys in application code.

```text
Application
     ↓
AWS Identity
     ↓
IAM Policy Evaluation
     ↓
Amazon Bedrock
```

### Security principles

* Do not hardcode AWS credentials.
* Prefer role-based credentials for AWS-hosted workloads.
* Apply least-privilege IAM permissions.
* Validate uploaded content before model invocation.
* Keep application errors separate from AI-generated content.
* Use HTTPS for public production traffic.
* Add real authentication before exposing expensive AI inference publicly.
* Add usage controls and quotas for production.

---

# 💰 Cost & Usage

NovaMind's AI cost is influenced by factors such as:

```text
Model selection
      +
Input/context size
      +
Conversation history
      +
Attachments
      +
Generated output
```

The current application provides **approximate usage/cost indicators**.

These values should not be treated as guaranteed AWS billing measurements.

One important consideration is conversation growth.

Because previous model history can be sent again:

```text
Turn 1
   ↓
Turn 2 + previous context
   ↓
Turn 3 + larger context
   ↓
Turn 4 + larger context
```

request size can grow over a long conversation.

A production implementation should therefore introduce:

* context budgeting,
* sensible output limits,
* attachment limits,
* usage accounting,
* user/request quotas,
* monitoring of real Bedrock usage information where available.

---

# 📈 Scalability

Amazon Bedrock manages the **foundation-model serving layer**.

However:

> **Bedrock scaling does not automatically scale the NovaMind application.**

The application tier still includes:

```text
Streamlit
Python process
Session state
Uploads
Streaming connections
Application memory
EC2 resources
```

The correct scaling strategy is:

```text
Monitor
   ↓
Load Test
   ↓
Find Bottleneck
   ↓
Scale What Actually Needs Scaling
```

If future traffic requires multiple application instances, the current in-memory session-state design would also need to be reconsidered.

The project intentionally avoids introducing Kubernetes or other orchestration systems without a demonstrated requirement.

---

# 🧪 Testing & GenAI Evaluation

## Current State

The current repository does **not yet contain a formal automated test suite**.

The Bedrock diagnostic tooling is useful for environment checks, but diagnostics should not be treated as a replacement for automated testing.

## Production Testing Strategy

A production V2 should introduce:

### Software Testing

```text
Unit Tests
   ↓
Mocked Service Tests
   ↓
Bedrock Integration Tests
   ↓
End-to-End Tests
   ↓
Regression Tests
```

Important regression areas include:

* upload validation,
* malformed images,
* document naming,
* model selection,
* fallback behaviour,
* conversation history,
* attachment lifecycle,
* Bedrock errors,
* streaming failures.

A Python framework such as **pytest** would be a reasonable choice for implementing these tests.

### GenAI Evaluation

Traditional software tests alone cannot determine whether an AI answer is good.

NovaMind should also evaluate:

* correctness,
* relevance,
* grounding,
* hallucination,
* instruction following,
* image understanding,
* document understanding,
* prompt-injection behaviour,
* safety,
* latency,
* usage/cost.

A repeatable evaluation dataset can then be used whenever prompts, models, or inference settings change.

---

# ⚠️ Current Limitations

NovaMind is functional, but the current version still has production-readiness gaps.

Important areas include:

### Input correctness

* stricter malformed-image validation,
* consistent size/dimension validation,
* document-name/API compatibility.

### Model invocation

* clearer fallback behaviour,
* explicit tracking of requested vs actual model.

### Conversation handling

* errors should never be stored as successful assistant responses,
* context should not grow indefinitely,
* attachment lifecycle should be explicit.

### Security

* demo authentication is not production authentication,
* public production traffic requires HTTPS,
* IAM permissions should follow least privilege,
* usage controls should protect expensive inference.

### Testing

* no formal automated regression suite yet,
* no systematic GenAI quality/evaluation suite yet.

### Deployment

* current deployment is largely manual,
* no established automated release/staging/rollback workflow.

These limitations form the basis of the production roadmap.

---

# 🚀 Production-Ready V2 Roadmap

The goal is **not to add AWS services just to make the diagram larger**.

The goal is to solve real engineering problems.

## 🔴 Priority 1 — Correctness & Security

* Strengthen image/document validation.
* Fix document/API naming edge cases.
* Make model fallback explicit.
* Keep application errors out of model history.
* Add real user authentication.
* Add HTTPS.
* Apply least-privilege IAM.
* Add user/request quotas.

## 🟠 Priority 2 — Reliability & Cost

* Add bounded conversation context.
* Improve attachment lifecycle.
* Improve usage accounting.
* Add automated regression tests.
* Add GenAI evaluation.
* Add structured application logging and metrics.

## 🟡 Priority 3 — Deployment Maturity

Introduce:

```text
Code Change
    ↓
Automated Tests
    ↓
GenAI Evaluation
    ↓
Staging
    ↓
Verification
    ↓
Production
    ↓
Monitoring
    ↓
Rollback if required
```

CloudWatch can provide centralized operational logs and metrics.

## 🟢 Requirement-Driven Future Improvements

These should be introduced **only when the product requirement justifies them**.

### Persistent conversation storage

Useful if users need to return later and recover previous conversations.

### S3-backed uploads

Useful if files need durable/shared storage rather than request/session-level handling.

### RAG

Useful when the application needs retrieval across a large persistent knowledge base or many documents.

### Containers / multiple replicas

Useful when deployment consistency or measured application load requires horizontal scaling.

### Additional model/modality capabilities

Useful when there is a clear user requirement.

---

# 🏭 Production V2 Concept

```text
                       User
                         │
                         ▼
                 Real Authentication
                         │
                         ▼
                       HTTPS
                         │
                         ▼
                Streamlit Application
                         │
             ┌───────────┼────────────┐
             │           │            │
             ▼           ▼            ▼
        Validation   Context      Usage / Quotas
                     Budget
             │
             └───────────┬────────────┘
                         ▼
                  Python Services
                         │
                         ▼
                       boto3
                         │
                         ▼
                Least-Privilege IAM
                         │
                         ▼
                  Amazon Bedrock
                         │
                         ▼
                Foundation Model


Application / Operational Telemetry
                 │
                 ▼
             CloudWatch
```

This is a **future production evolution**.

It does **not replace the current architecture diagram above**.

---

# 🎯 Key Architecture Decisions

| Decision                                      | Reason                                                                               |
| --------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Streamlit instead of React + FastAPI**      | Current requirement is a focused Python AI application                               |
| **Bedrock instead of self-hosted LLM**        | Managed foundation-model inference without managing GPU/model-serving infrastructure |
| **Layered monolith instead of microservices** | Current application does not require independently deployed services                 |
| **Direct document prompting instead of RAG**  | Current use case focuses on individual uploaded documents                            |
| **Streamlit session state**                   | Sufficient for active demo/session-level conversation context                        |
| **Streaming responses**                       | Improves interactive user experience                                                 |
| **No Kubernetes**                             | Current workload does not justify orchestration complexity                           |
| **No persistent file storage**                | Current files can be handled within the request/session workflow                     |

---

# 🎤 Interview Story

A concise way to explain the project:

> **“NovaMind AI is a multimodal Generative AI chatbot built using Python, Streamlit and Amazon Bedrock. It allows users to interact with foundation models using text, images and documents through one conversational interface.**
>
> **I designed the application as a layered monolith. Streamlit handles the UI and session state, while separate Python modules handle validation, image processing, document processing and Bedrock integration. The Bedrock service uses boto3 to send the user's current input, optional attachment, system instructions and previous conversation context to the selected foundation model, and the response is streamed back to the UI.**
>
> **For document Q&A, the current version uses direct document prompting rather than RAG because the requirement is focused on individual user-uploaded documents rather than retrieval across a large persistent knowledge base. I also avoided introducing microservices or Kubernetes because the current workload doesn't justify that complexity.**
>
> **The repository documents an EC2 deployment for the Streamlit application, while Bedrock provides managed model inference. I also identified production-readiness improvements around authentication, HTTPS, least-privilege IAM, validation, context growth, usage controls, automated testing, GenAI evaluation, observability and repeatable deployment.”**

---

# 📚 Project Documentation

Detailed project documentation is available in:

* [`architecture.md`](architecture.md) — architecture, components and request flow
* [`deployment.md`](deployment.md) — deployment procedure
* [`troubleshooting.md`](troubleshooting.md) — troubleshooting guidance
* [`model_selection.md`](model_selection.md) — model-related design information
* [`interview.md`](interview.md) — interview preparation

---

# 🧭 Engineering Philosophy

NovaMind intentionally follows a simple principle:

> **Start with the simplest architecture that satisfies the requirement. Measure real limitations, then add complexity only when a clear requirement justifies it.**

That means the current project does not claim to need RAG, Kubernetes, microservices, persistent storage, or a separate API layer simply because those technologies are popular.

The production roadmap instead focuses first on:

**Correctness → Security → Reliability → Testing → GenAI Evaluation → Observability → Deployment Maturity → Measured Scaling**

---

**Built by Aamir — AWS Generative AI Engineer**





<!-- ## 🎯 Project Overview

NovaMind AI demonstrates real-world Generative AI engineering on AWS. It goes beyond a basic tutorial chatbot to showcase:

- **Multimodal AI** — text, images, and documents in a single conversation
- **AWS Bedrock Converse API** — streaming, multi-turn, model-agnostic
- **3 AI model choices** — Amazon Nova Pro, Nova Lite, Claude 3.5 Sonnet
- **Production patterns** — layered architecture, input validation, error handling, security
- **Cost awareness** — live token & USD cost tracking per session
- **Interview-ready** — full documentation, architecture diagrams, Q&A guide

> **Portfolio note:** The sign-in UI uses demo credentials stored in source code. This is not production authentication. Production deployment would use Amazon Cognito.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 **Login Page** | Demo auth with branded login UI. Production → Amazon Cognito |
| 💬 **Text Chat** | Multi-turn conversations with full context memory and streaming |
| 🖼️ **Image Analysis** | Upload JPEG, PNG, GIF, WebP — describe, extract, reason about images |
| 📄 **Document Q&A** | Upload PDF, DOCX, CSV, TXT, MD, HTML — summarise and interrogate |
| 🧠 **3 AI Models** | Nova Pro, Nova Lite, Claude 3.5 Sonnet — switchable mid-session |
| 📋 **Prompt Templates** | 5 built-in personas: Default, Code Reviewer, Data Analyst, Doc Summariser, AWS Educator |
| 🌐 **8 Languages** | English, Arabic, French, Spanish, German, Hindi, Japanese, Chinese |
| 📊 **Token Counter** | Live input/output token count and estimated USD cost per session |
| 🔌 **AWS Health Check** | One-click Bedrock connectivity test with latency measurement |
| 📝 **Conversation Summary** | AI-generated structured summary of the full conversation |
| ⬇️ **Export Transcript** | Download conversation as plain text |
| 🌊 **Streaming Responses** | Token-by-token display with typing cursor |

---

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

### Architecture Diagram

![NovaMind AI Architecture](project-pic/architecture.jpg)

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

## 🧠 AI Model — Amazon Nova Pro

| Property | Value |
|---|---|
| **Model ID** | `amazon.nova-pro-v1:0` |
| **Fallback** | `us.amazon.nova-pro-v1:0` (cross-region inference profile) |
| **Provider** | Amazon (AWS-native) |
| **Context window** | 300,000 tokens |
| **Image input** | ✅ JPEG, PNG, GIF, WebP |
| **Document input** | ✅ PDF, CSV, DOCX, XLSX, TXT, HTML, MD |
| **Streaming** | ✅ ConverseStream API |
| **Region** | us-east-1 (primary) |
| **Cost** | $0.80 / 1M input tokens · $3.20 / 1M output tokens |

**Why Nova Pro?** It is the AWS-native model, supports all three modalities (text + image + document) natively in the Converse API, has the best price/performance ratio for portfolio demos, and is already enabled by default in AWS accounts. See [model_selection.md](model_selection.md) for the full comparison against Nova Lite and Claude 3.5 Sonnet.

---

## ☁️ AWS Services Used

| Service | Used | Purpose |
|---|---|---|
| **Amazon Bedrock Runtime** | ✅ | Streaming multimodal inference (Converse + ConverseStream APIs) |
| **Amazon Bedrock** | ✅ | Model discovery and access management |
| **AWS IAM** | ✅ | Authorises Bedrock calls — instance role on EC2, no hard-coded keys |
| **AWS STS** | ✅ | Identity verification in the diagnostic script |
| **Amazon EC2** | ✅ | Hosts the Streamlit application (Ubuntu, t3.micro) |
| **Amazon S3** | ❌ | Not used — files sent as bytes directly to Bedrock |
| **AWS Lambda** | ❌ | Not used — Streamlit is a long-running process |
| **API Gateway** | ❌ | Not used — Streamlit handles its own HTTP |
| **DynamoDB** | ❌ | Not used — session-scoped history only (future improvement) |
| **Amazon Cognito** | ❌ | Not used — demo auth only (future improvement) |

> The app is intentionally minimal — no persistent storage, no API layer, no vector store. The AI inference itself is fully serverless via Bedrock. See [architecture.md](architecture.md) for the complete design rationale.

## 🚀 Run Locally (Windows)

**Requirements:** Python 3.9+, AWS credentials with Bedrock access, Nova Pro model enabled in Bedrock Console, region `us-east-1`.

```powershell
# [PowerShell] — activate venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements_new.txt

# Verify AWS + Bedrock access (10 checks)
python scripts/bedrock_model_access_check.py

# Run the app
streamlit run mod_chatbot_frontend.py
```

Open **http://localhost:8501** — login with `demo / demo1234`

Credentials use the standard boto3 chain: environment variables → `~/.aws/credentials` → EC2 IAM role. Never put access keys in source code.

| Variable | Default | Purpose |
|---|---|---|
| `AWS_DEFAULT_REGION` | `us-east-1` | Bedrock Runtime region |
| `BEDROCK_MODEL_ID` | `amazon.nova-pro-v1:0` | Default model |
| `BEDROCK_SYSTEM_PROMPT` | Built-in NovaMind prompt | Assistant persona |

Copy `.env.example` to `.env` to customise any of these values.

## 🌐 Deploy to AWS EC2

```bash
# [EC2 — Ubuntu]
git clone https://github.com/aamir490/use-case-3--multimodal-ai-chatbot-aws-bedrock.git
cd use-case-3--multimodal-ai-chatbot-aws-bedrock
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements_new.txt
nohup streamlit run mod_chatbot_frontend.py \
  --server.port 8501 --server.address 0.0.0.0 > nohup.out 2>&1 &
```

Open `http://<ec2-public-ip>:8501`. Attach an IAM role with `AmazonBedrockFullAccess` — no credentials needed on the server. See [deployment.md](deployment.md) for full step-by-step instructions.

## 💰 Cost Estimate

| Component | Cost |
|---|---|
| Amazon Bedrock — Nova Pro input | $0.80 / 1M tokens |
| Amazon Bedrock — Nova Pro output | $3.20 / 1M tokens |
| Typical Q&A turn | ~$0.001 – $0.005 |
| 30-min demo session (20 turns) | ~$0.05 – $0.20 |
| EC2 t3.micro | ~$8/month (free tier eligible) |

**No charges when idle** — Bedrock is pay-per-request only. See [cleanup.md](cleanup.md) for teardown instructions.

## 🔐 Security

- ✅ No hard-coded AWS credentials anywhere in source code
- ✅ Credential chain: env vars → `~/.aws/credentials` → EC2 IAM role
- ✅ `.env` in `.gitignore` — never committed
- ✅ File upload validation: size + extension + magic byte integrity checks
- ✅ Path traversal protection in `sanitize_filename()`
- ✅ User input sanitised before sending to model
- ✅ Files sent as bytes — never written to disk permanently
- ✅ IAM role recommended for EC2 (no credentials stored on server)
- ⚠️ Demo auth only — replace with Amazon Cognito before public deployment
- ⚠️ HTTP only — add HTTPS via ALB + ACM for production

## 🔮 Future Improvements

| Priority | Improvement |
|---|---|
| 🔴 **P1** | Amazon Cognito authentication — replace demo login |
| 🔴 **P1** | HTTPS via AWS ALB + ACM certificate |
| 🔴 **P1** | CloudWatch structured logging and metrics |
| 🟡 **P2** | DynamoDB persistent conversation history per user |
| 🟡 **P2** | RAG pipeline via Bedrock Knowledge Bases for multi-document search |
| 🟡 **P2** | Exact token count from Bedrock response metadata |
| 🟢 **P3** | Docker + ECS Fargate containerised deployment |
| 🟢 **P3** | Multi-file attachment support per message |
| 🟢 **P3** | AWS CDK infrastructure-as-code |
| 🟢 **P3** | Bedrock Guardrails for content safety filtering |
| 🟢 **P3** | Voice input/output via Amazon Nova Sonic |

## Interview preparation

[interview.md](interview.md) contains five ready-to-say project stories, AWS service explanations, design trade-offs, and interview questions with answers.

## More documentation

- [architecture.md](architecture.md) — components, request flows, data lifecycle, security, and production evolution.
- [interview.md](interview.md) — interview storytelling and Q&A.
- [deployment.md](deployment.md), [troubleshooting.md](troubleshooting.md), and [model_selection.md](model_selection.md) — supporting guides. -->
