# 08 — Current Problems, Limitations & Production-Readiness Gaps

## Question

> **Based strictly on Codex’s analysis of my current NovaMind AI project, can you explain the current problems, limitations, and production-readiness gaps one by one in very simple English? For each problem, explain what the current implementation does, why it can become a problem, give a real example of what could go wrong, and classify it as correctness, security, scalability, reliability, cost, testing, deployment, or documentation. Do not improve or redesign the project yet—only help me understand the problems.**

---

# Answer

Until now, we studied what your project **does**.

Now we need to understand where the current implementation can fail or become risky.

This is an important engineering skill:

```text
Beginner thinking:

"It works on my laptop."
        ↓
"Project is finished."


Engineering thinking:

"It works."
   ↓
"But what happens when..."
   ↓
Wrong file?
Bad input?
Many requests?
AWS failure?
Server restart?
Long conversation?
Unauthorized user?
Unexpected model behavior?
```

Codex concluded that NovaMind AI has a sensible architecture for a portfolio/demo application, but it still needs correctness and operational safeguards before it should be treated as a public production system. 

We will **not fix anything in this lesson**.

We are only understanding the problems.

---

## 1. Document filenames can cause Bedrock request problems

**Category: Correctness**

### What does the current implementation do?

Your application allows users to upload documents and prepares them for the Bedrock request.

Codex found a specific issue around document naming: after sanitization, names can still contain underscores, while the Bedrock document-name contract described in the analysis doesn't allow that character. 

For example:

```text
aws_report_2026.pdf
```

may produce a document name containing:

```text
aws_report_2026
```

### Why is this a problem?

The document itself may be perfectly valid, but the **API request can still be invalid** because of the name sent with it.

### Real example

User uploads:

```text
monthly_aws_report.pdf
```

Your application accepts the PDF.

Then:

```text
Valid PDF
   ↓
Document Service
   ↓
Bedrock Request
   ↓
Invalid document name
   ↓
Request fails
```

This is a **correctness bug** because the application can accept something locally that later fails at the API boundary.

---

## 2. Image validation is not fully trustworthy

**Category: Correctness / Reliability**

### What does the current implementation do?

`image_service.py` performs image checks including size, signatures, dimensions, processing, and thumbnails.

However, Codex found that malformed image data can still be accepted in some paths, and that the current size/dimension handling doesn't fully match the intended limits/documentation. 

### Why is this a problem?

Your application may effectively say:

> “This image is okay.”

when the file is actually corrupted or doesn't meet the expected constraints.

### Real example

Someone uploads:

```text
error.png
```

but the file contents are damaged.

Conceptually:

```text
Upload
  ↓
Validation says OK
  ↓
Later image processing / Bedrock request
  ↓
Unexpected failure
```

This makes upload behavior less predictable.

---

## 3. Model fallback can silently change the model

**Category: Correctness / Reliability**

This is particularly important for an AI application.

### What does the current implementation do?

Codex found fallback logic in `bedrock_service.py`.

If invocation using the selected model ID fails, the fallback path can switch to a Nova Pro inference profile rather than simply retrying the exact same model through an equivalent route. 

### Why is that a problem?

Imagine the user selects:

```text
Claude 3.5 Sonnet
```

They expect:

```text
Question
   ↓
Claude
   ↓
Answer
```

But if that call fails, the fallback could effectively become:

```text
Claude selected
   ↓
Invocation fails
   ↓
Fallback
   ↓
Nova Pro
   ↓
Answer
```

The application may still produce an answer, so the user may think:

> “Claude generated this.”

when another model actually did.

That's a **correctness problem** because the application's reported model choice and actual inference path can diverge.

---

## 4. Error messages can become part of conversation history

**Category: Correctness / Reliability**

### What does the current implementation do?

Codex found that failed model interactions can be stored as assistant responses in the model history. 

Imagine Bedrock fails and your application produces something like:

```text
Assistant:
Error communicating with model...
```

That may then become part of:

```text
bedrock_history
```

### Why is this a problem?

Remember what happens with `bedrock_history`:

```text
Previous History
       +
New Question
       ↓
Next Bedrock Request
```

Now technical failure text can become part of future AI context.

### Real example

```text
User:
Explain this PDF.

Assistant:
Error invoking model.

User:
Try again and make it shorter.
```

