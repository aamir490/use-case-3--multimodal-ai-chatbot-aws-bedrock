# 14 — Error Handling & Troubleshooting

## Question

> **Can you teach me error handling and troubleshooting for my current NovaMind AI project from zero? Use the actual request flow and explain what can fail at each layer: browser/Streamlit, session state, upload validation, image/document processing, `bedrock_service.py`, boto3/AWS credentials, IAM permissions, Bedrock/model invocation, streaming responses, and EC2 deployment. For each failure, explain the likely symptom, possible cause, how I would isolate the problem step by step, and what logs/checks I should look at. Also explain the specific error-handling weaknesses Codex found in my current project and how production V2 should improve them. Finally, give me realistic troubleshooting interview scenarios and teach me how to answer them logically instead of memorizing fixes.**

---

# 1. What is error handling?

First separate two terms.

### Error handling

Error handling means:

> **What does my application do when something goes wrong?**

For example:

```text
User uploads invalid image
        ↓
Application detects problem
        ↓
Rejects upload safely
        ↓
Shows useful error
        ↓
Application continues running
```

Bad error handling could instead be:

```text
Invalid image
    ↓
Unhandled exception
    ↓
Application crashes
```

---

# 2. What is troubleshooting?

Troubleshooting is different.

It means:

> **Finding where and why something failed.**

Imagine the user says:

> “NovaMind isn't working.”

That tells us almost nothing.

The problem could be:

```text
Browser
   ↓
Network
   ↓
EC2
   ↓
Streamlit
   ↓
Session State
   ↓
Validation
   ↓
Image / Document Service
   ↓
bedrock_service.py
   ↓
boto3
   ↓
AWS Credentials
   ↓
IAM
   ↓
Bedrock
   ↓
Foundation Model
   ↓
Streaming Response
```

A good engineer doesn't immediately guess.

They **isolate the failing layer**.

---

# 3. The most important troubleshooting rule

Remember this:

> **Start from the symptom, identify the last layer that is working, then investigate the next layer.**

For example:

```text
Can user open website?
        │
        ├── NO
        │    ↓
        │  Deployment/network/app process
        │
        └── YES
             ↓
Can user use UI?
             │
             ├── NO → Streamlit/session problem
             │
             └── YES
                  ↓
Can upload work?
                  │
                  ├── NO → validation/processing
                  │
                  └── YES
                       ↓
Can Bedrock be called?
                       │
                       ├── NO → boto3/IAM/Bedrock
                       │
                       └── YES
                            ↓
Does response stream correctly?
```

This one mental model is more useful than memorizing 50 commands.

---

# 4. Let's troubleshoot one real NovaMind request

We'll use the same example from earlier lessons.

User uploads:

```text
access-denied.png
```

and asks:

> **“Why am I getting this AWS error?”**

The normal flow is:

```text
Browser
   ↓
Streamlit
   ↓
Session State
   ↓
validators.py
   ↓
image_service.py
   ↓
bedrock_service.py
   ↓
boto3
   ↓
IAM Authorization
   ↓
Amazon Bedrock
   ↓
Foundation Model
   ↓
Streaming Response
   ↓
Streamlit
   ↓
Browser
```

Now we'll deliberately break each layer.

---

# 5. Layer 1 — Browser / user access

Suppose the user says:

> **“I can't open NovaMind at all.”**

Before thinking about Bedrock, stop.

Bedrock probably isn't your first troubleshooting target.

Why?

Because the request hasn't even reached the AI flow yet.

---

## Possible causes

Conceptually:

```text
Browser
   ↓
Network
   ↓
Security Group
   ↓
EC2
   ↓
Port 8501
   ↓
Streamlit
```

A failure anywhere here could make the website unavailable.

Possible examples:

```text
EC2 unavailable
Streamlit process stopped
Wrong network endpoint
Port not reachable
Security-group/network issue
Application crashed during startup
```

The exact current security-group rules are not established by Codex's report, so don't invent a particular rule as the cause.

---

# 6. How would you troubleshoot?

Start outside and move inward.

### Step 1

Is EC2/application host actually available?

