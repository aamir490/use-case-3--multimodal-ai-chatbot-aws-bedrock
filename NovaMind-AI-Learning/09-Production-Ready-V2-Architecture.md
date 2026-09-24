# 09 — Production-Ready V2 Architecture

## Question

> **Based strictly on the problems Codex identified in my current NovaMind AI project, design a realistic production-ready V2 architecture. For every proposed change, first tell me which current problem it solves, why that change is needed, what technology or AWS service should be used, and how the request flow changes. Clearly separate must-have improvements from optional improvements, and do not add technologies just to make the architecture look complex.**

---

# Answer

Now we are moving from:

```text
Current NovaMind AI
        ↓
Understand problems
        ↓
Design justified solutions
        ↓
Production-ready V2
```

The most important rule is:

> **We should not add an AWS service unless it solves a real problem identified in the current project.**

Codex itself recommended keeping the core Streamlit/service-module structure rather than immediately introducing Kubernetes, agents, a vector database, or a separate REST backend. 

So V2 should be **better engineering**, not simply **more architecture**.

---

# 1. First: what should we keep?

We do **not** need to throw away your current project.

The core architecture is reasonable:

```text
Streamlit
    ↓
Python service modules
    ↓
boto3
    ↓
Amazon Bedrock
```

Codex specifically identified the small architecture, clear service boundaries, streaming, standard AWS credentials, and lack of unnecessary RAG/API layers as strengths. 

Therefore, V2 can evolve the existing architecture.

---

# 2. V2 Design Principle

For every change, ask:

```text
PROBLEM
   ↓
Why does it matter?
   ↓
What is the smallest sensible solution?
   ↓
How does architecture change?
```

Not:

```text
"I know Kubernetes."
        ↓
"Let's add Kubernetes."
```

That distinction is important in architecture interviews.

---

# MUST-HAVE IMPROVEMENTS

These are the areas Codex considered important before treating the application as production-ready. Its high-priority recommendations included correcting upload/API validation, making inference outcomes explicit, adding real authentication/security controls, bounding usage/history, and adding regression tests. 

---

# 3. Fix input and attachment validation

### Current problem

Codex found problems around:

* document-name compatibility
* malformed image handling
* inconsistent image limits
* stale upload state

 

### Why does it matter?

Bad input should fail **before** reaching Bedrock.

Current possibility:

```text
Upload
  ↓
Application accepts it
  ↓
Bedrock request
  ↓
Failure
```

V2 should behave more like:

```text
Upload
  ↓
Strict validation
  ↓
Valid?
 ┌───────┴───────┐
 NO              YES
 ↓                ↓
Reject clearly   Continue
```

### Technology

You don't need another AWS service for this.

Improve the existing:

```text
validators.py
image_service.py
document_service.py
```

This is an important architecture lesson:

> **Not every problem requires an AWS service.**

### New flow

```text
User upload
    ↓
Strict Validators
    ↓
Image Service / Document Service
    ↓
Validated Bedrock-compatible attachment
    ↓
Bedrock Service
```

---

# 4. Make model selection and fallback truthful

### Current problem

The current fallback can silently move from the selected model to Nova Pro in some failure cases. 

Imagine:

```text
User selects Claude
       ↓
Claude invocation fails
       ↓
Nova Pro fallback
       ↓
User sees answer
```

The answer works, but the application may no longer accurately represent which model produced it.

### V2 goal

The inference result should be explicit.

Conceptually:

```text
Requested model:
Claude

Actual model:
Claude

Status:
Success
```

or:

```text
Requested model:
Claude

Status:
Failed

Fallback:
Not performed without explicit policy
```

### Technology

Again, no new AWS service is required.

Improve:

```text
bedrock_service.py
```

and its result/error handling.

### Why?

Production engineering values:

**correct failure > misleading success**

---

# 5. Separate application errors from AI answers

### Current problem

Technical failures can end up stored as assistant messages in `bedrock_history`. 

V2 should conceptually separate:

```text
AI RESPONSE
```

from:

```text
APPLICATION ERROR
```

For example:

```text
Bedrock request
      ↓
 ┌────┴─────┐
Success    Failure
  ↓           ↓
AI answer   Error handler
  ↓           ↓
History     User error message
```

A failed Bedrock request should not pretend to be an AI-generated assistant answer.

### Technology

Existing Python exception/result handling.

No new AWS service necessary.

---

