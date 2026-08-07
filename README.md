# 🤖 NovaMind AI — Multimodal Chatbot powered by Amazon Bedrock

A production-grade, portfolio-level multimodal AI chatbot that supports **text conversations**, **image analysis**, and **document Q&A** — all powered by **Amazon Nova Pro** on **AWS Bedrock**.

Built with Python, Streamlit, and the AWS SDK (boto3). Designed to demonstrate real-world Generative AI engineering skills on AWS.

---

## ✨ Features

| Capability | Details |
|---|---|
| 💬 **Text Chat** | Multi-turn conversations with full context memory (300K token window) |
| 🖼️ **Image Analysis** | Upload JPEG, PNG, GIF, WebP — ask questions, extract text, describe scenes |
| 📄 **Document Q&A** | Upload PDF, DOCX, CSV, TXT, MD, HTML — summarise, extract, reason |
| 🌊 **Streaming** | Token-by-token streaming with typing cursor (ChatGPT-style) |
| 🎛️ **Live Controls** | Temperature, max tokens, system prompt — all adjustable mid-conversation |
| ⬇️ **Export** | Download full conversation transcript as plain text |
| 🛡️ **Validation** | File size, extension, MIME type, magic-byte integrity checks |
| 🔄 **Auto-fallback** | Automatic retry with cross-region inference profile on access errors |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│            mod_chatbot_frontend.py                   │
│         Streamlit  ·  ChatGPT-style UI               │
│   File upload · Streaming · Settings sidebar         │
└──────────────────────┬──────────────────────────────┘
                       │ Python function calls
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
 services/        services/         services/
 bedrock_         image_            document_
 service.py       service.py        service.py
        │
        │ boto3  converse_stream()
        ▼
 ┌─────────────────────────────────┐
 │     AWS Bedrock                  │
 │  amazon.nova-pro-v1:0            │
 │  Region: us-east-1               │
 │  Converse API (streaming)        │
 └─────────────────────────────────┘
```

See [architecture.md](architecture.md) for the full design document.

---

## 🗂️ Project Structure

```
Chatbot_text_image/
│
├── mod_chatbot_frontend.py          ← NEW: Main multimodal Streamlit app
│
├── services/                        ← NEW: Service layer (UI-agnostic)
│   ├── __init__.py
│   ├── bedrock_service.py           ← Bedrock Converse API, streaming
│   ├── document_service.py          ← PDF/doc validation & processing
│   └── image_service.py             ← Image validation & Pillow processing
│
├── utils/                           ← NEW: Shared utilities
│   ├── __init__.py
│   └── validators.py                ← File dispatch, sanitisation, export
│
├── scripts/                         ← NEW: Diagnostic tools
│   └── bedrock_model_access_check.py ← AWS/Bedrock environment checker
│
├── docs/                            ← NEW: Documentation folder
│
├── .env.example                     ← NEW: Environment variable template
├── requirements_new.txt             ← NEW: Clean pinned requirements
├── README.md                        ← NEW: This file
├── architecture.md                  ← NEW: Architecture deep-dive
├── deployment.md                    ← NEW: Step-by-step deployment guide
├── cleanup.md                       ← NEW: Cost & resource cleanup guide
├── model_selection.md               ← NEW: Model comparison & rationale
├── troubleshooting.md               ← NEW: Common issues & fixes
│
│── chatbot_backend.py               ← PRESERVED: Original LangChain backend
├── chatbot_frontend.py              ← PRESERVED: Original simple Streamlit UI
├── chatbot_frontend2.py             ← PRESERVED: Enhanced Streamlit UI
├── chatbot_backend_intermediate.py  ← PRESERVED: DeepSeek model test
└── requirements.txt                 ← PRESERVED: Original frozen requirements
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- AWS CLI configured (`aws configure`) with Bedrock access
- Amazon Nova Pro model enabled in AWS Bedrock console

### 1. Clone and navigate