### Step 2

Is the Streamlit process running?

### Step 3

Is Streamlit listening where expected?

The documented deployment uses port:

```text
8501
```

### Step 4

Can network traffic reach that port?

### Step 5

Check application/startup output for exceptions.

The current deployment is manual/demo-oriented and uses a background-process approach rather than a mature supervised production service. 

---

# 7. Important troubleshooting lesson

If:

```text
Website doesn't open
```

don't begin with:

```text
Check Bedrock model.
```

Why?

Because the initial browser-to-Streamlit path occurs before a normal chatbot model invocation.

Start at the failing layer.

---

# 8. Layer 2 — Streamlit application

Now imagine:

```text
EC2 reachable ✓

But Streamlit crashes ❌
```

Possible causes include:

```text
Python error
Missing dependency
Wrong Python version
Import failure
Application startup exception
```

Codex identified a real reproducibility problem:

Some documentation advertises Python 3.9 while source syntax requires Python 3.10+. 

So this is not merely theoretical.

---

# 9. Example

Suppose deployment documentation leads someone to install:

```text
Python 3.9
```

but source uses syntax requiring:

```text
Python 3.10+
```

Then:

```text
Streamlit starts
       ↓
Python parses source
       ↓
Unsupported syntax
       ↓
Application fails
```

The correct troubleshooting thought is:

> **“This is a runtime compatibility problem.”**

Not:

> “Bedrock is down.”

---

# 10. What would you check?

For Streamlit startup failures:

```text
1. Is correct Python being used?
2. Is correct virtual environment active?
3. Are dependencies installed?
4. Are imports succeeding?
5. What exception appears when Streamlit starts?
6. Which file/line generated it?
```

This is much better than randomly reinstalling everything.

---

# 11. Layer 3 — Session state

Suppose the UI works.

User says:

> “My conversation disappeared.”

Now ask:

> Is this an AI problem?

Probably not.

Remember from Lesson 7:

```text
Streamlit Session State
        │
        ├── chat_history
        ├── bedrock_history
        ├── settings
        ├── counters
        └── pending attachment
```

The current project stores session information in application memory rather than a durable database. 

---

# 12. Possible session-state symptom

```text
User chats
   ↓
Conversation exists
   ↓
Relevant session/process is lost
   ↓
Conversation no longer available
```

That isn't necessarily a Bedrock failure.

Bedrock isn't your persistent conversation database.

---

# 13. Another session-state problem — stale attachment

Codex found that upload state can become confusing.

An attachment can remain pending in ways that may lead to stale/incorrect attachment behavior. 

For example:

```text
User uploads image A
       ↓
Changes upload selection
       ↓
Application state isn't reset correctly
       ↓
Unexpected attachment may be submitted
```

This is an **application state bug**.

---

# 14. How do you troubleshoot state problems?

Ask:

```text
What does the UI show?
        ↓
What does session state contain?
        ↓
What does pending attachment contain?
        ↓
What enters bedrock_history?
        ↓
Does that match what the user intended?
```

You're tracing **state**, not networking.

---

# 15. Layer 4 — Upload validation

Suppose:

```text
User selects access-denied.png
```

and the application rejects it or behaves strangely.

Now look at:

```text
utils/validators.py
```

and the relevant attachment service.

Codex found real validation weaknesses in the current implementation. 

---

# 16. Current image-validation problem

Codex found that image validation can accept malformed input and that some size/dimension handling is inconsistent. 

Conceptually:

```text
User file
   ↓
Validation says:
"Looks okay"
   ↓
Later processing/API:
"Actually this is invalid"
   ↓
Failure happens later
```

That's bad because validation should ideally catch invalid input **before** expensive/downstream processing.

---

# 17. Troubleshooting an upload failure

Ask:

```text
1. Did browser receive the file?

2. What filename/type/size was detected?

3. Did validators.py accept it?

4. Did image_service.py or
   document_service.py accept it?

5. Was it transformed correctly?

6. What exact attachment representation
   reached bedrock_service.py?

7. Did Bedrock reject it?
```

This tells you **where** the file became invalid.

---

