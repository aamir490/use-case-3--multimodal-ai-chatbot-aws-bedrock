# 16 — Complete Project Storytelling

## Question

> **Now that I have completed Questions 1–15 for NovaMind AI, help me learn how to explain the complete project naturally in an interview. Explain the complete project using this storytelling structure: Problem → Requirement → Solution → Architecture → Request Flow → Key Design Decisions → AWS Deployment → Security → Challenges → Production Improvements.**

---

# 1. Why do I need a project story?

In an interview, you usually should **not** explain a project by listing technologies:

> “I used Python, Streamlit, boto3, Bedrock, EC2, IAM…”

That tells the interviewer **what technologies exist**, but not whether you understand the system.

A better explanation has a story:

```text
PROBLEM
   ↓
What problem was I trying to solve?

REQUIREMENT
   ↓
What did the application need to do?

SOLUTION
   ↓
What did I build?

ARCHITECTURE
   ↓
How did I structure it?

REQUEST FLOW
   ↓
How does one request travel through the system?

DESIGN DECISIONS
   ↓
Why did I choose this architecture?

AWS DEPLOYMENT
   ↓
How does it run on AWS?

SECURITY
   ↓
How is access controlled?

CHALLENGES
   ↓
What limitations/problems did I identify?

PRODUCTION IMPROVEMENTS
   ↓
How would I evolve it?
```

This creates a natural engineering story.

---

# 2. Problem

Start with the **problem**, not AWS services.

NovaMind AI was designed around a simple problem:

Users often have different kinds of technical information they want an AI assistant to help them understand.

That information isn't always plain text.

For example, a user might have:

```text
A technical question
        ↓
"What is Amazon Bedrock?"

A screenshot
        ↓
"Why am I getting this AWS error?"

A document
        ↓
"Summarize this report."

Code
        ↓
"Explain this code."
```

So the problem was broader than building a simple text chatbot.

The application needed to allow users to interact with generative AI using **multiple types of input**.

### How I would explain the problem

> **“The problem I wanted to solve was that users often need AI assistance with more than plain text. For example, they may want to understand an AWS error screenshot, summarize a document, review code, or ask follow-up questions about the same content. So I wanted to build a simple multimodal AI assistant that could handle these interactions through one interface.”**

This matches the actual project scope: Codex found text conversation, image/document input, code-related use cases, follow-up Q&A, selectable models/personas/languages and streaming responses. 

---

# 3. Requirement

Once the problem was clear, the next question was:

> **What did the application actually need to do?**

The core requirements were:

```text
User needs one chatbot interface
            ↓
Accept text questions
            ↓
Accept images
            ↓
Accept documents
            ↓
Maintain conversation context
            ↓
Allow model/settings selection
            ↓
Send multimodal requests to an AI model
            ↓
Stream the answer back
            ↓
Allow follow-up questions
```

The application also supports features such as:

* selectable Nova Pro, Nova Lite and Claude 3.5 Sonnet identifiers,
* personas/editable system instructions,
* multiple languages,
* temperature and output controls,
* conversation summaries,
* transcript downloads,
* a Bedrock connection check,
* approximate token/cost counters.



### How I would explain the requirement

> **“The main requirement was to provide a single conversational interface where a user could submit text, images or documents, send them to a supported foundation model through Amazon Bedrock, receive a streamed response, and continue asking follow-up questions while maintaining conversation context.”**

Now the interviewer understands what the system needed to accomplish.

---

# 4. Solution

The solution I built was **NovaMind AI**, a multimodal Generative AI chatbot.

The core technology choices are:

```text
Python
   +
Streamlit
   +
Application Service Modules
   +
boto3
   +
Amazon Bedrock
   +
Foundation Models
```

The application handles:

```text
User Interface
Input validation
Image processing
Document processing
Conversation state
Request construction
AWS communication
Streaming
```

Amazon Bedrock provides managed access to the selected foundation model.

The foundation model handles the actual AI understanding and generation.

### Important distinction

My application does:

```text
Validate
Prepare
Organize
Send
Receive
Display
```

The foundation model does:

```text
Understand
Reason over supplied content
Generate
```

That distinction is very important.

### How I would explain the solution