```powershell
# [PowerShell]
cd "E:\GenAi-Project-Udemy\Code_15042025\Chatbot_text_image"
```

### 2. Activate your virtual environment

```powershell
# [PowerShell]
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
# [PowerShell]
pip install -r requirements_new.txt
```

### 4. Verify AWS and Bedrock access

```powershell
# [PowerShell]
python scripts/bedrock_model_access_check.py
```

All 10 checks should pass. If any fail, see [troubleshooting.md](troubleshooting.md).

### 5. Run the multimodal chatbot

```powershell
# [PowerShell]
streamlit run mod_chatbot_frontend.py
```

Open your browser at: **http://localhost:8501**

---

## 🧠 AI Model

**Primary:** `amazon.nova-pro-v1:0` — Amazon Nova Pro

| Property | Value |
|---|---|
| Provider | Amazon |
| Context window | 300,000 tokens |
| Image input | ✅ JPEG, PNG, GIF, WebP |
| Document input | ✅ PDF, CSV, DOCX, XLSX, TXT, HTML, MD |
| Streaming | ✅ ConverseStream API |
| Region | us-east-1 (cross-region inference available) |
| Cost | $0.80 / 1M input tokens · $3.20 / 1M output tokens |

**Fallback:** `us.amazon.nova-pro-v1:0` (cross-region inference profile) — automatically used if the base model ID returns an access error.

See [model_selection.md](model_selection.md) for the full model comparison.

---

## ☁️ AWS Services Used

| Service | Purpose |
|---|---|
| **Amazon Bedrock** | Serverless AI inference — Nova Pro model |
| **AWS IAM** | Least-privilege credentials for Bedrock access |
| **AWS STS** | Credential verification in diagnostic script |

> **Architecture note:** This project intentionally does not use Lambda, API Gateway, S3, or DynamoDB. Streamlit is a long-running server process — wrapping it in Lambda would be architecturally incorrect and add unnecessary cost. The AI inference itself is fully serverless via Bedrock. See [architecture.md](architecture.md) for the reasoning.

---

## 🖼️ Supported File Types

### Images
| Format | Extension | Max Size |
|---|---|---|
| JPEG | .jpg, .jpeg | 5 MB |
| PNG | .png | 5 MB |
| GIF | .gif | 5 MB |
| WebP | .webp | 5 MB |

### Documents
| Format | Extension | Max Size |
|---|---|---|
| PDF | .pdf | 4.5 MB |
| Plain text | .txt | 4.5 MB |
| Markdown | .md | 4.5 MB |
| HTML | .html, .htm | 4.5 MB |
| CSV | .csv | 4.5 MB |
| Word | .doc, .docx | 4.5 MB |
| Excel | .xls, .xlsx | 4.5 MB |

---

## 🔐 Security

- No AWS credentials are hard-coded anywhere in the source code
- Credentials are loaded from the AWS default profile (`~/.aws/credentials`) or environment variables
- On EC2, use an IAM Instance Role — no credentials needed at all
- `.env` is in `.gitignore` — never committed
- All uploaded files are validated for size, extension, and magic bytes before processing
- Files are sent directly to Bedrock as bytes — never written to disk permanently
- Input is sanitised before sending to the model