# 6. Add real authentication

Now we reach the first major architectural addition.

### Current problem

The project currently has demo authentication, which isn't appropriate for a public production application. 

### What do we need?

A real identity system.

Codex's V2 recommendation explicitly calls for an authenticated user and identity integration. 

A natural AWS choice is:

**Amazon Cognito**

Conceptually:

```text
User
 ↓
Cognito
 ↓
Authenticated?
 ├── NO → Reject
 │
 └── YES
       ↓
   NovaMind AI
```

### What problem does Cognito solve?

It changes:

```text
"Anyone who reaches the app"
```

into:

```text
"Known authenticated users"
```

This gives the application a user identity around which access and usage policies can be enforced.

---

# 7. HTTPS / secure public entry

### Current problem

Codex identified the documented deployment as demo-oriented and called out the need for HTTPS and stronger production access handling. 

Its recommended V2 specifically describes:

```text
Authenticated user
       ↓
HTTPS reverse proxy
       ↓
Supervised Streamlit
```



### Why HTTPS?

Without encrypted transport:

```text
Browser
   ↓
Internet
   ↓
Application
```

traffic doesn't have the transport protection expected of a public production application.

### Technology

The exact implementation can vary. Based strictly on Codex's recommended architecture, the important requirement is:

**HTTPS reverse proxy / TLS termination in front of Streamlit.**

We don't need to invent a larger load-balancing architecture simply to make the diagram impressive.

---

# 8. Apply least-privilege IAM

### Current problem

Your documentation talks about least privilege, but Codex found deployment guidance using broader Bedrock access. 

### V2

Instead of:

```text
Application
   ↓
Broad Bedrock permissions
```

use:

```text
Application IAM Role
        ↓
Only required actions/resources
        ↓
Amazon Bedrock
```

### Why?

If your application needs only specific Bedrock inference operations, its AWS identity shouldn't automatically receive unnecessary AWS permissions.

### Technology

**AWS IAM**

You already use IAM.

This isn't “adding IAM.”

It's **using IAM correctly**.

---

# 9. Add request quotas and usage limits

### Current problem

Codex found no strong per-user quotas or spending controls. 

This matters because Bedrock usage costs money.

Imagine:

```text
One user
 ↓
10 requests
```

versus:

```text
Abusive user / script
 ↓
10,000 requests
```

### V2

Once users are authenticated, usage can be associated with a user identity.

Conceptually:

```text
Authenticated User
       ↓
Check Usage / Quota
       ↓
Allowed?
 ┌─────┴─────┐
 NO          YES
 ↓            ↓
Reject      Bedrock
```

### Technology

Codex recommends quotas/accounting as part of V2 but does not prescribe a specific AWS persistence service for implementing them. 

So based **strictly** on the report, we should not pretend that DynamoDB is mandatory here.

The architectural requirement is:

> **per-user/request usage limits and accounting.**

The exact storage implementation is a later engineering decision.

---

# 10. Bound conversation history

This is one of the most important GenAI improvements.

### Current problem

Currently:

```text
Q1
 ↓

Q1+A1+Q2
 ↓

Q1+A1+Q2+A2+Q3
 ↓

...
```

History grows, and previous attachments can also be resent. 

### V2

Introduce a **context budget**.

Conceptually:

```text
Conversation History
        ↓
Context Manager
        ↓
Within allowed budget?
      /       \
    YES        NO
     ↓          ↓
   Send      Trim/manage
```

### Technology

This can initially be **application logic**.

You do not need:

```text
Redis
Vector DB
Knowledge Base
```

just to solve conversation growth.

### New request flow

Current:

```text
Entire history
      ↓
Bedrock
```

V2:

```text
Conversation history
      ↓
Context budget
      ↓
Relevant/bounded history
      ↓
Bedrock
```

That helps control request size and cost.

---

# 11. Improve usage and cost accounting

### Current problem

Your current token/cost display is approximate and doesn't fully represent attachment/model usage. 

### V2

Where Bedrock provides actual usage information, use it rather than relying only on rough local estimates.

Conceptually:

```text
Bedrock Response
      ↓
Usage Metadata
      ↓
Accounting
      ↓
Application Metrics
```

### Why?

Then you can answer operational questions such as:

```text
How much model usage occurred?
Which model was invoked?
How large are requests becoming?
```

Codex lists actual usage accounting as part of the recommended V2. 

---

