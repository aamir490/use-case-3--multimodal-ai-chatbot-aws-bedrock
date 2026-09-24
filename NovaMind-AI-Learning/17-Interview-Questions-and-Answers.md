# 17 — NovaMind AI Interview Questions & Answers

## Question

> **Create 20 realistic interview questions and answers based on my NovaMind AI project. Show me what an interviewer may ask, what they are trying to check, how I should think about the question, a strong natural answer, and possible follow-up questions. Keep the answers based on my actual project and clearly separate the current implementation from production V2 improvements.**

This file is the final stage of the NovaMind learning path. The goal is not to memorize 20 scripts word-for-word. Learn the **idea and flow** behind each answer so you can speak naturally.

---

# 1. Tell me about your NovaMind AI project.

### What is the interviewer checking?

They want to know whether you can explain your own project clearly before they go deeper.

### How should I think?

Use:

**Problem → Solution → Architecture → Key feature → Current maturity**

### Strong interview answer

> **“NovaMind AI is a multimodal Generative AI chatbot that I built using Python, Streamlit and Amazon Bedrock. The main goal was to create one conversational interface where users can ask normal text questions and also upload images or documents—for example, an AWS error screenshot—and ask the AI to explain it.**
>
> **I designed it as a layered monolith. Streamlit handles the UI and session state, while separate Python modules handle validation, image processing, document processing and Bedrock integration. The application uses boto3 to send the user's input, system instructions and previous conversation context to a selected foundation model through Amazon Bedrock, and the response is streamed back to the UI.**
>
> **The current version is a portfolio/demo-oriented implementation. I have also identified the changes needed for a production V2, such as stronger authentication, stricter validation, bounded conversation context, better usage tracking, automated testing, AI evaluation and production observability.”**

That description matches the actual project scope and architecture.  

### Possible follow-ups

> Why Bedrock?
> Why Streamlit?
> What do you mean by multimodal?
> Walk me through the architecture.

---

# 2. What problem does NovaMind AI solve?

### What is the interviewer checking?

Whether you understand the **business/use-case problem**, rather than only technologies.

### How should I think?

Don't start with:

> “I wanted to use Bedrock.”

Start with the user problem.

### Strong interview answer

> **“The problem is that users may need AI assistance with different types of technical information, not only text. For example, someone may want to understand an AWS error screenshot, summarize a report, review pasted code or ask follow-up questions about a document. NovaMind provides one conversational interface for these multimodal interactions instead of creating separate tools for each type of input.”**

The project's documented features support text, images/documents, code-related use cases and follow-up conversations. 

### Possible follow-ups

> Who are the target users?
> Why not build a normal chatbot?
> What modalities do you support?

---

# 3. Explain the architecture of NovaMind AI.

### What is the interviewer checking?

Whether you genuinely understand the components and how they connect.

### How should I think?

Visualize:

```text id="fvxg67"
User
 ↓
Browser
 ↓
Streamlit
 ↓
Python Services
 ↓
boto3
 ↓
IAM
 ↓
Amazon Bedrock
 ↓
Foundation Model
```

### Strong interview answer

> **“The current architecture is a layered monolith. The user accesses the application through a browser, and Streamlit provides both the UI and application server. Inside the Python application I separated responsibilities into validation, image processing, document processing and Bedrock integration modules.**
>
> **When AI inference is required, `bedrock_service.py` constructs the request and uses boto3 to communicate with Amazon Bedrock Runtime. AWS IAM authorizes that call, Bedrock routes the request to the selected foundation model, and the generated response is streamed back through the Python application to Streamlit and then to the user.”**

Codex explicitly classifies the current design as a layered monolith with Streamlit communicating through Python services to Bedrock. 

### Possible follow-ups

> Why layered monolith?
> Why not microservices?
> Where is conversation state stored?

---

# 4. Walk me through one complete request.

### What is the interviewer checking?

This is one of the most important questions. They want proof that you understand what happens **internally**.

### How should I think?

Use a real example.

### Strong interview answer

> **“Suppose a user uploads an AWS AccessDenied screenshot and asks why the error is happening. Streamlit receives the upload and question. The application validates the file and routes image processing through the image service. When the user submits the request, `bedrock_service.py` constructs the model request using the system instructions, previous `bedrock_history`, the image, the current question and inference settings.**
>
> **Boto3 sends that request to Amazon Bedrock Runtime. AWS evaluates the application's IAM permissions, and if authorization succeeds, the selected foundation model processes the image and text. Bedrock then returns response fragments, which the application streams progressively into the Streamlit UI. Finally, the successful conversation is added to the application-managed history.”**