> **“I built NovaMind AI as a Python and Streamlit multimodal chatbot integrated with Amazon Bedrock through boto3. The application handles the UI, validation, image and document processing, conversation state and request construction, while Bedrock provides managed access to foundation models that perform the actual multimodal understanding and response generation.”**

The repository is a focused Python/Streamlit application rather than a React frontend plus separate REST backend. 

---

# 5. Current Architecture

The current project uses a **layered monolith**.

That means:

> It is one application, but its responsibilities are separated into modules.

It is **not** currently a microservices architecture.

The architecture is approximately:

```text
                       USER
                         │
                         ▼
                  WEB BROWSER
                         │
                         ▼
              ┌────────────────────┐
              │     STREAMLIT      │
              │                    │
              │ UI                 │
              │ Demo Login         │
              │ Settings           │
              │ Session State      │
              │ Chat               │
              │ Upload Handling    │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ PYTHON SERVICES    │
              │                    │
              │ validators.py      │
              │ image_service.py   │
              │ document_service.py│
              │ bedrock_service.py │
              └─────────┬──────────┘
                        │
                        ▼
                      boto3
                        │
                        ▼
                IAM AUTHORIZATION
                        │
                        ▼
                AMAZON BEDROCK
                        │
                        ▼
              FOUNDATION MODEL
                        │
                        ▼
                STREAMED RESPONSE
                        │
                        ▼
                    STREAMLIT
                        │
                        ▼
                      USER
```

Codex classified this as a layered monolith and confirmed that the browser communicates with Streamlit while the Python process makes AWS requests. AWS credentials are not placed in the browser. 

---

# 6. Responsibilities inside the architecture

The main entry point is:

```text
mod_chatbot_frontend.py
```

It handles things such as:

```text
Streamlit UI
Demo login
Settings
Session state
Uploads
Streaming display
Conversation summaries
Approximate cost information
```

Then responsibilities are separated.

### `utils/validators.py`

Responsible for validation and upload-related utilities.

### `services/image_service.py`

Responsible for processing/preparing image input.

### `services/document_service.py`

Responsible for processing/preparing document input and preview-related functionality.

### `services/bedrock_service.py`

Acts as the main integration layer between NovaMind and Amazon Bedrock.

It handles areas such as:

```text
Bedrock request construction
Conversation history
Model interaction
Streaming
Fallback behaviour
```

These responsibilities are supported by Codex's file-by-file analysis. 

---

# 7. Request Flow

Now imagine the interviewer asks:

> **“Can you walk me through one request?”**

This is where you should stop describing boxes and tell a story.

Suppose the user uploads:

```text
access-denied.png
```

and asks:

> **“Why am I getting this error?”**

---

## Step 1 — User interacts with Streamlit

The user opens NovaMind in the browser.

They can configure things such as:

```text
Model
Persona/system behaviour
Language
Temperature
Maximum output
```

Then they upload the screenshot.

---

## Step 2 — Input validation

The application determines what kind of upload it received.

Conceptually:

```text
Upload
  ↓
validators.py
  ↓
Image?
Document?
Invalid?
```

The purpose is to reject or prepare invalid input before it reaches the model path.

---

## Step 3 — Image processing

Because this example contains an image:

```text
image_service.py
```

handles application-level image processing.

Important:

> `image_service.py` does not understand what the AWS error means.

It prepares the image.

The **foundation model** performs semantic understanding.

---

## Step 4 — User submits the question

NovaMind now has:

```text
Question:
"Why am I getting this error?"

+

Image:
access-denied.png
```

The application also has conversation context and system instructions.

---

# 8. `bedrock_service.py` builds the AI request

Conceptually the request contains:

```text
System Instructions
        +
Previous bedrock_history
        +
Current Image
        +
Current Question
        +
Inference Settings
```

Then:

```text
bedrock_service.py
        ↓
boto3
        ↓
Amazon Bedrock Runtime
```

Codex found that the application sends previous history, new message, optional attachment, system instructions and inference settings through this path. 

---

# 9. IAM authorizes the AWS request

Before AWS allows the Bedrock invocation, AWS evaluates the caller's identity and permissions.

Conceptually:

```text
boto3
  ↓
AWS Identity
  ↓
IAM Policy Evaluation
  ↓
Allowed?
 /     \
No     Yes
↓       ↓
Error  Bedrock
```