# 18. Layer 5 — `image_service.py`

Important reminder:

`image_service.py` does **not** understand the screenshot.

It performs application-level image processing.

Conceptually:

```text
Image
 ↓
Validation
 ↓
Processing
 ↓
Preview / prepared bytes
 ↓
Bedrock
```

The foundation model performs the semantic understanding.

So if the image can't even be opened/validated:

```text
image_service.py / validation
```

is a better place to investigate than model reasoning.

---

# 19. Example image failure

User uploads:

```text
error.png
```

but the content is malformed/corrupted.

Possible flow:

```text
Upload accepted
      ↓
Image processing attempts decode
      ↓
Decode fails
      ↓
Error
```

A production system should return something like:

> “The uploaded image couldn't be processed. Please upload a valid supported image.”

rather than exposing a confusing Python stack trace to the user.

---

# 20. Layer 6 — `document_service.py`

Documents have their own processing path.

Codex found an important correctness issue:

**document names containing underscores can violate the Bedrock/API contract expected by the current implementation.** 

For example:

```text
aws_error_report.pdf
```

might pass through local handling but produce an invalid downstream document name/format.

---

# 21. How would you troubleshoot?

Trace:

```text
Original filename
      ↓
Sanitized filename
      ↓
document_service.py
      ↓
Bedrock document content block
      ↓
API request
```

Ask:

> **“At which step does the value stop satisfying the downstream contract?”**

That's engineering troubleshooting.

---

# 22. Layer 7 — `bedrock_service.py`

Now suppose:

```text
UI works ✓
Upload works ✓
Processing works ✓

But AI request fails ❌
```

Now `bedrock_service.py` becomes important.

It is responsible for the Bedrock-facing request flow, including request construction, history, streaming and fallback behavior. 

Conceptually it combines:

```text
System Instructions
        +
bedrock_history
        +
Current Question
        +
Attachment
        +
Inference Settings
```

and sends the request through boto3.

---

# 23. What could fail here?

Examples:

```text
Wrong model identifier
Invalid request structure
Invalid attachment content block
Unsupported model capability
History/request too large
Fallback behavior
Bedrock API exception
Streaming exception
```

The important thing is not memorizing every exception.

Ask:

> **“Was the request constructed correctly before it left my application?”**

---

# 24. Codex found a model fallback problem

This is particularly important.

Codex found that fallback logic can silently switch the request to a Nova Pro inference profile/model path. 

Imagine:

```text
User selected:
Model A
    ↓
Model A invocation fails
    ↓
Application silently falls back
    ↓
Model B generates answer
```

The user may believe:

> “Model A generated this.”

when it didn't.

That's a correctness/observability problem.

---

# 25. What should V2 do?

Fallback should be explicit.

Conceptually:

```text
Requested Model
      ↓
Invocation
      ↓
Failed
      ↓
Is fallback allowed?
   /            \
 NO             YES
 ↓               ↓
Clear error    Explicit fallback
               + record actual model
```

You should be able to answer:

```text
Requested model?
Actual model?
Why fallback happened?
```

Codex places explicit inference outcomes/model-aware fallback among the high-priority improvements. 

---

# 26. Layer 8 — boto3 / AWS credentials

Suppose `bedrock_service.py` creates a correct request.

Then:

```text
Python
 ↓
boto3
 ↓
AWS
```

But boto3 needs valid AWS credentials.

If credentials aren't available/valid, the request can fail **before successful Bedrock inference**.

---

# 27. Troubleshooting credentials

Ask:

```text
1. Which environment am I running in?

Local laptop?
EC2?

2. Which AWS identity is boto3 actually using?

3. Are credentials available?

4. Are they valid?

5. Are they expired?

6. Is the expected IAM role/profile being used?
```

Don't immediately edit IAM policies before determining which identity is actually calling AWS.

---

# 28. Why STS can help

Your project contains diagnostics involving AWS STS. 

Conceptually, STS identity information can help answer:

> **“Who does AWS think I am?”**

That's extremely useful.

You might think:

```text
I'm using Role A
```

but discover the request is actually using:

```text
Profile/User/Role B
```