This follows the actual request sequence identified by Codex. 

### Possible follow-ups

> Who actually understands the screenshot?
> What does `image_service.py` do?
> What does boto3 do?
> What happens if IAM denies the request?

---

# 5. Why did you choose Amazon Bedrock?

### What is the interviewer checking?

Your architectural reasoning.

### Strong interview answer

> **“I chose Amazon Bedrock because I wanted managed access to foundation models without managing model weights, GPU infrastructure or the model-serving runtime myself. My application can focus on the multimodal workflow, conversation management and AWS integration, while Bedrock manages the foundation-model inference layer.**
>
> **The trade-off is that I depend on the models, capabilities, quotas and pricing available through the Bedrock environment, but for this project's requirements that was preferable to operating my own LLM-serving infrastructure.”**

The project uses Bedrock Runtime for managed model inference rather than self-hosting the foundation models. 

### Possible follow-ups

> What is a foundation model?
> What does boto3 do?
> Bedrock vs SageMaker?
> Does Bedrock automatically scale your whole application?

---

# 6. Why did you use Streamlit instead of React and FastAPI?

### What is the interviewer checking?

Whether you understand trade-offs rather than simply following a tutorial.

### Strong interview answer

> **“The current requirement is a focused Python-based GenAI application, so Streamlit allows me to keep the interface and application logic in one Python application. I didn't currently need separate mobile clients, public REST APIs or a highly customized frontend, so introducing React plus FastAPI would add additional development, API and deployment complexity without solving an immediate requirement.**
>
> **If the application later needed multiple client applications, a highly customized frontend or independently scalable backend APIs, I would reconsider that architecture.”**

Codex confirms that the current project has no separate frontend framework or REST backend. 

### Possible follow-ups

> What are Streamlit's limitations?
> When would you introduce FastAPI?
> How would frontend and backend communicate?

---

# 7. How does multimodal processing work?

### What is the interviewer checking?

Whether you understand the difference between **processing an input** and **AI understanding**.

### Strong interview answer

> **“NovaMind supports text, images and documents. My application is responsible for validating and preparing those inputs. For images, the image service handles application-level checks and preparation; for documents, the document service handles validation, API preparation and preview-related processing.**
>
> **Those services do not perform the semantic AI understanding. The prepared multimodal content is included in the Bedrock request, and the selected foundation model performs the actual understanding and response generation.”**

The project's service boundaries and multimodal behaviour are described in Codex's file analysis and request flow.  

### Possible follow-ups

> What does Pillow do?
> What does pypdf do?
> What happens with an invalid image?
> Does your Python code understand the screenshot?

---

# 8. Is NovaMind a RAG application?

### What is the interviewer checking?

This can expose whether a candidate adds popular terminology to a project without understanding it.

### Strong interview answer

> **“No. The current NovaMind implementation is not RAG. For document Q&A, the document is sent directly as model input through Bedrock. There is no current chunking, embedding generation, vector database or retrieval pipeline.**
>
> **I intentionally wouldn't call that RAG. Direct document prompting is sufficient for the current requirement where a user uploads a document and asks questions about it. If the requirement changed to searching across a large persistent knowledge base or many documents, then I would consider a RAG architecture.”**

Codex explicitly classifies the implementation as direct document prompting rather than RAG. 

### Possible follow-ups

> What is RAG?
> When would you add it?
> What components would RAG require?
> Why not add a vector database now?

---

# 9. How does conversation history work?

### What is the interviewer checking?

Whether you understand state and how follow-up questions get context.

### Strong interview answer

> **“The application maintains two histories. `chat_history` is used for readable UI and export purposes, while `bedrock_history` contains the structured conversation context used for model requests, including attachment-related content.**
>
> **For a follow-up question, the application sends previous `bedrock_history` together with the new user message. So the apparent conversational memory is currently managed by the application.”**

Codex confirms these two histories and their different purposes. 

### Possible follow-ups

> Where is history stored?
> What happens when the session is lost?
> Why maintain two histories?
> How does this affect cost?

---

# 10. Does Amazon Bedrock remember the conversation?

### What is the interviewer checking?

Whether you understand the application/model boundary.

### Strong interview answer

> **“In my current implementation, I don't rely on Bedrock as a persistent conversation database. The Streamlit application maintains the model conversation history and resends previous context with later requests. So the model appears to remember previous turns because my application provides that context again.”**