See the [Security Checklist](#-security-checklist) below.

---

## 💰 Cost Awareness

Running this project generates AWS charges from Amazon Bedrock only:

| Component | Estimated Cost |
|---|---|
| Nova Pro input | $0.80 per million tokens |
| Nova Pro output | $3.20 per million tokens |
| Typical text Q&A turn | ~$0.001 – $0.005 |
| Image analysis turn | ~$0.005 – $0.015 |
| PDF Q&A turn (10 pages) | ~$0.010 – $0.030 |

There are **no always-on infrastructure charges** — Bedrock is pay-per-request. You only pay when the app is actively being used.

See [cleanup.md](cleanup.md) for full cost details and teardown instructions.

---

## 🌐 Deployment

The app can be deployed on **AWS EC2** (Ubuntu) for public access.

Quick summary:
1. Launch EC2 `t3.micro` (Ubuntu 24.04 LTS)
2. Open port 8501 in the security group
3. Clone the repo, create venv, install requirements
4. Attach an IAM role with `AmazonBedrockFullAccess` (no credentials needed)
5. Run with `nohup streamlit run mod_chatbot_frontend.py --server.address 0.0.0.0 &`

See [deployment.md](deployment.md) for exact step-by-step commands.

---

## 🔧 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region for Bedrock calls |
| `BEDROCK_MODEL_ID` | `amazon.nova-pro-v1:0` | Bedrock model ID |
| `BEDROCK_SYSTEM_PROMPT` | Built-in NovaMind persona | Assistant personality |

Copy `.env.example` to `.env` to customise. See `.env.example` for all options.

---

## ✅ Security Checklist

- [x] No hard-coded AWS credentials in source code
- [x] `.env` in `.gitignore`
- [x] `.env.example` has only placeholder values
- [x] File uploads validated for size, extension, and magic bytes
- [x] Path traversal protection in filename sanitisation
- [x] User input sanitised before sending to model
- [x] Files sent as bytes — never permanently stored
- [x] IAM role recommended over access keys for EC2
- [x] Bedrock is the only billable service (no unintended resource creation)

---

## 🧪 Running the Diagnostic Script

```powershell
# [PowerShell] — run from project root with venv activated
python scripts/bedrock_model_access_check.py
```

Checks performed:
1. Python version ≥ 3.9
2. Required packages installed
3. AWS credentials valid
4. AWS region supports Nova Pro
5. Bedrock service reachable
6. Nova / Claude model availability
7. Live text inference (Nova Pro)
8. Image / vision capability
9. Document / PDF capability
10. Streaming (ConverseStream)

---

## 🔮 Future Improvements

- [ ] RAG pipeline with Amazon Bedrock Knowledge Bases for multi-document search
- [ ] Persistent conversation history via Amazon DynamoDB
- [ ] User authentication with Amazon Cognito
- [ ] Structured logging to Amazon CloudWatch
- [ ] Multi-model selector (switch between Nova Pro, Claude 3.5 Sonnet, etc.)
- [ ] Voice input/output via Amazon Nova Sonic
- [ ] Docker container for portable deployment
- [ ] AWS CDK infrastructure-as-code for one-command deployment
- [ ] Conversation summarisation for very long sessions

---

## 📚 Documentation

| File | Contents |
|---|---|
| [architecture.md](architecture.md) | Architecture design, data flows, component diagram |
| [deployment.md](deployment.md) | Local setup + EC2 deployment (step-by-step) |
| [cleanup.md](cleanup.md) | Cost breakdown + teardown instructions |
| [model_selection.md](model_selection.md) | Model comparison table + rationale |
| [troubleshooting.md](troubleshooting.md) | Common errors + fixes |

---

## 🎓 Original Project

This project was built on top of a Udemy course chatbot. The original files are preserved:

- `chatbot_backend.py` — original LangChain + Nova Pro backend
- `chatbot_frontend.py` — original Streamlit UI
- `chatbot_frontend2.py` — enhanced Streamlit UI with themes

You can still run the original chatbot at any time:
```powershell
streamlit run chatbot_frontend2.py
```

---

## 👤 Author

**Aamir** — AWS Generative AI / MLOps Engineer

- GitHub: [github.com/aamir490](https://github.com/aamir490)
- Project: [use-case-3 — Multimodal AI Chatbot using Amazon Bedrock, LangChain, Streamlit](https://github.com/aamir490/use-case-3--multimodal-ai-chatbot-aws-bedrock)

---

*Powered by [Amazon Nova Pro](https://docs.aws.amazon.com/nova/latest/userguide/what-is-nova.html) · [AWS Bedrock](https://aws.amazon.com/bedrock/) · [Streamlit](https://streamlit.io)*