Then changing permissions on Role A won't solve anything.

---

# 29. Layer 9 — IAM permissions

Now suppose:

```text
Credentials valid ✓
AWS recognizes identity ✓

Bedrock request:
AccessDenied ❌
```

This points toward authorization.

Remember:

```text
Authentication
= Who are you?


Authorization
= What can you do?
```

IAM controls the second.

---

# 30. AccessDenied troubleshooting

Think in this order:

```text
WHO?
Which AWS identity?


WHAT?
Which action is being attempted?


RESOURCE?
Which model/profile/resource?


POLICY?
Does the identity have permission?


RESULT?
Why did AWS deny it?
```

Do not solve AccessDenied by immediately giving:

```text
AdministratorAccess
```

That's not good troubleshooting.

That's bypassing the security design.

---

# 31. Important project-specific IAM weakness

Codex found that the architecture talks about least privilege while deployment guidance recommends broader Bedrock access. 

So V2 should make this consistent:

```text
Application requirement
      ↓
Required Bedrock actions/resources
      ↓
Least-privilege policy
```

not:

```text
AccessDenied
   ↓
Give everything
```

---

# 32. Layer 10 — Bedrock/model invocation

Now suppose:

```text
Credentials ✓
IAM ✓
AWS connection ✓
```

but model invocation still fails.

Possible causes could include:

```text
Incorrect model/profile
Model unavailable for that path/configuration
Unsupported input modality
Invalid request format
Input too large
Service throttling/limits
Transient AWS/service failure
```

Notice:

> **Successful AWS authentication doesn't guarantee successful model inference.**

These are different stages.

---

# 33. The connection-check trap

Your application has a Bedrock connection check.

Codex found that the connection check can itself make an inference call and therefore may be billable. 

Also, Codex warns that diagnostics aren't equivalent to proving every real application request will work. 

So:

```text
Diagnostic succeeds
```

means:

> “That diagnostic path succeeded.”

It does **not** automatically prove:

```text
Every model
Every attachment
Every request type
Every conversation
```

will succeed.

---

# 34. Layer 11 — Streaming response

Your normal chat uses streaming.

Flow:

```text
Bedrock
 ↓
Response fragment
 ↓
boto3
 ↓
bedrock_service.py
 ↓
Streamlit placeholder
 ↓
User sees text
```

Now imagine:

```text
First few words appear
        ↓
Then response stops
```

That's different from:

```text
Nothing ever appeared
```

The symptom gives you information.

---

# 35. Possible streaming failure

Conceptually:

```text
Model begins generation
      ↓
Fragments arrive
      ↓
Something fails mid-stream
      ↓
Partial answer remains
```

Questions to ask:

```text
Did Bedrock begin responding?
Did fragments reach boto3?
Did application parse them?
Did Streamlit update?
Was there an exception mid-stream?
Was partial output incorrectly saved as final?
```

Again, follow the data.

---

# 36. One of the most important current bugs: errors become AI history

Codex found that when inference fails, a user-facing error string can be stored as if it were an assistant answer in `bedrock_history`. 

This is a serious correctness problem.

Imagine:

```text
User:
"Explain Bedrock."

AI call fails.

Application:
"Error: Bedrock invocation failed."
```

Then history becomes:

```text
User:
Explain Bedrock

Assistant:
Error: Bedrock invocation failed.
```

Later:

```text
User:
"Explain it more simply."
```

The application sends previous history to the model.

Now the model receives:

```text
Assistant previously said:
"Error: Bedrock invocation failed."
```

as if that were legitimate conversation content.

That's wrong.

---

# 37. Why is that bad?

Because you are mixing two completely different things:

```text
AI CONTENT
```

and:

```text
APPLICATION ERROR
```

They should not be the same data type.

Think:

```text
Successful AI response
      ↓
bedrock_history ✓


Application/API failure
      ↓
Error handling/logging
      ↓
bedrock_history ✗
```

That's the correct conceptual design.

---

# 38. How V2 should handle errors

Conceptually:

```text
Bedrock Invocation
      │
      ├── SUCCESS
      │      ↓
      │  AI response
      │      ↓
      │  bedrock_history
      │
      └── FAILURE
             ↓
        Application error
             │
             ├── Safe user message
             ├── Structured log
             └── Metrics/error tracking
```

Don't contaminate the AI conversation with infrastructure errors.

---

# 39. Layer 12 — EC2 deployment

Now imagine:

> “It worked yesterday. Today after deployment, NovaMind won't start.”

Think about deployment changes.

```text
Old Version
    ↓
git pull / update
    ↓
New Version
    ↓
Restart
    ↓
Failure
```

Possible causes include:

```text
New code bug
Dependency change
Python incompatibility
Wrong environment
Configuration issue
Credentials issue
Process failed to restart
```

---

# 40. Current deployment weakness

Codex found the current deployment to be manual/demo-oriented, with no established mature automated:

```text
Release process
Restart supervision
Rollback
HTTPS
```



That makes troubleshooting/recovery more dependent on manual investigation.

---

# 41. Example deployment failure

Suppose:

```text
V1
✓ works

Developer deploys V2

V2
❌ crashes
```

Question:

> “Can we quickly restore V1?”

Current architecture doesn't establish a mature rollback workflow.

Production V2 should.

---

# 42. Production V2 troubleshooting architecture

Codex recommends application logs/metrics flowing into CloudWatch. 

Conceptually:

```text
                     USER
                       │
                       ▼
                    HTTPS
                       │
                       ▼
                  STREAMLIT
                       │
                       ▼
               Python Services
                       │
                       ▼
                    boto3
                       │
                       ▼
                   BEDROCK


Meanwhile:

Streamlit ───────────┐
Python Services ─────┤
Bedrock failures ────┤
Usage/latency ───────┤
                     ▼
                 CLOUDWATCH
                     │
             Logs / Metrics
```

Now troubleshooting isn't based only on:

> “A user told me it failed.”

You have operational evidence.

---

# 43. What should you log?

Conceptually, useful logs can include things like:

```text
Timestamp
Request/session correlation identifier
Requested model
Actual model/profile used
Request outcome
Error category
Latency
Attachment type/metadata
Fallback occurrence
```

But be careful.

Don't blindly log:

```text
Passwords
AWS credentials
Secret keys
Sensitive document contents
Full private prompts
```

Observability itself must respect security/privacy.

---

# 44. Error categories

Instead of every error being:

```text
"Something went wrong"
```

V2 should distinguish categories.

For example:

```text
VALIDATION_ERROR
AUTHENTICATION_ERROR
AUTHORIZATION_ERROR
MODEL_INVOCATION_ERROR
THROTTLING_ERROR
STREAMING_ERROR
INTERNAL_APPLICATION_ERROR
```

Why?

Because:

```text
AccessDenied
```

shouldn't be troubleshot the same way as:

```text
Invalid PDF
```

---

# 45. User error vs system error

This distinction is useful.

### User/input problem

Example:

```text
Unsupported file
```

User can potentially fix it.

Response:

> “Please upload a supported document type.”

### System problem

Example:

```text
Bedrock unavailable
```

User can't fix AWS infrastructure.

Response:

> “The AI service is temporarily unavailable. Please try again.”

Internal logs should contain the technical details.

---

# 46. Don't expose raw technical errors to users

Imagine AWS returns a large exception containing:

```text
Resource identifiers
Internal details
Stack traces
Configuration information
```

You generally don't want to dump all of that directly into the browser.

Use two views:

```text
USER
↓
Simple safe message


ENGINEER
↓
Detailed diagnostic information
```

This is a fundamental error-handling pattern.

---

# 47. Another weakness — upload state

We discussed stale attachment behavior.

V2 should make attachment lifecycle explicit:

```text
Upload
 ↓
Validate
 ↓
Pending
 ↓
Submit
 ↓
Consumed
 ↓
Clear/reset
```

instead of ambiguous state where an old attachment might accidentally survive.

Codex identified upload-state correctness as one of the current gaps. 

---

# 48. Another weakness — diagnostic scripts

Your project has:

```text
scripts/bedrock_model_access_check.py
```