The next request could include:

```text
User: Explain this PDF
Assistant: Error invoking model
User: Try again and make it shorter
```

But the error isn't a genuine model answer.

So application errors and conversational content become mixed together.

---

## 5. Token and cost numbers are only approximate

**Category: Cost / Correctness**

### What does the current implementation do?

Your UI contains token/cost counters.

But Codex found that they are approximate rather than being complete accounting based on actual Bedrock usage metadata. It also found that attachment-related input isn't properly represented in those estimates. 

### Why does that matter?

Imagine the UI says:

```text
Estimated cost:
$0.02
```

The user may interpret that as:

> “AWS charged exactly $0.02.”

But that's not what the current number means.

### Real example

A user has:

```text
Long conversation
+
Large PDF
+
Multiple previous attachments
+
Long generated response
```

The application estimate may not fully represent the actual billable usage.

Therefore:

```text
Displayed estimate
      ≠
Guaranteed AWS bill
```

---

## 6. Uploaded-file state can become confusing

**Category: Correctness / Reliability**

### What does the current implementation do?

The project maintains a pending attachment in Streamlit session state.

Codex found several state-related edge cases, including stale attachment behavior and the uploader not being explicitly reset when a conversation is cleared. 

### Why is this a problem?

UI state and application state can disagree.

### Real example

Imagine:

```text
1. Upload report.pdf
2. Use it in a question
3. Clear conversation
4. Start a new conversation
```

The user expects:

```text
Completely clean state
```

But some upload-related state may remain.

That can make the application feel unpredictable.

---

## 7. Document preview has an HTML-safety issue

**Category: Security**

Codex found that document preview text is interpolated into HTML that Streamlit renders with unsafe HTML enabled. 

### What does that mean in simple English?

Suppose text extracted from a document contains HTML-like content.

Your application should normally treat that content as:

> “User-provided text.”

But unsafe HTML rendering can cause the browser to interpret some content as markup rather than ordinary text.

Conceptually:

```text
Uploaded document
      ↓
Extract preview text
      ↓
Insert into HTML
      ↓
Browser renders HTML
```

### Why is this a problem?

Data from an uploaded file should not automatically be trusted as safe page markup.

This creates a **security boundary problem** between uploaded content and the browser interface.

---

# 8. Demo login is not production authentication

**Category: Security**

This is one of the largest production-readiness gaps.

### What does the current implementation do?

NovaMind AI includes a **demo sign-in**.

Codex explicitly describes it as demo authentication rather than real production identity management. 

### Why is that okay for a demo?

For a portfolio project:

```text
Open app
 ↓
Simple login
 ↓
Show functionality
```

can be perfectly reasonable.

But public production software has different requirements.

### Real example

Suppose your application becomes publicly reachable.

Someone discovers it and repeatedly sends:

```text
Large documents
Large prompts
Long generations
```

Your application is calling a paid AWS service.

Without strong user identity and usage controls, you have limited ability to answer:

```text
Who is this user?

Should they have access?

How much have they consumed?

Should this request be allowed?
```

Codex specifically flagged the public deployment's authentication and abuse-control limitations. 

---

# 9. There are no strong quotas or spending controls

**Category: Security / Cost / Reliability**

This is connected to the previous issue.

### What does the current implementation do?

The chatbot can send requests to Bedrock, but Codex found no proper per-user quotas, request limits, or spending guardrails in the application. 

### Real example

Imagine an automated client sends:

```text
Request
Request
Request
Request
Request
...
```

Each one may cause Bedrock inference.

That means:

```text
More requests
      ↓
More inference
      ↓
Potentially more AWS cost
```

A normal demo user might make 20 requests.

An abusive client could attempt thousands.

That's why cost control is also part of production AI engineering.

---

# 10. AWS permissions are broader than the architecture story suggests

**Category: Security**

Your architecture documentation talks about IAM and least privilege.

But Codex found that the deployment documentation recommends broad Bedrock access rather than tightly scoped permissions. 

### What is the problem?

There is a difference between:

```text
Application requires:
Specific Bedrock operations/models
```

and:

```text
IAM gives:
Broad Bedrock permissions
```

The second grants more authority than the application necessarily needs.

### Why is that important?

A production security principle is:

> Give an application only the permissions it actually requires.

