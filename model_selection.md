# Model Selection — NovaMind AI Multimodal Chatbot

## Selected Model

**Primary:** `amazon.nova-pro-v1:0` — Amazon Nova Pro  
**Fallback:** `us.amazon.nova-pro-v1:0` — Cross-region inference profile

---

## Model Comparison Table

| Property | Nova Pro | Nova Lite | Claude 3.5 Sonnet | Claude 3 Haiku |
|---|---|---|---|---|
| **Provider** | Amazon | Amazon | Anthropic | Anthropic |
| **Model ID** | `amazon.nova-pro-v1:0` | `amazon.nova-lite-v1:0` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | `anthropic.claude-3-haiku-20240307-v1:0` |
| **Context window** | 300K tokens | 300K tokens | 200K tokens | 200K tokens |
| **Image input** | ✅ | ✅ | ✅ | ✅ |
| **Document input** | ✅ PDF, CSV, DOCX, XLSX, TXT, HTML, MD | ✅ Same | ✅ PDF (with citations API) | ✅ |
| **Video input** | ✅ | ✅ | ❌ | ❌ |
| **Streaming** | ✅ | ✅ | ✅ | ✅ |
| **Converse API** | ✅ | ✅ | ✅ | ✅ |
| **us-east-1** | ✅ | ✅ | ✅ | ✅ |
| **Input cost** | $0.80/M tokens | $0.06/M tokens | ~$3.00/M tokens | $0.25/M tokens |
| **Output cost** | $3.20/M tokens | $0.24/M tokens | ~$15.00/M tokens | $1.25/M tokens |
| **Fine-tuning** | ✅ | ✅ | ❌ | ❌ |
| **AWS-native** | ✅ | ✅ | ❌ (Anthropic) | ❌ (Anthropic) |
| **Benchmark vs Nova Pro** | — | Weaker | Stronger on 9/9 | Weaker |
| **Best for** | Balanced multimodal portfolio | High-volume, cost-sensitive | Complex reasoning tasks | Fast, cheap Q&A |

---

## Why Amazon Nova Pro Was Chosen

### 1. Already working in your account
Nova Pro is the model used in the original `chatbot_backend.py`. Model access is already granted, credentials are already configured, and the model ID is proven to work with your AWS setup. No onboarding friction.

### 2. Full multimodal capability
Nova Pro accepts text, images (JPEG/PNG/GIF/WebP), documents (PDF/DOCX/CSV/etc.), and video in a single request through the Converse API. This covers all three use cases in this project (text, image, document) with a single model and a single API.

### 3. 300K token context window
300,000 tokens supports very long conversations, large PDFs, and extensive chat history without truncation issues during a demo. This is a strong portfolio talking point.

### 4. Direct document understanding — no RAG needed
Nova Pro processes PDFs up to 4.5 MB as raw bytes in the Converse API. This eliminates the need for a chunking pipeline, vector store, or embedding model for single-document Q&A — which is the primary portfolio use case. The architecture is simpler, faster, and cheaper.

### 5. Cost-effective
At $0.80/M input and $3.20/M output, Nova Pro is dramatically cheaper than Claude 3.5 Sonnet (which is ~3.75× more expensive on input and ~4.7× more on output). For a portfolio demo with moderate usage, Nova Pro keeps costs negligible.

### 6. AWS-native signal
Using an Amazon-built model on Amazon Bedrock sends a stronger "AWS engineer" signal than using an Anthropic or Meta model. For an interview focused on AWS Generative AI, this matters.

### 7. Fine-tuning supported
Nova Pro supports fine-tuning via Amazon Bedrock and SageMaker AI. This is a valuable portfolio extension point — you can demonstrate domain adaptation without changing the application code.

### 8. Inference profile resilience
The cross-region inference profile `us.amazon.nova-pro-v1:0` automatically distributes traffic across multiple US regions, providing resilience against regional capacity issues. The application falls back to this profile automatically on `AccessDeniedException`.

---

## Why Claude 3.5 Sonnet Was NOT Chosen

Claude 3.5 Sonnet outperforms Nova Pro on most language benchmarks. However, for this project:

- It costs 3–5× more per token
- It has a weaker "AWS-native" portfolio story
- Nova Pro is sufficient for the demo use cases (text chat, image analysis, document Q&A)
- Nova Pro already works in the account

Claude 3.5 Sonnet would be the right choice if:
- Raw benchmark performance is the primary concern
- Budget is not a constraint
- The use case involves complex multi-step reasoning over long documents

---

## Why Nova Lite Was NOT Chosen

Nova Lite is significantly cheaper than Nova Pro ($0.06/M vs $0.80/M input) and supports the same modalities. For a production high-volume application, Lite would be worth evaluating.

For a portfolio project, Nova Pro is the better choice because:
- Better reasoning quality and coherence for demos
- Portfolio projects benefit from showing the more capable model
- The cost difference is negligible at demo-scale usage

---

## Model ID Reference

```python
# Direct model ID (requires model access in the specific region)
PRIMARY_MODEL = "amazon.nova-pro-v1:0"

# Cross-region inference profile (works from any US region,
# distributes load, automatic fallback on capacity issues)
INFERENCE_PROFILE = "us.amazon.nova-pro-v1:0"
```

The application tries `PRIMARY_MODEL` first and automatically switches to `INFERENCE_PROFILE` on `AccessDeniedException`.

---

## Future Model Options

As Amazon Bedrock continues to evolve, these models are worth evaluating:

| Model | Notes |
|---|---|
| `amazon.nova-premier-v1:0` | Most capable Nova model — 1M context, available us-east-1 only |
| `amazon.nova-2-lite-v1:0` | Nova 2 generation — enhanced capabilities, 1M context |
| `anthropic.claude-sonnet-4-*` | Best benchmark performance if cost is not a concern |
| `amazon.nova-sonic-v1:0` | Add voice input/output capability |