# 12. Add automated regression tests

### Current problem

Codex found important correctness issues and recommended regression tests as a high-priority improvement. 

### What should be tested?

Not just:

```text
Does Python start?
```

but behaviors such as:

```text
Valid image accepted
Invalid image rejected

Valid document accepted
Invalid document rejected

Document names Bedrock-compatible

Bedrock failure doesn't pollute history

Model selection behaves correctly

History budgeting works
```

### Technology

You already have:

**pytest**

So:

```text
Code change
    ↓
pytest
    ↓
PASS / FAIL
```

No new cloud service is required to start.

---

# 13. Add AI-specific evaluation

Traditional tests aren't enough for a Generative AI system.

Codex found no proper AI evaluation benchmark. 

### Why?

A function can technically work while the model's answer quality becomes worse.

For example, maintain a small evaluation set:

```text
Test 1:
AWS AccessDenied screenshot

Expected behavior:
Identify access problem
Explain clearly
Avoid inventing unsupported details


Test 2:
PDF report

Expected behavior:
Summarize key information


Test 3:
Follow-up question

Expected behavior:
Use previous context
```

Then when you change:

```text
Prompt
Model
History strategy
Attachment processing
```

you can evaluate whether behavior regressed.

### Technology

Codex recommends an **AI evaluation set**, but does not prescribe a new AWS service. 

Again, keep it simple.

---

# 14. Make deployment reproducible

### Current problem

Deployment is largely manual, and Codex found no CI/CD or IaC implementation. 

The problem isn't simply:

> “Manual commands are bad.”

It's:

> “Can I repeatedly deploy the same application and recover from a bad release?”

### V2 needs

Conceptually:

```text
Source Code
    ↓
Automated Tests
    ↓
Release
    ↓
Staging
    ↓
Verification
    ↓
Production
```

Codex specifically recommends automated tests, releases, and rollback. 

The exact CI/CD product wasn't mandated by the report, so we shouldn't claim CodePipeline/GitHub Actions/etc. is required based strictly on Codex.

The requirement is:

> **repeatable automated release process with rollback.**

---

# 15. Supervise the Streamlit process

### Current problem

A production application shouldn't depend on someone manually opening a terminal and keeping:

```text
streamlit run ...
```

alive.

Codex recommends a **supervised Streamlit process**. 

The documented deployment already discusses `systemd`, so that remains a reasonable lightweight approach.

Conceptually:

```text
EC2
 ↓
systemd
 ↓
Streamlit
```

If the process stops unexpectedly, process supervision provides a controlled operational mechanism rather than depending on manual intervention.

---

# 16. Add logs and metrics

### Current problem

Current observability is limited.

Codex recommends:

```text
Logs / Metrics
      ↓
CloudWatch
```

for V2. 

### Technology

**Amazon CloudWatch**

This is a justified new AWS service.

### What should we observe?

Conceptually:

```text
Application
   │
   ├── Request errors
   ├── Bedrock failures
   ├── Latency
   ├── Application health
   └── Usage information
        ↓
    CloudWatch
```

Now if someone says:

> “The chatbot is failing.”

you have operational evidence to investigate.

---

# 17. Fix dependency and configuration reproducibility

### Current problem

Codex found:

* Python-version inconsistencies
* loose dependency specifications
* configuration/documentation inconsistencies



### V2

The runtime requirements should be explicit and reproducible:

```text
Known Python version
       +
Known dependencies
       +
Known configuration
       ↓
Predictable environment
```

Again, this doesn't require another AWS service.

This is repository and release engineering.

---

# The Must-Have V2 Architecture

Now we can connect the justified changes.

```text
                       USER
                         │
                         ▼
                  AUTHENTICATION
                 Identity integration
                         │
                         ▼
                  HTTPS ENTRY POINT
                         │
                         ▼
              STREAMLIT APPLICATION
                  supervised process
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
 Strict Input      Context/Usage       Session
 Validation          Controls           State
        │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                PYTHON SERVICES
             ┌───────────┼───────────┐
             │           │           │
           Image      Document     Bedrock
           Service     Service      Service
                                     │
                                     ▼
                              boto3 / IAM Role
                                     │
                               least privilege
                                     │
                                     ▼
                              AMAZON BEDROCK
                                     │
                                     ▼
                           Selected Foundation
                                  Model
                                     │
                                     ▼
                              Streaming Output
                                     │
                                     ▼
                                STREAMLIT
                                     │
                                     ▼
                                   USER


Application / Bedrock telemetry
              │
              ▼
       AMAZON CLOUDWATCH


Engineering path:

Source
  ↓
Automated Tests
  ↓
AI Evaluations
  ↓
Repeatable Release
  ↓
Staging
  ↓
Production
  ↓
Rollback capability
```