IAM doesn't understand the screenshot.

IAM doesn't generate the response.

IAM answers:

> **“Is this AWS identity allowed to perform this action?”**

---

# 10. Bedrock and the foundation model

If authorization succeeds:

```text
Amazon Bedrock
       ↓
Selected Foundation Model
```

The model receives the supplied multimodal content and generates a response.

Your project doesn't download and host the model weights itself.

That's one of the important benefits of using Bedrock.

---

# 11. Streaming response

NovaMind uses streaming for normal chat.

Instead of waiting for the entire answer:

```text
Generate complete answer
        ↓
Return everything
```

the model response can arrive incrementally:

```text
"The..."
"The error..."
"The error indicates..."
```

Conceptually:

```text
Foundation Model
      ↓
Bedrock
      ↓
boto3
      ↓
bedrock_service.py
      ↓
Streamlit
      ↓
Browser
```

Codex confirmed that the normal interaction uses streaming fragments that update the Streamlit UI progressively. 

---

# 12. Conversation memory

NovaMind has two histories:

```text
chat_history
```

and:

```text
bedrock_history
```

### `chat_history`

Used for readable UI/display/export purposes.

### `bedrock_history`

Used for structured model conversation context, including attachment information.

Codex confirmed this separation. 

---

# 13. Does Bedrock remember the conversation?

Not in the way a beginner might imagine.

NovaMind maintains the conversation in the application.

For example:

```text
Q1
A1

Q2
A2

Q3
```

When Q3 is asked, NovaMind can send previous model history again:

```text
Q1
A1
Q2
A2
Q3
    ↓
Bedrock
```

Therefore the model appears to remember.

The important sentence is:

> **“Conversation memory is currently application-managed. The application resends previous context to Bedrock rather than relying on a persistent Bedrock conversation ID.”**



---

# 14. Document flow

Documents follow a similar pattern:

```text
Document
   ↓
validators.py
   ↓
document_service.py
   ↓
bedrock_service.py
   ↓
Bedrock
   ↓
Foundation Model
```

And this leads to an extremely important architecture point:

# NovaMind is currently NOT a RAG application.

For document Q&A, the project sends the document directly to the model.

There is no current:

```text
Chunking
Embedding generation
Vector database
Semantic retrieval
Retrieved-context pipeline
```

Codex explicitly classifies the implementation as **direct document prompting, not RAG**. 

---

# 15. Key Design Decision — Why Streamlit?

For the current requirement, I needed:

```text
Chat interface
Uploads
Controls
Streaming
Python integration
```

Streamlit allowed these to remain in one Python application.

I didn't need:

```text
React frontend
        +
Separate FastAPI backend
        +
API contracts
        +
Two deployment units
```

for the current project requirement.

### Interview explanation

> **“I chose Streamlit because the project is a focused Python-based GenAI application. It allowed me to build the interface and application logic quickly without introducing a separate frontend and REST backend. The trade-off is that if the product later required mobile clients, external APIs, a highly customized frontend or independently scalable backend services, I would reconsider that choice.”**

That's a design decision, not simply:

> “Streamlit is easy.”

---

# 16. Key Design Decision — Why Amazon Bedrock?

Another option would have been self-hosting an LLM.

That could require managing:

```text
Model weights
GPU infrastructure
Inference runtime
Serving
Scaling
Operational maintenance
```

Instead:

```text
NovaMind
   ↓
boto3
   ↓
Bedrock
   ↓
Managed foundation-model inference
```

### Interview explanation

> **“I chose Amazon Bedrock because I wanted managed access to foundation models without operating the underlying model-serving and GPU infrastructure myself. This lets the application focus on the multimodal workflow and AWS integration while AWS manages the model-serving layer.”**

---

# 17. Key Design Decision — Why direct document prompting instead of RAG?

Current requirement:

```text
User uploads document
        ↓
Asks questions about that document
```

For this focused use case, sending the document directly to a capable supported model keeps the architecture simple.

RAG would introduce:

```text
Chunking
Embeddings
Vector storage
Retrieval
Ranking
Context construction
```

Those components should solve a requirement, not simply make the architecture look impressive.

### Interview explanation

