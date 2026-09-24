# 10 — Architecture & Design Decisions

## Question

> **For my NovaMind AI project, teach me the important architecture and design decisions I should be able to justify in an interview. For example: Why Streamlit instead of React + FastAPI? Why Amazon Bedrock instead of hosting an LLM myself? Why direct document prompting instead of RAG? Why keep conversation state in Streamlit for V1? Why not Kubernetes or microservices? For each decision, explain the requirement, the choice I made, the trade-off, when that choice would stop being suitable, and how I should explain it naturally in an interview.**

---

# 1. First understand: what is a design decision?

A **design decision** means you had multiple ways to build something, but selected one approach because it suited your requirements.

For example:

```text
Requirement:
Build a focused multimodal GenAI chatbot
        ↓
Possible choices:
React + FastAPI
Streamlit
Django
Flask
        ↓
Chosen:
Streamlit
        ↓
Question:
WHY?
```

That **“why?”** is what interviewers care about.

A strong engineer doesn't just say:

> “I used Streamlit.”

They can explain:

> “I used Streamlit because..., the trade-off is..., and if the requirements changed, I would...”

Your current NovaMind AI is a deliberately small layered monolith rather than a large distributed architecture. Codex considered that appropriate for its current scope and specifically noted that the absence of unnecessary RAG/API layers is a strength. 

---

# 2. Decision 1 — Why Streamlit?

Your current application uses:

```text
Python
   +
Streamlit
```

There is **no separate React frontend and FastAPI backend** in the current implementation. 

## Requirement

You needed an interface where users could:

```text
Enter prompts
Upload images/documents
Select models
Change AI settings
See streaming responses
Maintain a conversation
```

The main goal was demonstrating the **Generative AI functionality**, not building a complex web platform.

## Choice

You used **Streamlit**.

That lets the architecture remain:

```text
Browser
   ↓
Streamlit
   ↓
Python Services
   ↓
boto3
   ↓
Amazon Bedrock
```

instead of:

```text
Browser
   ↓
React
   ↓
REST API
   ↓
FastAPI
   ↓
Python Services
   ↓
Bedrock
```

## Why is that reasonable?

Because Streamlit lets a Python AI application provide both its browser UI and application-server behavior without requiring a separate frontend framework/API tier.

For this project's scope, that's simpler.

## Trade-off

The simplicity comes with limitations.

A dedicated frontend/backend architecture can give you more control over:

```text
Complex UI/UX
Independent frontend/backend releases
Public APIs
Multiple clients
Large application architecture
Independent scaling
```

So Streamlit isn't universally “better.”

It was a reasonable choice for **this project**.

## When would Streamlit stop being enough?

Imagine NovaMind becomes:

```text
Thousands of users
      +
Mobile application
      +
Complex enterprise UI
      +
External API consumers
      +
Many backend integrations
```

Then separating frontend and backend could become justified.

## Interview answer

> **“I chose Streamlit because NovaMind AI was primarily a focused multimodal GenAI application, so I wanted to keep the application layer simple and concentrate on Bedrock integration, multimodal processing and conversation handling. Streamlit allowed me to build the UI and Python application together without introducing a separate React and REST API layer. The trade-off is less flexibility for a larger web platform, so if the application needed multiple clients, a complex frontend or independently scalable APIs, I would consider separating the frontend and backend.”**

That's much stronger than:

> “I used Streamlit because it's easy.”

---

# 3. Decision 2 — Why Amazon Bedrock?

This is probably one of your most important interview questions.

Your application needs foundation-model inference.

You could theoretically:

```text
Download an open-source model
        ↓
Provision GPU infrastructure
        ↓
Host model
        ↓
Operate inference server
```

Instead, you chose:

**Amazon Bedrock.**

---

## Requirement

NovaMind AI needs models capable of working with inputs such as:

```text
Text
Images
Documents
```

and generating responses.

## Choice

```text
Application
    ↓
boto3
    ↓
Amazon Bedrock
    ↓
Foundation Model
```

Codex confirmed that Bedrock Runtime is the project's model-inference layer and that your application doesn't host model weights itself. 