Codex therefore identified a mismatch between the project's architectural security story and its deployment guidance.

---

# 11. Deployment security is not fully production-grade

**Category: Security / Deployment**

Codex found that the documented EC2 deployment is useful for a demo but lacks several production safeguards, including a consistently established HTTPS/release story in the actual repository state. 

The important distinction is:

```text
Can the application run on a server?
          YES

Does that automatically mean
production deployment?
          NO
```

Production readiness also involves things such as secure traffic handling, reliable process management, controlled releases, rollback, monitoring, and repeatability.

Codex found gaps in those areas.

---

# 12. Conversation history can grow without a proper limit

**Category: Scalability / Cost / Reliability**

We touched on this in Lesson 7.

Your application sends previous `bedrock_history` with later requests.

Conceptually:

```text
Request 1:
Q1

Request 2:
Q1 + A1 + Q2

Request 3:
Q1 + A1 + Q2 + A2 + Q3
```

Codex found no proper context-budget or history-trimming strategy. 

### Why is this a problem?

A conversation can keep growing.

That can mean:

```text
Longer history
    ↓
Larger requests
    ↓
More model input
    ↓
Higher resource/cost pressure
```

Eventually, model/context limits can also become relevant.

---

# 13. Previous attachments can also be resent

**Category: Scalability / Cost**

This makes the previous issue more significant.

Codex found that attachment content can remain in model history and be resent with future requests. 

Imagine:

```text
Turn 1:
Large PDF + question

Turn 2:
Previous history + new question

Turn 3:
Previous history + new question
```

That means the cost/resource problem isn't just text history.

Attachments can contribute too.

---

# 14. Conversation history isn't persistent

**Category: Reliability / Scalability**

Your history currently lives in Streamlit session state rather than a persistent database. 

### Real example

User has a useful conversation:

```text
Q1
A1
Q2
A2
Q3
A3
```

Then the relevant session/application state disappears.

The user later returns expecting:

> “Show my previous conversation.”

The current architecture doesn't provide durable conversation recovery.

This is acceptable for a demo, but it's a limitation for applications that require persistent user histories.

---

# 15. “Summarize Conversation” doesn't actually shrink the context

**Category: Cost / Scalability**

The name can be misleading.

You might think:

```text
Long conversation
      ↓
Summarize
      ↓
Replace old history
      ↓
Short context
```

But Codex found that the summary feature copies the model history, asks for a summary, and assigns the extended copy back. It therefore doesn't currently act as context compression. 

So even after summarization, the history-growth problem remains.

---

# 16. There is no Bedrock Guardrail integration

**Category: Security / Reliability**

Codex found no Bedrock Guardrail integration in the current implementation. 

Don't interpret this as:

> “Therefore the application is automatically unsafe.”

That's too strong.

The actual gap is that the project doesn't currently have that explicit additional safety/control layer.

For a public AI application, you'd want to understand how undesirable input/output behavior is controlled and evaluated.

---

# 17. There is no proper AI evaluation framework

**Category: Testing / Reliability**

Traditional software tests might ask:

```text
Did this function return the expected value?
```

AI applications need another kind of testing too.

For example:

```text
Does the model correctly explain our test screenshots?

Does it summarize documents accurately?

Does it follow system instructions?

Does it avoid unsupported claims?

Does behavior change when the model changes?
```

Codex found no prompt-injection evaluation, grounding evaluation, or broader AI quality benchmark in the current project. 

### Real example

You change:

```text
Nova Lite
   ↓
Nova Pro
```

The application technically works.

But:

> Did answer quality improve?

> Did document summarization regress?

> Does image analysis still meet your expectations?

Without an evaluation set, you can't answer those questions systematically.

---

# 18. Diagnostic checks can give misleading confidence

**Category: Testing / Reliability**

Your repository contains diagnostic scripts such as the Bedrock model-access check.

That's useful.

But Codex found that some diagnostics don't perfectly prove the same path that normal application traffic uses. 

For example:

```text
Diagnostic check:
PASS
```

does not necessarily guarantee:

```text
Every real application request:
PASS
```

A health check is only meaningful if it accurately represents what you need to verify.

---

# 19. Deployment is still largely manual

**Category: Deployment / Reliability**

Codex described the deployment process as involving steps such as:

```text
Install Python
Create virtual environment
Install dependencies
Configure AWS access
Run diagnostics
Start Streamlit
Git pull
Restart
```

and found no Infrastructure as Code or CI/CD pipeline in the repository. 

### Why is manual deployment a problem?

Imagine version 1 works.

You manually change the server to version 2.

Version 2 breaks.

Now you need to remember:

```text
What exactly changed?
How do I restore V1?
What packages were installed?
What commands did I run?
```

Manual processes increase the chance of human error and inconsistent environments.

---

# 20. No Infrastructure as Code

**Category: Deployment / Reliability**

Codex found no:

```text
Terraform
CloudFormation
AWS CDK
```

in the current repository. 

That means the repository doesn't define the AWS infrastructure in a reproducible infrastructure configuration.

### Real example

Suppose the EC2 environment is lost.

A new engineer asks:

> “Can I recreate the exact infrastructure from the repository?”

The current repository doesn't provide a complete IaC definition for that.

---

# 21. No automated CI/CD pipeline

**Category: Deployment / Testing / Reliability**

Codex also found no CI/CD pipeline in the repository. 

So there isn't currently a repository-defined flow like:

```text
Developer pushes code
       ↓
Automated tests
       ↓
Build/check
       ↓
Deployment
       ↓
Verification
```

Instead, deployment depends much more on manual operations.

Again, that isn't automatically bad for a portfolio demo.

It becomes a gap when you call the application **production-ready**.

---

# 22. Observability is limited

**Category: Reliability / Deployment**

Your architecture diagram/docs mention services such as CloudWatch as proposed concepts, but Codex found those dashed services are not part of the current implemented architecture. 

Therefore, don't say in an interview:

> “CloudWatch is implemented in my current application”

based only on that architecture image.

### Why does observability matter?

Suppose users say:

> “The chatbot became slow at 3 PM.”

You would want information such as:

```text
What requests failed?
What exceptions occurred?
How long did Bedrock calls take?
How often are requests failing?
Is the server healthy?
```

The current repository doesn't establish a mature observability setup for answering all of those production questions.

---

# 23. Python-version documentation is inconsistent

**Category: Documentation / Correctness**

Codex found that some documentation advertises Python 3.9, while source syntax requires Python 3.10 or newer. 

### Real example

README says:

```text
Python 3.9 supported
```

A developer installs Python 3.9.

Then the source contains syntax unsupported by that version.

Result:

```text
Follow documentation
       ↓
Install Python 3.9
       ↓
Run application
       ↓
Syntax / compatibility problem
```

That's why documentation correctness matters.

---

# 24. Dependency versions aren't fully reproducible

**Category: Deployment / Reliability**

Codex found lower-bound dependency specifications rather than a fully locked environment. 

Conceptually, a loose dependency rule can mean:

```text
Developer A installs today
        ↓
Library version X

Developer B installs months later
        ↓
Library version Y
```

If library Y changed behavior, the two environments may behave differently.

That's a reproducibility problem.

---

# 25. Documentation contains other inconsistencies

**Category: Documentation**

Codex also identified several repository/documentation mismatches, including:

* `.env.example` tracking/configuration issues
* documentation referring to absent files
* an MIT badge without a corresponding license file
* model-support claims that aren't fully demonstrated by the implementation



Individually these might seem small.

Together they matter because another engineer or interviewer may ask:

> “Can I trust the README as an accurate description of the repository?”

Good documentation should closely match the actual code.

---

# 26. Architecture diagram contains future/proposed components

**Category: Documentation**

This one is especially important for **your interviews**.

Codex found that the architecture image contains dashed components such as:

```text
Cognito
S3
DynamoDB
CloudWatch
ECS/Fargate
Knowledge Bases
```

but these are proposals rather than implemented current components. 

So if an interviewer points at:

```text
DynamoDB
```

you should **not** say:

> “Yes, DynamoDB stores my current conversation history.”

It doesn't.

Your current conversation history is in Streamlit session state.

This is why we have been carefully separating:

```text
CURRENT IMPLEMENTATION
```

from:

```text
FUTURE / V2 ARCHITECTURE
```

---

# 27. The project isn't automatically scalable just because Bedrock is managed

**Category: Scalability**

This is an important architecture concept.