This stays quite close to Codex's recommended V2 rather than inventing a new platform. 

---

# 18. What AWS services are actually justified?

Based on the report, your core AWS story can remain small:

| Service                                  | Why                                                                     |
| ---------------------------------------- | ----------------------------------------------------------------------- |
| **Amazon Bedrock**                       | Foundation-model inference                                              |
| **AWS IAM**                              | Least-privilege AWS authorization                                       |
| **EC2**                                  | Can continue hosting Streamlit in the lightweight V2 described by Codex |
| **Amazon CloudWatch**                    | Logs/metrics/operational visibility                                     |
| **Identity integration such as Cognito** | Real user authentication                                                |

Notice what's **not** automatically present:

```text
EKS
ECS
Lambda
API Gateway
SQS
Kinesis
OpenSearch
ElastiCache
Vector Database
Bedrock Knowledge Bases
Step Functions
```

Those services can be excellent when requirements justify them.

But adding them merely because this is an AWS project would make the architecture harder to explain and operate.

---

# OPTIONAL IMPROVEMENTS

Now we can discuss features that Codex specifically treated as optional or requirement-dependent.

---

# 19. Persistent conversation history — Optional

### Current problem

Session history disappears when the relevant Streamlit session state is lost. 

But first ask:

> **Does the product actually need users to return later and recover previous conversations?**

If no:

Keep session state.

If yes:

Persistent storage becomes justified.

Codex lists persistent history as optional rather than mandatory. 

The report doesn't require a particular database, so we shouldn't invent one as mandatory.

---

# 20. S3 uploads — Optional

Your current project keeps uploads in memory, which Codex actually identified as a strength for its current scope. 

If requirements later become:

```text
Keep uploaded documents
Allow users to revisit files
Process files asynchronously
Share files across application instances
```

then durable object storage such as Amazon S3 could become justified.

Codex explicitly lists S3 uploads as optional. 

But don't add S3 simply because:

> “Every AWS architecture should contain S3.”

---

# 21. RAG — Optional

This is particularly important for your interviews.

Current system:

```text
User uploads document
       ↓
Document sent directly
       ↓
Bedrock model
```

Codex says this is direct document prompting, not RAG. 

Should V2 automatically add RAG?

**No.**

RAG becomes useful if the requirement changes to something like:

```text
Thousands of company documents
        ↓
Search relevant information
        ↓
Retrieve specific chunks
        ↓
Ground model response
```

Then:

```text
Documents
    ↓
Chunking
    ↓
Embeddings
    ↓
Vector Store
    ↓
Retrieval
    ↓
Foundation Model
```

could be justified.

Codex explicitly lists RAG as optional. 

---

# 22. Containers / multiple replicas — Optional

Current lightweight deployment can remain:

```text
EC2
 ↓
Supervised Streamlit
```

If traffic later requires multiple application instances, stronger deployment isolation, or horizontal scaling, then containers/multiple replicas can become justified.

Codex treats that as an optional later evolution. 

Therefore:

> Don't claim ECS or Kubernetes is necessary for V2 unless you have a scaling/deployment requirement that justifies it.

---

# 23. More models/modalities — Optional

Don't add:

```text
Audio
Video
Agents
More models
```

simply because they're trendy.

Codex's recommendation is essentially:

> Add capabilities when requirements justify them. 

That's a strong engineering principle.

---

# Current V1 vs Production V2

Here's the transformation you should understand:

| Area              | Current                  | V2                                                              |
| ----------------- | ------------------------ | --------------------------------------------------------------- |
| UI                | Streamlit                | **Keep Streamlit**                                              |
| Core language     | Python                   | **Keep Python**                                                 |
| AI                | Bedrock                  | **Keep Bedrock**                                                |
| AWS SDK           | boto3                    | **Keep boto3**                                                  |
| Authentication    | Demo login               | **Real identity/authentication**                                |
| Transport         | Demo-oriented deployment | **HTTPS entry**                                                 |
| IAM               | Broad guidance           | **Least privilege**                                             |
| Upload validation | Has edge cases           | **Strict validation**                                           |
| Model fallback    | Can be misleading        | **Explicit outcome**                                            |
| History           | Grows                    | **Bounded context**                                             |
| Usage             | Approximate              | **Actual accounting where available**                           |
| Testing           | Limited                  | **Regression + AI evaluation**                                  |
| Deployment        | Manual-heavy             | **Repeatable releases + rollback**                              |
| Monitoring        | Limited                  | **CloudWatch logs/metrics**                                     |
| Persistence       | Session only             | **Still session-based unless persistence is actually required** |
| RAG               | None                     | **Still none unless requirement justifies it**                  |

That's a much more realistic V2 than rewriting everything.

---

# Problem → Solution Map

The architecture should now make logical sense:

```text
Bad attachment validation
        ↓
Stricter validators/services

Silent model fallback
        ↓
Explicit inference result handling

Errors entering AI history
        ↓
Separate errors from model messages

Demo authentication
        ↓
Real identity integration

Broad IAM
        ↓
Least-privilege role

Abuse / uncontrolled usage
        ↓
Quotas + accounting

Growing history
        ↓
Context budget

Approximate usage
        ↓
Actual usage metadata where available

Limited tests
        ↓
pytest regression suite + AI evaluations

Manual releases
        ↓
Repeatable release/rollback process

Limited visibility
        ↓
CloudWatch logs/metrics

Session-only history
        ↓
Keep it unless persistent history is required

Direct document prompting
        ↓
Keep it unless RAG is actually required
```

That is exactly how you should reason about architecture.

---

# How to explain this in an interview

Suppose the interviewer asks:

> **“How would you make your NovaMind AI application production-ready?”**

A strong answer is:

> **“I wouldn't redesign the entire application just to add more AWS services. The current Streamlit, Python service-layer and Bedrock architecture is suitable for the application's scope. I would first fix the correctness issues around upload validation, model fallback and error handling. Then I would add real authentication, HTTPS, least-privilege IAM, per-user usage controls, bounded conversation context and accurate usage accounting. For reliability, I would add regression tests, an AI evaluation set, repeatable releases with rollback, process supervision and CloudWatch monitoring. Features such as persistent chat history, S3 storage, RAG, containers or multiple replicas would remain requirement-driven rather than automatically being added.”**

That's a much stronger architecture answer than:

> “I would add Kubernetes, Lambda, DynamoDB, S3, API Gateway, OpenSearch and RAG.”

because you can explain **why every component exists**.

---

# The biggest lesson from V2

Production architecture is not:

> **More services = better architecture.**

It is:

> **Problem → Requirement → Smallest appropriate solution → Verify it works.**

Your V2 should therefore evolve like this:

```text
V1
Functional GenAI application
        ↓
Correctness
        ↓
Security
        ↓
Usage / context control
        ↓
Testing
        ↓
Repeatable deployment
        ↓
Observability
        ↓
Production-ready V2
```

This also closely matches the roadmap Codex recommended: fix request correctness first, then inference reliability, measurable usage, bounded resources, secure access, reproducibility, testing, staging, monitoring, and finally production operation. 

## Save this lesson as

**`09-Production-Ready-V2-Architecture.md`**

Your learning folder now becomes:

```text
NovaMind-AI-Learning/
│
├── 01-Project-Overview.md
├── 02-Project-Architecture.md
├── 03-Application-Flow.md
├── 04-Technology-Stack.md
├── 05-Amazon-Bedrock.md
├── 06-Multimodal-Processing.md
├── 07-Conversation-History-and-Session-State.md
├── 08-Current-Problems-and-Limitations.md
├── 09-Production-Ready-V2-Architecture.md
└── images/
```

### Question 10 — Next

Now that you understand both **V1 and V2**, I would **not add another architecture topic yet**. The next important skill is explaining your design decisions:

> **“For my NovaMind AI project, teach me the important architecture and design decisions I should be able to justify in an interview. For example: Why Streamlit instead of React + FastAPI? Why Amazon Bedrock instead of hosting an LLM myself? Why direct document prompting instead of RAG? Why keep conversation state in Streamlit for V1? Why not Kubernetes or microservices? For each decision, explain the requirement, the choice I made, the trade-off, when that choice would stop being suitable, and how I should explain it naturally in an interview.”**

That should become **`10-Architecture-Design-Decisions.md`**.