## Why?

This allows your application to focus on:

```text
Prompting
Conversation handling
Multimodal input
Application logic
AWS permissions
User experience
```

rather than:

```text
GPU servers
Model weights
Inference infrastructure
Model-serving software
GPU drivers
Serving capacity
```

The model-serving infrastructure is managed outside your Python application.

## Trade-off

Managed inference also means your application depends on:

```text
AWS service availability
Supported models
AWS APIs
Model availability/access
Service pricing
AWS quotas/limits
```

And you have less infrastructure-level control than if you hosted your own model.

## When might self-hosting make sense?

If requirements eventually demanded things such as:

```text
Very specialized model hosting
Full infrastructure/model control
A model unavailable through Bedrock
Specific cost economics at large scale
Specialized inference configuration
```

then self-hosting might deserve evaluation.

That doesn't mean self-hosting would automatically be better.

## Interview answer

> **“I chose Amazon Bedrock because my requirement was to integrate foundation models into the application without operating the underlying model-serving and GPU infrastructure myself. The application can use boto3 and Bedrock Runtime to invoke supported models while I focus on multimodal processing, conversation handling and application logic. The trade-off is dependency on AWS-supported models, pricing and service limits. If I needed a model or inference configuration that Bedrock couldn't provide, I would evaluate self-hosting.”**

---

# 4. Decision 3 — Why boto3?

You learned this earlier, but now let's understand it as a design decision.

Your Python application needs to communicate with AWS.

You could manually construct HTTP requests to AWS APIs.

Instead, you use:

```text
boto3
```

Codex identified boto3/botocore as part of the application's current stack. 

## Requirement

Python needs to call Bedrock Runtime.

## Choice

Use AWS's Python SDK.

```text
Python
  ↓
boto3
  ↓
AWS API
```

## Why?

It provides the Python interface for AWS operations and integrates with normal AWS credential handling.

Your application can work with Bedrock using SDK operations rather than implementing AWS API authentication/request mechanics itself.

## Interview answer

> **“Since the application is written in Python and Bedrock is an AWS service, I use boto3 as the AWS SDK layer between my application and Bedrock Runtime.”**

For this question, you don't need a 2-minute answer.

---

# 5. Decision 4 — Why direct document prompting instead of RAG?

This is **extremely important** because many GenAI candidates say:

> “RAG”

even when their application doesn't actually use RAG.

Your project currently does **not** use RAG. 

The current flow is approximately:

```text
User uploads document
        ↓
Validate / prepare document
        ↓
Bedrock request
        ↓
Foundation model
        ↓
Answer
```

---

## Requirement

Your project's document use case is:

> User uploads a document and asks questions about that supplied document.

For example:

```text
Upload:
AWS-report.pdf

Question:
"Summarize this report."
```

## Choice

Direct document prompting.

The document is supplied to the model rather than first building:

```text
Chunking
   ↓
Embeddings
   ↓
Vector DB
   ↓
Retrieval
   ↓
LLM
```

## Why?

For the current focused use case, adding a complete retrieval system wasn't necessary.

Codex explicitly regarded the absence of an unnecessary RAG layer as a strength of the current architecture. 

## Trade-off

Direct prompting becomes less appropriate as the knowledge problem grows.

Imagine instead of:

```text
One uploaded report
```

you have:

```text
100,000 company documents
```

Now sending all documents with every question isn't practical.

You need to locate relevant information first.

That's where retrieval becomes useful.

## When would you introduce RAG?

When the requirement becomes:

> “Users should ask questions across a large persistent knowledge base.”

Then:

```text
Question
   ↓
Retrieve relevant chunks
   ↓
Provide retrieved context
   ↓
Foundation Model
```

becomes justified.

## Interview answer

> **“I intentionally didn't use RAG in the current version because the use case is direct question answering over a user-uploaded document. The application sends the supplied document to the Bedrock model, so adding chunking, embeddings and a vector database would introduce unnecessary complexity for that requirement. If the requirement changed to searching across a large persistent document collection, then I would introduce a retrieval layer.”**