The current application has no durable Bedrock-side conversation ID or persistent conversation database. 

### Possible follow-ups

> What happens when history becomes large?
> What if the server restarts?
> How would you persist conversations?

---

# 11. How do you secure NovaMind and its access to Bedrock?

### What is the interviewer checking?

AWS security understanding.

### How should I think?

Separate:

```text id="2cnbfj"
USER SECURITY
Who is the user?

AWS SECURITY
What can the application do?
```

### Strong interview answer

> **“I separate user authentication from AWS authorization. The current application only has demo-oriented sign-in, so I don't consider that production authentication. For a production version I would introduce real identity integration.**
>
> **For AWS access, the Python application uses boto3 with standard AWS credential mechanisms, and IAM determines whether that AWS identity is allowed to invoke Bedrock. I would use role-based credentials for AWS-hosted deployment and apply least privilege so the application receives only the Bedrock permissions it actually requires rather than broad administrative access.”**

Codex identifies standard AWS credentials/no hardcoded keys as a strength, while also identifying demo authentication and broad permission guidance as production gaps.  

### Possible follow-ups

> IAM role vs IAM user?
> Authentication vs authorization?
> What is least privilege?
> How would you troubleshoot AccessDenied?

---

# 12. How is NovaMind deployed on AWS?

### What is the interviewer checking?

Whether you understand what happens after development.

### Strong interview answer

> **“The repository documents EC2 as the hosting target, although the code review did not independently verify a currently running production deployment. The documented approach is to place the Python application on EC2, create a virtual environment, install dependencies, configure AWS access, verify model access and run the Streamlit application on port 8501.**
>
> **The current deployment is largely manual, including source updates and application restarts, so I describe it as a demo-oriented deployment rather than claiming mature CI/CD. Bedrock itself is separate—the EC2 instance runs my Streamlit/Python application, while Bedrock provides managed model inference.”**

Codex found the documented EC2/manual deployment and the lack of mature automated releases, rollback and HTTPS. 

### Possible follow-ups

> What is a virtual environment?
> Why port 8501?
> What happens after `git pull`?
> How would you improve deployment?

---

# 13. How do you troubleshoot if the UI works but AI responses fail?

### What is the interviewer checking?

Your troubleshooting process.

### Strong interview answer

> **“If the UI loads correctly, I know the browser, EC2 and Streamlit path is at least partly working, so I would focus on the downstream AI path. I would first inspect the request construction in `bedrock_service.py`, then verify which AWS identity boto3 is actually using, check credentials and IAM authorization, confirm the configured model or inference profile, and inspect the exact Bedrock exception.**
>
> **I troubleshoot layer by layer rather than immediately restarting everything or giving broad permissions.”**

### Possible follow-ups

> What if it returns AccessDenied?
> What if credentials are missing?
> What if only one model fails?
> What if streaming starts and then stops?

---

# 14. What major challenges or limitations did you identify?

### What is the interviewer checking?

Whether you understand your project's weaknesses instead of pretending it is perfect.

### Strong interview answer

> **“The code review identified several important production gaps. Input validation needs to be stricter for malformed images and document naming. Model fallback can be insufficiently transparent. Failed inference messages can enter model history as if they were valid assistant responses. Conversation context and attachments can grow without a proper context budget, which affects memory, latency and cost.**
>
> **There are also broader production gaps such as demo authentication, approximate usage accounting, no automated test suite, no systematic GenAI evaluation, and a largely manual deployment process. I treat those as a prioritized engineering roadmap rather than hiding them.”**

These are directly reflected in Codex's production-readiness findings. 

### Possible follow-ups

> Which issue would you fix first?
> How would you fix the history problem?
> What is wrong with fallback?
> What tests would you add?

---

# 15. How do you control Bedrock cost?

### What is the interviewer checking?

Whether you understand how GenAI architecture affects cost.

### Strong interview answer

> **“The current application has approximate token and cost counters, but I wouldn't claim those are exact billing measurements because the analysis found incomplete accounting, particularly around multimodal usage. Another important cost issue is conversation growth: previous `bedrock_history`, including attachments, can be resent with future requests, which can increase request size and model input usage.**
>
> **For production I would bound conversation context, enforce input and output limits, use actual usage metadata where available, associate usage with authenticated users and introduce quotas. Model selection is also relevant because different models can have different cost and capability characteristics.”**