> **“For the current requirement, users interact with a document they upload directly, so I used direct document prompting instead of introducing a RAG pipeline. If the requirement changed to searching across a large persistent knowledge base or many documents, then I would consider chunking, embeddings, retrieval and a vector store.”**

---

# 18. Key Design Decision — Why a layered monolith?

Current architecture:

```text
One application

but

Separate modules/responsibilities
```

That gives simplicity while maintaining code organization.

### Interview explanation

> **“I kept the application as a layered monolith because the current workload didn't require independently deployed services. I still separated validation, image handling, document handling and Bedrock integration into modules so the responsibilities remain clear. Microservices would add deployment, networking and operational complexity without solving a current requirement.”**

---

# 19. Why not Kubernetes?

This is a great interview question.

Current system is essentially:

```text
One focused Streamlit application
        +
Managed Bedrock inference
```

Kubernetes would introduce substantial orchestration complexity.

Codex's recommended V2 explicitly says there is no immediate requirement for Kubernetes. 

### Interview explanation

> **“I wouldn't introduce Kubernetes just because the application runs on AWS. The current system is a small application and Bedrock already manages model serving. I would first monitor and load-test the application tier. If future requirements introduced multiple containerized services or enough scale to justify orchestration, then I would evaluate it.”**

---

# 20. AWS Deployment

Now explain how the application reaches users.

The documented deployment target is EC2.

Important wording:

> **The repository documents EC2 deployment, but Codex did not verify a currently running production EC2 environment.**



The documented flow is approximately:

```text
Laptop
  ↓
Source Repository
  ↓
EC2
  ↓
Python
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

---

# 21. What runs where?

This is worth remembering:

```text
EC2
│
├── Python
├── Streamlit
├── NovaMind source code
├── Application services
└── boto3


Amazon Bedrock
│
└── Managed foundation-model inference
```

So:

> **EC2 hosts my application. Bedrock provides managed model inference.**

Those are different responsibilities.

---

# 22. Current deployment process

The repository describes a manual deployment process involving:

```text
Prepare EC2
      ↓
Install Python
      ↓
Create virtual environment
      ↓
Install dependencies
      ↓
Configure AWS access
      ↓
Check model access
      ↓
Start Streamlit
      ↓
Serve through port 8501
```

Updates are essentially based around pulling newer source and restarting the application. The documented approach uses a manual background process such as `nohup`; Codex found no mature automated release, restart, rollback or HTTPS mechanism. 

Therefore I should **not** falsely claim:

> “My current deployment has full CI/CD, automated rollback and production process supervision.”

It doesn't.

---

# 23. Security — Two different identities

This was one of our most important lessons.

There are two security questions.

### User

```text
Who is using NovaMind?
```

That's user authentication.

### Application

```text
Is NovaMind allowed to invoke Bedrock?
```

That's AWS authorization.

Don't mix them.

---

# 24. Current user authentication

The current application has demo sign-in functionality.

Codex explicitly identifies it as insufficient for a public production application. 

So:

```text
Current
↓
Demo Authentication


Production
↓
Real Identity Integration
```

Cognito could be one possible AWS choice, but it is a **proposed option**, not something currently implemented or mandated by Codex.

---

# 25. AWS authorization

The Python application uses:

```text
boto3
```

to call AWS.

AWS evaluates the caller's credentials/identity and IAM permissions.

Conceptually:

```text
EC2/Application
      ↓
AWS Identity
      ↓
IAM Policy
      ↓
Bedrock Permission
      ↓
Bedrock
```

The repository's use of standard AWS credentials rather than hardcoded keys was identified as a strength. 

---

# 26. Least privilege

Least privilege means:

> **Give the application only the permissions it actually needs.**

For NovaMind:

```text
Need:
Required Bedrock inference access

Not automatically:
Administrator access to AWS
```

Codex found an inconsistency here: the architecture discusses least privilege, while deployment guidance recommends broader Bedrock full access. 

That's something I would correct for production.

---

# 27. Challenges and limitations

This is where your project explanation becomes much stronger.

Don't say:

> “Everything worked perfectly.”

Engineering projects have trade-offs and problems.

Codex identified several real issues.

---

# 28. Challenge — Input validation

There are correctness problems around attachment handling.

Examples include:

```text
Malformed image validation

Image size/dimension inconsistencies