which is useful.

But Codex found diagnostic logic that can produce misleading confidence—for example, model listing isn't equivalent to proving actual inference access. 

The lesson is:

> **Test the operation you actually depend on.**

If production depends on:

```text
Invoke model with multimodal request
```

then merely proving:

```text
I can list models
```

is not enough.

---

# 49. Troubleshooting by layers

This is the most useful table in this lesson.

| Symptom                              | Start investigating                  |
| ------------------------------------ | ------------------------------------ |
| Website won't open                   | EC2/network/Streamlit                |
| App opens but crashes                | Python/runtime/dependencies/app      |
| Conversation disappears              | Session state                        |
| Upload rejected                      | Validators                           |
| Image can't process                  | Image service                        |
| PDF/document fails                   | Document service/request format      |
| No AWS identity                      | boto3/credentials                    |
| AccessDenied                         | IAM                                  |
| Model invocation rejected            | Bedrock request/model                |
| Wrong model answers                  | Selection/fallback logic             |
| Partial answer then failure          | Streaming path                       |
| Works locally, not EC2               | Deployment/config/runtime            |
| Works after restart then fails later | Process/resources/state              |
| Costs grow unexpectedly              | History/attachments/usage accounting |

Do not memorize this table.

Understand the progression.

---

# 50. Troubleshooting Scenario 1 — Website doesn't open

Interviewer:

> **“A user says NovaMind AI is down. How do you troubleshoot it?”**

Bad answer:

> “I restart EC2.”

Why bad?

You haven't identified the problem.

Better:

> **“First I would determine whether the failure is before or after the application layer. I would check whether the EC2 host is reachable, whether the Streamlit process is running and listening on the expected port, and whether the network/security-group path allows the request. If Streamlit isn't running, I would inspect its startup/application output for Python, dependency or configuration errors. I wouldn't investigate Bedrock first because the user can't even reach the application.”**

Excellent reasoning.

---

# 51. Scenario 2 — UI works, AI doesn't

Interviewer:

> **“The NovaMind UI loads correctly, but every prompt fails. What would you check?”**

Think:

```text
Browser ✓
Network ✓
EC2 ✓
Streamlit ✓

Problem must be later
        ↓
Application → AWS path
```

Good answer:

> **“Because the UI loads, I know the browser-to-Streamlit path is basically working. I would then inspect the Bedrock request path: verify that `bedrock_service.py` constructs the request correctly, determine which AWS identity boto3 is using, verify credentials and IAM permissions, check the configured region/model, and inspect the exact Bedrock exception. This narrows the investigation rather than treating the whole application as broken.”**

---

# 52. Scenario 3 — AccessDenied

Interviewer:

> **“Bedrock returns AccessDenied. What do you do?”**

Bad:

> “Give AdministratorAccess.”

Never make that your default answer.

Better:

> **“I would first identify the AWS principal actually making the request, because changing the wrong role won't help. Then I would identify the exact Bedrock action and resource being requested and compare that with the IAM policy. I would correct only the missing required permission, following least privilege, rather than granting broad administrative access.”**

Excellent.

---

# 53. Scenario 4 — Works locally but fails on EC2

Possible layers:

```text
Python version
Dependencies
AWS identity
Region/configuration
Network
Environment/config
Different code version
```

Answer:

> **“I would compare the environments rather than assuming the application logic is wrong. I would verify the deployed commit, Python version, active virtual environment and dependencies, then compare AWS identity/configuration and inspect the EC2 application error. Codex already identified Python-version and dependency reproducibility issues in the current project, so those would be high-value checks.”**



---

# 54. Scenario 5 — User selects Claude but response came from Nova

This relates directly to your current fallback issue.

Answer:

> **“I would inspect the model-selection and fallback path in `bedrock_service.py`. The current project can silently fall back to a Nova Pro profile, so I would check the requested model, actual invocation target and the exception that triggered fallback. In V2 I would make fallback explicit and record the actual model used.”**



Very project-specific answer.

---

# 55. Scenario 6 — Follow-up answer becomes strange after previous error

This is a great interview scenario.