Codex identifies both unbounded history/attachment resending and incomplete cost accounting.  

### Possible follow-ups

> What are tokens?
> Why does history increase cost?
> How do images/documents affect usage?
> How would you enforce quotas?

---

# 16. What happens if 100 or 1,000 users use NovaMind?

### What is the interviewer checking?

Whether you understand scalability without making unsupported claims.

### Strong interview answer

> **“I wouldn't claim an exact user capacity without load testing. As concurrency increases, the Streamlit application could experience pressure from active sessions, in-memory conversation state, uploads, streaming connections and application CPU or memory usage. At the same time, the number of Bedrock requests increases and service quotas or throttling can become relevant.**
>
> **Bedrock manages the model-serving layer, but it does not automatically scale my Streamlit application. I would monitor CPU, memory, latency, request volume and errors, perform load testing, identify the actual bottleneck, and only then decide whether multiple application instances or containerization are justified.”**

Codex explicitly notes that Bedrock's managed serving does not remove capacity concerns from the Streamlit server. 

### Possible follow-ups

> Would you use Kubernetes?
> How would multiple instances affect session state?
> Would you add S3?
> How would you load-test it?

---

# 17. How do you handle errors and model fallback?

### What is the interviewer checking?

Reliability and whether you understand current implementation weaknesses.

### Strong interview answer

> **“One issue I identified in the current version is that application failures can be represented in history as though they were successful assistant messages. That's dangerous because the error can then be sent back to the model as conversation context. In production I would separate successful AI content from application errors completely.**
>
> **I would also make model fallback explicit. The current fallback path can silently change the effective model, so production behaviour should record the requested model, actual model, fallback reason and outcome. User-facing errors should remain simple and safe, while detailed technical information should go to structured logs.”**

Codex identified both error-history contamination and silent fallback behaviour. 

### Possible follow-ups

> What if Bedrock is throttled?
> What if streaming fails halfway?
> What should be logged?
> Would you retry every error?

---

# 18. How did you test NovaMind AI?

### What is the interviewer checking?

This is a question where you **must not exaggerate**.

### Strong interview answer

> **“The current repository does not yet have a formal automated test suite, and I consider that a production-readiness gap. It has diagnostic tooling for Bedrock-related checks, but I don't treat diagnostics as equivalent to automated tests.**
>
> **For production V2, I would add unit and regression tests around deterministic logic such as validation, image and document handling, Bedrock request construction, model fallback, conversation history and error handling. I would mock Bedrock for most failure scenarios, keep a smaller set of controlled real Bedrock integration tests, and separately maintain a GenAI evaluation set for correctness, relevance, grounding, hallucination, multimodal understanding, safety, latency and usage.”**

Codex confirms there is no automated test suite and separately identifies the lack of AI quality, grounding and prompt-injection evaluation.  

### Possible follow-ups

> What is a mock?
> Unit vs integration testing?
> Why can't you exact-match LLM answers?
> How would you evaluate hallucination?

---

# 19. How would you make NovaMind production-ready?

### What is the interviewer checking?

Whether you can prioritize architecture improvements.

### Strong interview answer

> **“I wouldn't begin by completely rewriting the architecture. I would first fix the existing correctness issues: strict multimodal validation, explicit model selection and fallback, proper error handling, bounded conversation context and accurate usage accounting.**
>
> **Then I would strengthen the production boundary with real user authentication, HTTPS, least-privilege IAM and per-user quotas. On the engineering side I would add automated regression tests, GenAI evaluation, repeatable releases with staging and rollback, and CloudWatch logs and metrics.**
>
> **Only after monitoring and load testing showed a real capacity requirement would I consider optional changes such as persistent conversation storage, S3-backed uploads, containers or multiple replicas. I wouldn't add RAG, microservices or Kubernetes unless the product requirements justified them.”**

This closely follows Codex's prioritized V2 and roadmap.  

### Possible follow-ups

> Which improvement comes first?
> Why CloudWatch?
> How would you implement authentication?
> When would you containerize?

---

# 20. If you rebuilt NovaMind today, what would you do differently?

### What is the interviewer checking?

This isn't asking whether your project was a failure.

They want to see whether you've **learned from building it**.

### Strong interview answer