Amazon Bedrock manages model-serving infrastructure.

But your application still has:

```text
Streamlit Application
```

running somewhere.

Codex specifically pointed out that managed Bedrock model serving doesn't remove the need to think about the capacity of the Streamlit application server. 

So:

```text
Bedrock scales its managed inference side
```

does **not** mean:

```text
Your entire application automatically scales
```

The application tier still has its own capacity/state considerations.

---

# 28. Production-ready doesn't mean “add every AWS service”

This isn't a bug, but it's an important conclusion from Codex's analysis.

Codex actually identified your project's small architecture and lack of unnecessary RAG/API layers as strengths. 

So don't interpret today's lesson as:

```text
Problems found
     ↓
Add Kubernetes
Add microservices
Add 20 AWS services
Add RAG
Add agents
```

That would be the wrong lesson.

Today we're only identifying where the **current requirements and implementation don't yet meet stronger production expectations**.

---

# The big picture

You don't need to memorize 28 sections.

Put the gaps into these categories:

```text
CURRENT NOVAMIND AI
        │
        ├── CORRECTNESS
        │     ├── Document naming
        │     ├── Image validation
        │     ├── Model fallback
        │     └── Error history
        │
        ├── SECURITY
        │     ├── Demo authentication
        │     ├── HTML preview handling
        │     ├── Broad permissions
        │     ├── Limited abuse controls
        │     └── No explicit Guardrail integration
        │
        ├── COST / SCALABILITY
        │     ├── Growing conversation history
        │     ├── Attachments resent
        │     ├── Approximate cost tracking
        │     └── No strong quotas
        │
        ├── RELIABILITY
        │     ├── Session-only history
        │     ├── Upload-state edge cases
        │     └── Diagnostics limitations
        │
        ├── TESTING
        │     └── Limited AI evaluation
        │
        ├── DEPLOYMENT
        │     ├── Manual deployment
        │     ├── No IaC
        │     ├── No CI/CD
        │     └── Limited observability
        │
        └── DOCUMENTATION
              ├── Python version mismatch
              ├── Dependency reproducibility
              ├── Docs/repository inconsistencies
              └── Future components shown in diagram
```

---

# Most important mindset

Before this lesson, you might have thought:

> **“My chatbot works, therefore it is production-ready.”**

Now you should distinguish:

```text
FUNCTIONAL
   ↓
"It can perform the intended task."

        ≠

PRODUCTION-READY
   ↓
"It can perform that task reliably,
securely, repeatedly and operationally
under real-world conditions."
```

Your current NovaMind AI already demonstrates useful application architecture and Bedrock integration.

The production gaps are mainly about what happens **around the happy path**:

```text
Normal user + normal file + successful Bedrock request
                       ↓
                      Works

But production asks:

What about bad input?
AWS errors?
Long sessions?
Abuse?
Cost?
Restarts?
Deployment mistakes?
Monitoring?
Model regressions?
Security?
```

That is exactly why identifying these gaps matters.

## Interview Explanation

If an interviewer asks:

> **“Is this application production-ready?”**

A much stronger answer than simply saying “yes” is:

> **“The current version is a functional portfolio/demo implementation with a clean separation between the Streamlit UI, multimodal processing services, and Bedrock integration. During my review I identified several gaps before I would consider it public-production-ready, including stronger authentication and usage controls, bounded conversation context, more reliable upload and model-fallback handling, persistent state where required, AI evaluation, repeatable deployment, observability, and documentation consistency.”**

That answer shows that you understand the difference between **building a feature** and **operating a production system**.

---

## Save this lesson as

**`08-Current-Problems-and-Limitations.md`**

Your learning folder becomes:

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
│
└── images/
    └── NovaMind-AI-Current-Architecture.png
```

### Question 9 — Next: V2

Now we're finally ready to discuss improvements. The next question should connect **each problem you just learned** to a justified solution rather than randomly adding AWS services:

> **“Based strictly on the problems Codex identified in my current NovaMind AI project, design a realistic production-ready V2 architecture. For every proposed change, first tell me which current problem it solves, why that change is needed, what technology or AWS service should be used, and how the request flow changes. Clearly separate must-have improvements from optional improvements, and do not add technologies just to make the architecture look complex.”**

That can become **`09-Production-Ready-V2-Architecture.md`**.