Excellent answer.

---

# 6. Decision 5 — Why two conversation histories?

Your project uses:

```text
chat_history
```

and:

```text
bedrock_history
```

Codex identified this separation as one of the good design choices. 

## Requirement

Two consumers need conversation information:

```text
Human/UI
```

and:

```text
Foundation model
```

But they don't need exactly the same representation.

## Choice

Separate them.

```text
Conversation
     │
 ┌───┴──────────┐
 ▼              ▼
chat_history   bedrock_history
 │              │
UI/export      Model context
```

## Why?

The UI can need:

```text
Timestamps
Filenames
Thumbnails
Display information
```

while the model needs structured:

```text
User messages
Assistant messages
Attachment content
```

Keeping them separate prevents UI concerns from controlling your model-message representation.

## Trade-off

Now you maintain two histories.

That means:

```text
More state
More synchronization responsibility
```

If one is updated and the other isn't, bugs can occur.

## Interview answer

> **“I separated UI history from model history because they serve different purposes. `chat_history` is display/export-oriented, while `bedrock_history` contains the structured conversation sent back to the model for context. The trade-off is that I have to keep both histories synchronized correctly.”**

---

# 7. Decision 6 — Why Streamlit Session State?

Current conversation state lives in Streamlit session state rather than a persistent database. 

## Requirement

For V1, you need the chatbot to remember earlier messages during the active session.

You don't necessarily need:

```text
User logs in next month
        ↓
All previous conversations appear
```

## Choice

Use Streamlit Session State.

```text
Current user session
       ↓
Session State
       ↓
chat_history
bedrock_history
settings
attachments
```

## Why?

It's sufficient for an active demo conversation and avoids introducing a database before persistence is required.

## Trade-off

The state isn't durable.

If the relevant session disappears:

```text
Session state
     ↓
Gone
     ↓
Conversation isn't recoverable
```

## When would this stop being suitable?

If the requirement becomes:

```text
Conversation history across devices
Persistent user accounts
Recover old chats
Analytics over conversations
Shared history across multiple app instances
```

then durable persistence becomes justified.

## Interview answer

> **“For V1, I used Streamlit session state because the requirement was to preserve context during an active chatbot session rather than provide durable chat storage. It kept the architecture simple. The trade-off is that history isn't persistent, so if cross-session conversation recovery became a requirement, I would introduce persistent storage.”**

---

# 8. Decision 7 — Why a layered monolith instead of microservices?

This is another excellent interview topic.

Your current project is essentially a **layered monolith**. 

Don't be afraid of the word **monolith**.

It isn't automatically bad.

Your application is one deployable Python application but internally separated into modules:

```text
Streamlit App
      │
      ├── validators.py
      │
      ├── image_service.py
      │
      ├── document_service.py
      │
      └── bedrock_service.py
```

---

## Requirement

The application is relatively focused.

Its services belong to the same chatbot workflow.

## Choice

One deployable application with clean internal modules.

## Why not microservices?

Imagine turning each component into:

```text
Image Microservice
Document Microservice
Bedrock Microservice
Conversation Microservice
Authentication Microservice
```

Now you introduce:

```text
Network communication
Service discovery
Independent deployments
More monitoring
More failure modes
More infrastructure
Distributed debugging
```

What problem would that solve today?

For the current scope, Codex didn't identify a requirement that justifies that complexity.

## Trade-off

A monolith can become harder to manage if it grows dramatically.

For example:

```text
Huge engineering teams
Independent business domains
Components needing independent scaling
Independent deployment requirements
```

Then service separation may become useful.

## Interview answer

> **“I kept the application as a layered monolith because the current services belong to one focused chatbot workflow and don't require independent deployment or scaling. I still separated responsibilities into image, document, validation and Bedrock modules so the code isn't tightly mixed together. Moving immediately to microservices would add distributed-system complexity without solving a current requirement.”**

That's a very strong engineering answer.

---

# 9. Decision 8 — Why not Kubernetes?

You already know Kubernetes from your DevOps background, which makes this question even more useful.