> **“I would keep the core architecture relatively simple because the current requirement still doesn't justify microservices or Kubernetes. But I would build production safeguards earlier.**
>
> **I would define strict attachment contracts and regression tests from the beginning, separate application errors from model conversation history, design explicit model fallback behaviour, and introduce a context budget before conversation history could grow indefinitely. I would also design usage accounting and quotas earlier because GenAI cost is closely related to request and context size.**
>
> **For deployment, I would establish a reproducible runtime, automated tests and GenAI evaluation before release, staging, rollback and centralized monitoring. I would still use Bedrock for managed model inference and would only introduce RAG, persistent storage or horizontal scaling when the actual product requirements justified them.”**

That reasoning follows the weaknesses and roadmap identified in the current implementation.  

### Possible follow-ups

> Why would you keep Streamlit?
> Would you use FastAPI now?
> Would you use RAG?
> What is your highest-priority improvement?

---

# The interview pattern behind all 20 questions

You don't actually have **20 completely different answers** to memorize.

Most questions come back to this architecture:

```text id="zhaw8e"
                   NOVAMIND AI

USER
 │
 ▼
STREAMLIT
 │
 ├── UI
 ├── Session State
 ├── chat_history
 └── bedrock_history
 │
 ▼
PYTHON SERVICES
 │
 ├── validators.py
 ├── image_service.py
 ├── document_service.py
 └── bedrock_service.py
 │
 ▼
boto3
 │
 ▼
IAM
 │
 ▼
AMAZON BEDROCK
 │
 ▼
FOUNDATION MODEL
 │
 ▼
STREAMING RESPONSE
 │
 ▼
USER
```

Then different questions simply zoom into different boxes.

If the interviewer asks:

```text id="tr31pg"
Security
```

zoom into:

```text id="i0gtbb"
Authentication → boto3 → AWS identity → IAM
```

If they ask:

```text id="bx9ufb"
Cost
```

zoom into:

```text id="7y3n62"
Model choice
+
Input/context
+
Output
+
Attachments
```

If they ask:

```text id="zhx2tw"
Troubleshooting
```

trace:

```text id="8ulc6i"
Browser
→ Streamlit
→ Python
→ boto3
→ IAM
→ Bedrock
→ Model
```

If they ask:

```text id="dbmcb6"
Scaling
```

separate:

```text id="fdr6ch"
Application Tier
vs
Managed Model-Serving Tier
```

If they ask:

```text id="uifb3v"
Production
```

think:

```text id="g4pb40"
Correctness
→ Security
→ Cost controls
→ Testing
→ Observability
→ Deployment
→ Scaling
```

That's why understanding the architecture is more powerful than memorizing answers.

---

# 5 interview rules for this project

**Rule 1 — Never claim something that isn't implemented.** Say “current implementation” versus “production V2.” This is especially important for RAG, automated tests, CI/CD, authentication, monitoring and scaling.

**Rule 2 — Explain why, not only what.** Instead of “I used Streamlit,” explain why it matched the requirement and what trade-off you accepted.

**Rule 3 — Use one real example.** Your screenshot example is extremely useful:

> “Suppose the user uploads an AWS AccessDenied screenshot…”

You can use that to explain architecture, multimodality, Bedrock, IAM, troubleshooting and testing.

**Rule 4 — Don't invent numbers.** Don't say “my EC2 supports exactly 1,000 users” without load-test evidence. Say you would measure and load-test.

**Rule 5 — Admit limitations, then explain the engineering response.** Saying “The current version doesn't yet have automated tests; here's how I'd build the V2 testing strategy” is much stronger than pretending the feature exists.

---

## Your 17-file NovaMind learning system is now complete

```text id="tsm7mm"
NovaMind-AI-Learning/

01 ✅ Project Overview
02 ✅ Project Architecture
03 ✅ Application Flow
04 ✅ Technology Stack
05 ✅ Amazon Bedrock
06 ✅ Multimodal Processing
07 ✅ Conversation History & Session State
08 ✅ Current Problems & Limitations
09 ✅ Production-Ready V2 Architecture
10 ✅ Architecture Design Decisions
11 ✅ Security & IAM
12 ✅ AWS Deployment
13 ✅ Cost & Scalability
14 ✅ Error Handling & Troubleshooting
15 ✅ Testing & GenAI Evaluation
16 ✅ Complete Project Storytelling
17 ✅ Interview Questions & Answers
```

Save this lesson as **`17-Interview-Questions-and-Answers.md`**.

At this point, reading more NovaMind notes will give you diminishing returns. The next useful phase is **speaking practice**: start with Question 1 — *“Tell me about your NovaMind AI project”* — answer it without looking at the prepared answer, then compare your explanation against what you now understand.