Document-name/API compatibility
```



### How I would explain it

> **“One area I identified for improvement is strict multimodal input validation. Some malformed images or document naming cases can pass too far into the request path before failing. For production I would enforce the Bedrock/API contract before constructing the inference request and add regression tests around those cases.”**

---

# 29. Challenge — Model fallback

Codex found that model fallback can silently switch to a Nova Pro path. 

That's problematic because:

```text
User selects Model A
       ↓
Model A fails
       ↓
Model B silently used
```

The user/application may believe Model A produced the result.

### Production solution

Make fallback explicit and record:

```text
Requested model
Actual model
Fallback reason
Outcome
```

---

# 30. Challenge — Error handling

Codex found that a failed inference can result in an error string being stored as if it were an assistant response in `bedrock_history`. 

That can contaminate future model context.

Correct architecture:

```text
Successful AI Response
        ↓
bedrock_history


Application Error
        ↓
Error handling/logging
        ✕
Do not treat as AI answer
```

---

# 31. Challenge — Conversation growth

Because previous `bedrock_history` is resent:

```text
Turn 1
 ↓
Turn 2 includes Turn 1
 ↓
Turn 3 includes previous context
 ↓
...
```

conversation context can grow.

Attachments can also remain in history and be resent. 

That can affect:

```text
Request size
Memory
Latency
Cost
Model context limits
```

### Production solution

Use a **context budget**.

Bound how much conversation content is sent rather than allowing indefinite growth.

---

# 32. Challenge — Cost accounting

The current application has approximate token/cost counters.

But Codex found they don't fully represent actual multimodal/Bedrock usage. 

So:

```text
UI estimate
≠
Guaranteed AWS billing
```

For production, use actual usage metadata where available and build usage accounting/quotas around it.

---

# 33. Challenge — Session persistence

Current conversation/session state lives in the application.

It isn't a durable conversation database. 

Therefore:

```text
Active Session
↓
History available


Session/process lost
↓
History may not persist
```

That's acceptable for the current demo scope.

If the requirement becomes:

> “Users must return tomorrow and continue their conversation,”

then durable persistence becomes necessary.

---

# 34. Challenge — Testing

The current repository has **no automated test suite**. 

It has diagnostics, but diagnostics are not the same as tests.

Codex also found no systematic:

```text
AI quality benchmark
Grounding evaluation
Prompt-injection evaluation
```



This is a major V2 improvement area.

---

# 35. Challenge — Deployment

Current deployment is manual/demo-oriented.

It doesn't establish mature:

```text
Automated testing before release
Repeatable deployment
Staging
Rollback
HTTPS
Process supervision
Production observability
```



This doesn't mean the project is bad.

It means:

> **The current architecture is a portfolio/demo application with a clear path toward production engineering.**

---

# 36. Production V2 — philosophy

Here's the most important part.

I would **not** solve the previous problems by blindly adding:

```text
Kubernetes
Microservices
RAG
Vector database
Kafka
Lambda
API Gateway
15 AWS services
```

The V2 principle is:

> **Keep the architecture simple and improve the weaknesses that actually exist.**

Codex recommends essentially the same approach. 

---

# 37. Production V2 architecture

A realistic V2 is:

```text
                         USER
                           │
                           ▼
                 REAL AUTHENTICATION
                           │
                           ▼
                       HTTPS
                           │
                           ▼
               ┌─────────────────────┐
               │   STREAMLIT / EC2   │
               │                     │
               │ Supervised Process  │
               │                     │
               │ Strict Validation   │
               │ Context Budget      │
               │ Usage / Quotas      │
               │ Session Handling    │
               └──────────┬──────────┘
                          │
                          ▼
                  PYTHON SERVICES
                          │
                          ▼
                        boto3
                          │
                          ▼
                 LEAST-PRIVILEGE IAM
                          │
                          ▼
                   AMAZON BEDROCK
                          │
                          ▼
               APPROVED FOUNDATION MODEL


Application / Operational Telemetry
                │
                ▼
             CLOUDWATCH
```

And deployment/release becomes:

```text
Code Change
    ↓
Automated Software Tests
    ↓
GenAI Evaluation
    ↓
Release
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

This closely follows Codex's recommended V2 and roadmap.  

---

# 38. Production improvement — Testing

For deterministic Python behaviour, I would add tests around:

```text
validators.py
image_service.py
document_service.py
bedrock_service.py
session/history handling
fallback behaviour
error handling
```

A framework such as **pytest** would be a sensible choice.

Important:

> pytest is a **proposed V2 technology**. It is not currently implemented according to Codex.

Then add:

```text
Unit tests
Mocked Bedrock tests
Controlled real integration tests
End-to-end tests
Regression tests
```

---

# 39. Production improvement — GenAI evaluation

Traditional software testing isn't enough.

I would maintain repeatable evaluation cases covering:

```text
Text questions
Image understanding
Document Q&A
Grounding
Hallucination
Prompt injection
Safety
Instruction following
Latency
Usage/cost
```

Then:

```text
Prompt/model/configuration change
           ↓
Run same evaluation set
           ↓
Compare against baseline
```

This helps prevent AI-quality regressions.

---

# 40. Production improvement — Observability

Codex recommends CloudWatch logs/metrics. 

I would want operational visibility into things such as:

```text
Request outcomes
Errors
Latency
Model/fallback behaviour
Usage
Application health
```

without logging credentials or unnecessarily exposing sensitive user content.

---

# 41. Production improvement — Scalability

A very important interview answer:

> **Bedrock scaling does not mean my entire application automatically scales.**

Bedrock manages model serving.

But I still own the application tier:

```text
EC2
Streamlit
Python
Session State
Uploads
Streaming connections
```

Codex specifically points out this distinction. 

Therefore I would:

```text
Monitor
   ↓
Load test
   ↓
Identify bottleneck
   ↓
Scale only when required
```

---

# 42. If traffic increases significantly

I would not immediately say:

> “Move to Kubernetes.”

Instead:

```text
Measure current application
        ↓
Can single instance meet requirement?
        │
       YES
        ↓
Keep architecture simple


        NO
        ↓
Identify why
        ↓
Evaluate multiple instances /
containerization if justified
```

At that point, because session state is currently in memory, I would also need to reconsider how conversation state works across multiple instances.

Codex lists persistence, S3-backed uploads, containers and multiple replicas as optional later improvements when requirements justify them. 

---

# 43. When would I add RAG?

Not because:

> “Every GenAI project needs RAG.”

I would add RAG if the requirement becomes something like:

```text
Thousands of documents
      ↓
Persistent knowledge base
      ↓
Find relevant information
      ↓
Retrieve only relevant chunks
      ↓
Generate grounded answer
```

Current requirement:

```text
User uploads a document
       ↓
Ask about that document
```

So direct prompting remains reasonable.

---

# 44. Complete project story — connected together

Now look at the project as **one story**:

```text
PROBLEM
│
│ Users need AI help with text,
│ screenshots, documents and code.
▼
REQUIREMENT
│
│ One conversational multimodal interface.
▼
SOLUTION
│
│ Python + Streamlit + Amazon Bedrock.
▼
ARCHITECTURE
│
│ Layered monolith with separate
│ validation/image/document/Bedrock modules.
▼
REQUEST
│
│ User → Streamlit → Services → boto3
│ → IAM → Bedrock → Model → Stream
│ → User.
▼
STATE
│
│ Streamlit session state +
│ chat_history / bedrock_history.
▼
DESIGN
│
│ Streamlit for focused Python app.
│ Bedrock for managed inference.
│ Direct document prompting for current use case.
│ No unnecessary microservices/Kubernetes/RAG.
▼
DEPLOYMENT
│
│ Documented EC2 + Python + venv +
│ dependencies + Streamlit :8501.
▼
SECURITY
│
│ User authentication separate from
│ AWS IAM authorization.
▼
CHALLENGES
│
│ Validation, fallback, history growth,
│ error handling, cost accounting,
│ authentication, testing, deployment.
▼
V2
│
│ Strict validation
│ Real authentication
│ HTTPS
│ Least privilege
│ Context budget
│ Quotas
│ Tests + AI evals
│ Repeatable releases
│ CloudWatch
│ Rollback
▼
SCALE WHEN REQUIREMENTS JUSTIFY IT
```

That's your complete NovaMind story.

---

# 45. A natural interview version

Once you understand all the sections above, your project introduction can sound like this:

> **“NovaMind AI is a multimodal Generative AI chatbot I built using Python, Streamlit and Amazon Bedrock. The problem I wanted to solve was allowing users to interact with AI not only through text, but also with screenshots and documents—for example, uploading an AWS error screenshot and asking the model to explain it.**
>
> **The application is currently designed as a layered monolith. Streamlit handles the user interface and session state, while I separated validation, image processing, document processing and Bedrock integration into Python service modules. The Bedrock service uses boto3 to send the user's question, optional attachment, system instructions and previous conversation context to a selected foundation model through Amazon Bedrock. The response is streamed back to Streamlit.**
>
> **For document Q&A, the current version uses direct document prompting rather than RAG because the requirement is focused on a user-uploaded document rather than retrieval across a large persistent knowledge base. Similarly, I kept the architecture as a simple Streamlit application instead of introducing microservices or Kubernetes without a requirement for that complexity.**
>
> **The repository documents an EC2 deployment where the Python application runs in a virtual environment and Streamlit serves the application on port 8501. The application uses AWS credentials or role-based identity through boto3 to access Bedrock, with IAM controlling authorization.**
>
> **During review I identified several production-readiness gaps, including stricter attachment validation, model fallback transparency, unbounded conversation context, approximate usage accounting, demo authentication, lack of automated regression tests and AI evaluations, and a largely manual deployment process.**
>
> **For a production V2, I would keep the core architecture simple but add real authentication, HTTPS, least-privilege IAM, bounded conversation context, usage quotas, automated software tests, GenAI evaluation, repeatable staging and deployment with rollback, and CloudWatch observability. I would then load-test and monitor the application tier before introducing containers, multiple replicas or more complex orchestration.”**

That is the **complete story in compressed interview form**.

Do not try to memorize every word.

Understand the sequence:

> **Problem → Requirement → Solution → Architecture → Flow → Decisions → Deployment → Security → Challenges → Improvements**

Then you can recreate the explanation naturally.

---

# 46. A shorter 60–90 second version

If an interviewer says:

> **“Tell me about your NovaMind AI project.”**

you can give a shorter opening:

> **“NovaMind AI is a multimodal Generative AI chatbot built with Python, Streamlit and Amazon Bedrock. It allows users to ask text questions or upload images and documents and then interact with supported foundation models through a conversational interface.**
>
> **Architecturally, I kept it as a layered monolith: Streamlit handles the UI and session state, while separate Python modules handle validation, images, documents and Bedrock integration. The Bedrock service uses boto3 to send the user's input and conversation context to the selected model and streams the response back to the UI.**
>
> **I intentionally used direct document prompting rather than RAG because the current requirement is uploaded-document Q&A, and I avoided microservices or Kubernetes because the application doesn't currently require that complexity. The documented deployment target is EC2.**
>
> **I also identified production gaps around authentication, validation, context growth, usage tracking, automated testing, observability and deployment automation. My production V2 would address those first before introducing additional architecture.”**

Then stop.

Let the interviewer choose where to go deeper.

They might ask:

```text
"Why Bedrock?"

"Why no RAG?"

"Explain request flow."

"How is it deployed?"

"How do you secure Bedrock?"

"How do you control cost?"

"How would you scale it?"

"What challenges did you face?"

"How did you test it?"
```

And **Questions 1–15 have prepared you for exactly those follow-ups.**

---

# 47. The interview technique I want you to use

Don't dump everything at once.

Think of your knowledge like this:

```text
                    PROJECT
                       │
             60–90 sec overview
                       │
        Interviewer chooses direction
                       │
     ┌────────┬────────┼────────┬────────┐
     ▼        ▼        ▼        ▼        ▼
Architecture Bedrock Security Deployment Challenges
     │        │        │        │        │
   Deep     Deep     Deep     Deep     Deep
   answer   answer   answer   answer   answer
```

Your **opening answer should create doors**.

The interviewer opens one.

Then you use what you learned in Questions 1–15 to go deeper.

That is much better than trying to give a 10-minute monologue.

---

## Save this lesson as

**`16-Complete-Project-Storytelling.md`**

Your NovaMind learning structure is now:

```text
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

17 ⏳ Interview Questions & Mock Interview
```

**Question 16 completes the “I understand my project” phase. Question 17 should now test whether you can explain that understanding yourself rather than simply reading my answers.**