Knowing Kubernetes doesn't mean every application should use it.

## Requirement

Your current application is:

```text
One Streamlit application
```

with Bedrock handling managed model inference.

## Current choice

No Kubernetes.

Codex explicitly says there is no immediate need for Kubernetes in the recommended V2. 

## Why?

Kubernetes solves problems such as:

```text
Container orchestration
Large numbers of services
Replica management
Scheduling
Rolling deployments
Service discovery
Complex scaling
```

Your project doesn't currently demonstrate those requirements.

Using Kubernetes would mean operating:

```text
Cluster
Nodes
Pods
Services
Ingress
Deployments
Autoscaling
Observability
Permissions
```

for a small application.

That's unnecessary operational complexity.

## When might Kubernetes become justified?

Suppose NovaMind evolves into:

```text
Many independently deployed services
Large traffic
Complex scaling requirements
Large engineering organization
Containerized platform already standardized on Kubernetes
```

Then Kubernetes may become reasonable.

## Interview answer

> **“I have experience with Kubernetes, but I deliberately didn't use it here because the application is currently a small single deployable service and Bedrock already handles the managed model-serving side. Kubernetes would add operational complexity without solving a current requirement. I would reconsider it if the platform evolved into multiple independently scalable containerized services or if the organization's standard platform required Kubernetes.”**

That answer demonstrates more engineering maturity than:

> “Yes, I know Kubernetes, so I deployed everything on EKS.”

---

# 10. Decision 9 — Why not Docker yet?

Codex found no Dockerfile in the current repository. 

This needs a slightly different explanation.

Don't say:

> “We intentionally decided Docker was unnecessary.”

unless you actually made that decision.

The repository evidence only supports:

> **Docker is not currently implemented.**

That's different.

For an interview, be transparent:

> **“The current version isn't containerized. The existing deployment is a simpler Python/virtual-environment deployment. Containerization would be a reasonable later improvement if I needed stronger environment consistency, portable releases, or container-based scaling.”**

Notice the difference.

We're not inventing a historical design decision that Codex didn't find evidence for.

---

# 11. Decision 10 — Why not FastAPI?

Similar reasoning.

There is currently no separate REST backend. 

The application currently does:

```text
Browser
   ↓
Streamlit
   ↓
Python
```

rather than:

```text
Browser
   ↓
Frontend
   ↓
FastAPI
   ↓
Services
```

### When would FastAPI become useful?

If you needed:

```text
React frontend
Mobile app
External API clients
Multiple frontends
Independent backend deployment
API versioning
```

then a backend API layer becomes easier to justify.

For the current project, it would mostly introduce another layer.

---

# 12. Decision 11 — Why process images/documents before Bedrock?

You don't simply accept any file and blindly send it to AWS.

You have:

```text
validators.py
image_service.py
document_service.py
```

before `bedrock_service.py`. 

## Requirement

Bedrock expects valid inputs.

Users can upload invalid inputs.

Therefore:

```text
Untrusted user input
        ↓
Validation / preparation
        ↓
Bedrock-compatible input
```

is a sensible separation.

The model should not be responsible for application-level file validation.

That's your application's responsibility.

---

# 13. Decision 12 — Why streaming responses?

Your project uses streaming for normal chat responses. 

Instead of:

```text
User submits
     ↓
Wait...
Wait...
Wait...
     ↓
Entire answer appears
```

your application can do:

```text
User submits
     ↓
First text arrives
     ↓
Display
     ↓
More arrives
     ↓
Display
     ↓
...
```

### Why?

Foundation-model responses can take time to complete.

Streaming improves the user's **perceived responsiveness** because they can begin reading before generation finishes.

### Trade-off

Streaming requires additional application logic for:

```text
Partial responses
UI updates
Failure during generation
Finalizing history
```

But for conversational AI, the UX benefit can justify that complexity.

---

# 14. Decision 13 — Why IAM instead of AWS keys in code?

Your application uses normal AWS credential mechanisms rather than hardcoded credentials, which Codex identified as a strength. 

Never build:

```python
aws_access_key = "AKIA..."
aws_secret_key = "..."
```