Imagine:

```text
Question 1
 ↓
Bedrock error
 ↓
Error text stored in bedrock_history

Question 2
 ↓
Previous "assistant error" sent to model
 ↓
Confusing context
```

Answer:

> **“I would inspect `bedrock_history`. Codex found that the current implementation can store a failed inference message as though it were an assistant response. That contaminates future model context. I would separate application errors from successful model messages and only append a valid assistant response to model history.”**



---

# 56. Scenario 7 — Large conversation becomes slow or expensive

Think:

```text
bedrock_history grows
       ↓
Larger requests
       ↓
More context processing
       ↓
Potential latency/cost/resource pressure
```

Answer:

> **“I would inspect conversation size and whether old attachments are being resent. The current implementation has no proper context budget, so history can grow continuously. For V2 I would bound the model context and monitor actual usage rather than allowing every session to grow indefinitely.”**



---

# 57. Scenario 8 — Deployment broke after an update

Answer:

> **“First I would compare the last known-good release with the new version: deployed commit, Python runtime, dependency changes and startup logs. If the new release introduced the failure, production should support rollback to the known-good version. The current manual deployment doesn't establish a mature rollback mechanism, which is one of the improvements I would make in V2.”**



---

# 58. How NOT to troubleshoot

Avoid this approach:

```text
Problem
 ↓
Guess
 ↓
Change something
 ↓
Still broken
 ↓
Change something else
 ↓
Still broken
 ↓
Restart everything
```

That's random troubleshooting.

Use:

```text
SYMPTOM
   ↓
IDENTIFY LAST WORKING LAYER
   ↓
IDENTIFY FIRST FAILING LAYER
   ↓
COLLECT EVIDENCE
   ↓
FORM HYPOTHESIS
   ↓
TEST HYPOTHESIS
   ↓
FIX ROOT CAUSE
   ↓
VERIFY
   ↓
PREVENT RECURRENCE
```

This is the main lesson.

---

# 59. Example of the full reasoning process

User says:

> “My prompt isn't getting an answer.”

Don't immediately change IAM.

Ask:

### Check 1

Can they open NovaMind?

```text
Yes
```

Good.

So:

```text
EC2/network/Streamlit
```

are at least partly working.

### Check 2

Can they submit the prompt?

```text
Yes
```

Good.

### Check 3

Does application log show Bedrock request?

```text
Yes
```

Now we've reached the AWS path.

### Check 4

What's the exception?

```text
AccessDenied
```

Now focus on:

```text
AWS identity
+
IAM policy
```

not:

```text
Pillow
pypdf
Security Group
Streamlit UI
```

You have reduced a huge system to a small problem.

That's troubleshooting.

---

# 60. Production V2 error-handling strategy

Your V2 should conceptually evolve toward:

```text
                     REQUEST
                        │
                        ▼
                INPUT VALIDATION
                        │
              invalid ──┴── valid
                 │             │
                 ▼             ▼
            Safe error      Application
                               │
                               ▼
                          Bedrock Call
                               │
                    ┌──────────┴─────────┐
                    │                    │
                 SUCCESS               FAILURE
                    │                    │
                    ▼                    ▼
             AI response          Error category
                    │                    │
                    ▼             ┌──────┴──────┐
            Model history         │             │
                                  ▼             ▼
                             User-safe       Detailed
                              message         logging
                                               │
                                               ▼
                                           CloudWatch
```

That separation is extremely important.

---

# 61. What V2 should improve

Based on Codex's analysis, the important improvements include:

```text
Strict input validation

Correct document-name handling

Explicit model/fallback behavior

Do not store failures as assistant history

Better attachment-state management

Least-privilege IAM

More reliable diagnostics

Automated regression tests

AI evaluation

Supervised deployment

Repeatable releases

Rollback

CloudWatch logs/metrics
```

These improvements correspond directly to gaps Codex identified and its recommended production path.  

---

# 62. Interview answer — “How do you troubleshoot your GenAI application?”

You can naturally explain:

> **“I troubleshoot NovaMind layer by layer rather than assuming every failure is an LLM problem. I start from the user symptom and identify the last working layer. If the website doesn't load, I investigate EC2, networking and the Streamlit process. If the UI works but inference fails, I trace `bedrock_service.py`, boto3 credentials, IAM authorization and the Bedrock/model request. For attachment failures, I trace validation and the image or document service before Bedrock. I also separate application errors from successful model responses so failures don't contaminate conversation history. In production I would centralize structured logs and metrics in CloudWatch so each request can be traced across these layers.”**

That's an excellent project answer.

---

# 63. Interview answer — “How do you handle errors?”

> **“I classify errors by layer and type. User-input errors should be rejected early with a clear message, while infrastructure or Bedrock errors should be logged with enough technical detail for troubleshooting but shown to the user as a safe message. Successful model responses should enter `bedrock_history`, but application errors should not. For transient service failures I would handle them explicitly, and any model fallback should be visible rather than silently changing models.”**

---

# 64. The one troubleshooting framework I want you to remember

Don't memorize every error from this lesson.

Remember:

## **L → E → H → F → V**

```text
L = Locate
Where is the failure?

E = Evidence
What do logs/errors/state tell me?

H = Hypothesis
What is the likely cause?

F = Fix
Fix the root cause.

V = Verify
Did the fix actually solve it?
```

Example:

```text
Symptom:
Bedrock AccessDenied

LOCATE
AWS authorization layer

EVIDENCE
AccessDenied + calling identity

HYPOTHESIS
Required permission missing

FIX
Correct least-privilege policy

VERIFY
Run actual Bedrock request again
```

That's troubleshooting rather than memorization.

---

# 65. Your complete troubleshooting map

```text
USER
 │
 ▼
Browser
 │
 │ Can't open?
 │ → Network / deployment
 ▼
EC2
 │
 │ Server unhealthy?
 │ → EC2/runtime
 ▼
Streamlit
 │
 │ Process/app crash?
 │ → Python/dependencies
 ▼
Session State
 │
 │ Wrong/lost context?
 │ → State handling
 ▼
Validators
 │
 │ File rejected?
 │ → Input validation
 ▼
Image / Document Service
 │
 │ Processing failed?
 │ → File handling
 ▼
bedrock_service.py
 │
 │ Request malformed?
 │ → Application integration
 ▼
boto3
 │
 │ No credentials?
 │ → AWS identity
 ▼
IAM
 │
 │ AccessDenied?
 │ → Authorization
 ▼
Bedrock
 │
 │ Invocation failure?
 │ → Model/API/service
 ▼
Foundation Model
 │
 ▼
Streaming
 │
 │ Partial/broken response?
 │ → Stream processing
 ▼
Streamlit
 │
 ▼
USER
```

When an interviewer gives you a problem, mentally locate it on this diagram first.

---

## Save this lesson as

**`14-Error-Handling-and-Troubleshooting.md`**

Progress:

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
11 ✅ Security & IAM
12 ✅ AWS Deployment
13 ✅ Cost & Scalability
14 ✅ Error Handling & Troubleshooting

15 ⏳ Testing & GenAI Evaluation

───────────────
After Question 15:
No more major new concepts.
We start learning how YOU explain the project.
───────────────

16 ⏳ Complete Project Storytelling
17 ⏳ Mock Interview + Feedback
```

### Question 15 — Testing & GenAI Evaluation

> **“Can you teach me testing and GenAI evaluation for my current NovaMind AI project from zero? First explain why normal software testing and GenAI evaluation are different. Based strictly on Codex’s analysis, explain what automated tests my project currently has or does not have. Then show what should be tested in `validators.py`, `image_service.py`, `document_service.py`, `bedrock_service.py`, conversation/session handling, model fallback, error handling, and the Bedrock integration. Explain unit tests, integration tests, end-to-end tests, regression tests, mocks, and what pytest could be used for if I add it. Then explain how to evaluate AI response quality, multimodal answers, hallucination/grounding, prompt injection, safety, latency and cost. Finally, design a realistic V2 testing strategy and teach me how to answer testing questions in an interview without falsely claiming tests that are not currently implemented.”**