into source code.

For AWS-hosted deployment, the conceptual architecture is:

```text
Application
     ↓
IAM Role
     ↓
Permission check
     ↓
Amazon Bedrock
```

The important design principle is:

> **Credentials shouldn't be embedded in application source code.**

---

# 15. The pattern behind ALL these decisions

Notice that every good design decision follows the same structure:

```text
1. What was my requirement?
        ↓
2. What did I choose?
        ↓
3. Why did that choice fit?
        ↓
4. What trade-off did I accept?
        ↓
5. When would I change the architecture?
```

This is how I want you to start thinking in interviews.

---

# 16. Example — weak vs strong interview answer

Interviewer:

> **“Why didn't you use RAG?”**

### Weak answer

> “Because my project doesn't need RAG.”

That doesn't demonstrate much understanding.

### Strong answer

> **“My current requirement is question answering over a document that the user directly uploads. Bedrock can receive that document with the user's question, so introducing chunking, embeddings, retrieval and a vector database would add complexity without solving a current problem. If the requirement changed to querying a large persistent document collection, I would introduce RAG.”**

Notice the structure:

```text
Requirement
    ↓
Choice
    ↓
Reason
    ↓
Trade-off
    ↓
Future condition
```

---

# 17. Another example

Interviewer:

> **“Why didn't you use microservices?”**

Don't say:

> “Because microservices are complicated.”

Say:

> **“The application currently has one focused business workflow, and its image, document and Bedrock components don't need independent deployment or scaling. I separated them into internal service modules while keeping one deployable application. That gives me separation of concerns without distributed-system overhead. If individual components later needed independent scaling or ownership, I would reconsider service decomposition.”**

Now you sound like someone who **made an architectural decision**, rather than someone who simply followed a tutorial.

---

# 18. Your Current Architecture Philosophy

Your project's architecture can be summarized as:

```text
KEEP IT SIMPLE
      │
      ├── Streamlit
      │
      ├── Python
      │
      ├── Modular services
      │
      ├── boto3
      │
      ├── IAM
      │
      └── Amazon Bedrock
              ↓
     Solve current requirements
              ↓
     Add complexity only when
       requirements justify it
```

That is actually an excellent principle to carry into interviews.

---

# What you should remember

Don't memorize thirteen separate answers.

Learn this decision framework:

> **“For the current requirement, I chose X because Y. The trade-off is Z. If the requirement changed to A, I would consider B.”**

For example:

> **“For the current document-Q&A requirement, I chose direct document prompting because users interact with a supplied document. The trade-off is that this doesn't scale to a large knowledge base. If we needed search across thousands of documents, I would consider RAG.”**

Once you can speak like this naturally, architecture questions become much easier.

---

## Save this lesson as

**`10-Architecture-Design-Decisions.md`**

You have now completed **10 of the planned 17 lessons**.

```text
01 ✅ Project Overview
02 ✅ Current Architecture
03 ✅ Application Flow
04 ✅ Technology Stack
05 ✅ Amazon Bedrock
06 ✅ Multimodal Processing
07 ✅ Conversation History
08 ✅ Problems & Limitations
09 ✅ Production V2 Architecture
10 ✅ Architecture Design Decisions

11 ⏳ Security & IAM
12 ⏳ AWS Deployment
13 ⏳ Cost & Scalability
14 ⏳ Error Handling & Troubleshooting
15 ⏳ Testing & GenAI Evaluation

Then we stop studying new concepts.

16 ⏳ Complete Project Storytelling
17 ⏳ Mock Interview + Feedback
```

### Question 11 — Security & IAM

Use this next:

> **“Can you teach me security and IAM in my current NovaMind AI project from zero? Explain how my Python application gets permission to call Amazon Bedrock, the difference between authentication and authorization, IAM users vs IAM roles vs policies, why credentials should not be hardcoded, what least privilege means specifically for this project, what security weaknesses Codex found in my current implementation, and how security should work in the production V2. Use the actual NovaMind AI request flow and explain how I should answer security questions in an interview.”**
