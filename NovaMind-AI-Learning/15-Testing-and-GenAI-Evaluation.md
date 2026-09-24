# 15 — Testing & GenAI Evaluation

## Question

> **Can you teach me testing and GenAI evaluation for my current NovaMind AI project from zero? First explain why normal software testing and GenAI evaluation are different. Based strictly on Codex’s analysis, explain what automated tests my project currently has or does not have. Then show what should be tested in `validators.py`, `image_service.py`, `document_service.py`, `bedrock_service.py`, conversation/session handling, model fallback, error handling, and the Bedrock integration. Explain unit tests, integration tests, end-to-end tests, regression tests, mocks, and what pytest could be used for if I add it. Then explain how to evaluate AI response quality, multimodal answers, hallucination/grounding, prompt injection, safety, latency and cost. Finally, design a realistic V2 testing strategy and teach me how to answer testing questions in an interview without falsely claiming tests that are not currently implemented.**

---

# 1. First, an important correction

Earlier, I incorrectly told you that your project already had **pytest/tests**.

That was wrong.

Codex's actual analysis says:

> **Your current NovaMind AI repository has no automated test suite.**

It also found no Dockerfile, CI/CD, Terraform, CloudFormation, or CDK. 

So for interviews:

**Do not say:**

> “I implemented pytest automated testing.”

Instead say:

> **“The current version does not yet have an automated test suite. Automated regression testing and GenAI evaluation are part of my production V2 improvement plan.”**

`pytest` is something we **could add** because this is a Python project. It is not something Codex verified as currently implemented.

This distinction is important.

---

# 2. Why testing a GenAI application is different

NovaMind contains two different kinds of behaviour.

```text id="7wqoy8"
NOVAMIND AI
     │
     ├──────────────┐
     ▼              ▼
SOFTWARE         GENERATIVE AI
LOGIC            BEHAVIOUR
     │              │
     ▼              ▼
Traditional       GenAI
Testing           Evaluation
```

Let's understand the difference.

---

# 3. Traditional software testing

Traditional software usually has relatively deterministic rules.

For example:

```text id="ip5th8"
Input:
Invalid file type

Expected:
Reject file
```

Or:

```text id="hvpgzb"
Input:
Valid PNG

Expected:
Validation succeeds
```

You can often test:

```text id="8c1bnx"
Expected Result
       ==
Actual Result
```

Pass or fail.

---

# 4. GenAI is different

Suppose we ask NovaMind:

> “Explain Amazon Bedrock in simple English.”

The model might answer:

```text id="dzz6dc"
Amazon Bedrock is an AWS service...
```

Next time it might say:

```text id="jpl3cf"
Amazon Bedrock allows developers to access...
```

Both answers could be correct.

Therefore:

```text id="ngqgo3"
Exact Answer A
≠
Exact Answer B
```

doesn't necessarily mean:

```text id="z5z84v"
one answer is wrong
```

Generative AI outputs are often **non-deterministic**.

That's why we need **evaluation**, not only exact-output assertions.

---

# 5. The core distinction

Remember this:

```text id="gk9omc"
SOFTWARE TESTING

"Did the system behave
according to its rules?"


GENAI EVALUATION

"Was the generated answer
good enough for our requirement?"
```

NovaMind needs **both**.

---

# 6. Example from your actual project

User uploads:

```text id="1s1c1e"
access-denied.png
```

and asks:

> “Why am I getting this error?”

There are two sets of questions.

### Software questions

```text id="j5sxuk"
Was image accepted correctly?

Was invalid input rejected?

Was correct image sent?

Was correct model selected?

Did boto3 receive correct request?

Was response streamed correctly?

Was successful response added to history?

Was an error kept OUT of model history?
```

These are primarily **software tests**.

### AI questions

```text id="9h6bdj"
Did the model correctly understand
the screenshot?

Did it identify the relevant error?

Was the explanation accurate?

Did it invent information?

Was the suggested solution relevant?

Was the answer safe?
```

These are **GenAI evaluations**.

Now the difference should be clearer.

---

# 7. Your current testing status

Based strictly on Codex's repository analysis:

```text id="uvvs8i"
Current NovaMind
      │
      └── Automated test suite ❌
```

Codex specifically recommends **regression tests** as a high-priority production improvement. 

Codex also found:

```text id="fgp6h9"
No AI evaluation set
No prompt-injection evaluation
No grounding evaluation
No quality benchmark
```



This is an important production gap.

---

# 8. But you do have diagnostics

Your repository contains:

```text id="7t8wni"
scripts/bedrock_model_access_check.py
```

and other diagnostic behaviour.

But:

> **Diagnostics are not the same thing as automated tests.**

Codex specifically warned that the diagnostics can provide misleading confidence about actual application behaviour. 

For example:

```text id="ab9bzg"
Can list models
        ✓
```

does not necessarily prove:

```text id="vycq1s"
Real multimodal inference
        ✓
```

That's why we shouldn't say:

> “I already have automated tests because I have a diagnostic script.”

---

# 9. Types of testing you should understand

For NovaMind, we'll learn five ideas:

```text id="w9qrlc"
Unit Tests

Integration Tests

End-to-End Tests

Regression Tests

GenAI Evaluations
```

Plus one technique:

```text id="xfmv3j"
Mocks
```

Don't memorize definitions. We'll apply each to your project.

---

# 10. Unit testing

A **unit test** tests a small piece of code independently.

Think:

```text id="x5gop5"
One function
or
One small component
```

Example:

```text id="ncyoex"
validators.py
```

Suppose a validation function accepts image uploads.

You could test:

```text id="rf0x59"
Valid PNG
    ↓
Accepted ✓


Invalid file
    ↓
Rejected ✓
```

You don't need real Bedrock for that.

---

# 11. What should we unit-test in `validators.py`?

Codex found validation problems, so this is especially important. 

Potential test cases:

```text id="l1mvqu"
Valid PNG
→ accept

Valid JPEG
→ accept

Unsupported type
→ reject

Oversized upload
→ reject

Malformed image
→ reject

Empty input
→ handle correctly

Filename requiring sanitization
→ sanitize correctly
```

This is exactly where regression tests would have been valuable.

---

# 12. Why does this matter?

Remember Codex found image validation can accept malformed content.

Imagine we fix that bug.

Without automated testing:

```text id="ddbn2h"
Fix bug
 ↓
Change other code later
 ↓
Same bug accidentally returns
```

With a regression test:

```text id="bl6mzd"
Malformed image
       ↓
Must be rejected
       ↓
Test runs after future changes
       ↓
Bug returning → TEST FAILS
```

That's powerful.

---

# 13. Testing `image_service.py`

Remember:

```text id="0pf5l2"
image_service.py
```

handles image validation/processing/preparation, not semantic understanding.

Useful software tests could cover:

```text id="o8z9bi"
Valid image opens correctly

Corrupted image rejected

Unsupported image rejected

Size limit enforced

Dimension rules enforced

Preview/thumbnail produced correctly

Prepared bytes remain valid
```

This tests your **application logic**.

It doesn't test:

> “Does Nova understand the screenshot?”

That's an AI evaluation later.

---

# 14. Testing `document_service.py`

Codex found the document-name problem.

A very important regression test would be around filenames such as:

```text id="qxvh49"
aws_error_report.pdf
```

because Codex found underscores can violate the current Bedrock/API naming contract. 

Tests should cover cases such as:

```text id="fl2n4o"
normal.pdf
→ valid

aws_error_report.pdf
→ converted/sanitized to valid API name

Very long filename
→ handled

Unsupported document
→ rejected

Oversized document
→ rejected

Malformed PDF
→ handled safely

Preview extraction fails
→ application handles failure
```

---

# 15. Testing `bedrock_service.py`

This is one of the most important components.

Remember its responsibilities include:

```text id="m84t4c"
Request construction

Conversation history

System instructions

Attachments

Model selection

Bedrock calls

Streaming

Fallback
```



So we need many tests here.

---

# 16. Test request construction

Suppose the user asks:

```text id="c5h0ce"
"What is AWS?"
```

The test can verify that the service builds the expected structure:

```text id="xq4m4o"
System Instructions
+
bedrock_history
+
Current User Message
+
Inference Settings
```

For an image:

```text id="1myt8k"
System Instructions
+
History
+
Image Content Block
+
Question
```

For a document:

```text id="p9nbmg"
System Instructions
+
History
+
Document Content Block
+
Question
```

We don't need a real AI answer just to test that our application builds the request correctly.

---

# 17. Test model selection

Suppose user chooses:

```text id="z5ah88"
Nova Lite
```

Your test should verify that the application attempts the expected configured model/profile path.

Why?

Because model selection affects:

```text id="ix9hrr"
Behaviour
Capabilities
Cost
```

and Codex found problems around fallback.

---

# 18. Test fallback behaviour

This is a very important regression test.

Current problem:

```text id="mj9d38"
Requested Model
      ↓
Failure
      ↓
Silent Nova Pro fallback
```



A V2 test could enforce:

```text id="06wq3a"
Model A fails
      ↓
Fallback policy evaluated
      ↓
Actual fallback is explicit
      ↓
Actual model recorded
```

or, depending on the design:

```text id="az58p9"
Fallback disabled
      ↓
Model A fails
      ↓
Clear failure
```

The important point is that behaviour is **predictable and tested**.

---

# 19. Test error handling

Remember the current bug:

```text id="8r25za"
Bedrock fails
      ↓
Error message
      ↓
Stored as assistant response
      ↓
bedrock_history
```



A regression test should make sure:

```text id="25gnxc"
Bedrock exception
      ↓
Safe user error
      ↓
Error logged
      ↓
NOT appended as successful
assistant response
```

This is an excellent example of a project-specific test.

---

# 20. Testing conversation/session handling

You have:

```text id="5n99b5"
chat_history
bedrock_history
pending attachment
settings
counters
```

in Streamlit session state. 

Useful tests should verify:

```text id="n7tmqk"
New session
→ histories initialized

Successful message
→ correct histories updated

Failed inference
→ model history not contaminated

Clear conversation
→ histories/counters reset

Sign out
→ session cleared

Pending attachment
→ correct lifecycle

Old attachment
→ not accidentally reused
```

That last case is especially important because Codex identified stale upload-state behaviour. 

---

# 21. Integration testing

Now move one level higher.

A **unit test** asks:

> “Does this small component work?”

An **integration test** asks:

> **“Do multiple components work correctly together?”**

For example:

```text id="dv3b4c"
validators.py
      ↓
image_service.py
      ↓
bedrock_service.py
```

Do those pieces agree on formats and behaviour?

---

# 22. Example integration test

Take:

```text id="e8dz24"
valid-test-image.png
```

Test:

```text id="kcvb1h"
Upload
 ↓
Validator accepts
 ↓
Image service processes
 ↓
Bedrock service receives
correct attachment structure
```

You can test much of this without making a real AWS call.

That brings us to **mocks**.

---

# 23. What is a mock?

Imagine testing `bedrock_service.py`.

You don't want every test run to:

```text id="d1k21v"
Call real Bedrock
 ↓
Wait for real model
 ↓
Consume real AWS resources
 ↓
Potentially incur cost
```

Instead you can create a fake replacement for the external dependency.

Conceptually:

```text id="8f9o12"
Application
     ↓
Fake Bedrock Client
     ↓
Controlled Response
```

That's a **mock**.

---

# 24. Example mock

You tell your test:

```text id="dv3uw3"
When application calls Bedrock:

Pretend Bedrock returns:
"Amazon Bedrock is..."
```

Then test:

```text id="2wt5t7"
Did my application:

✓ construct correct request?
✓ process response?
✓ update history?
✓ stream/display correctly?
```

without needing the real Bedrock service.

---

# 25. Mocks can also simulate failures

This is extremely useful.

Tell the mock:

```text id="wyf0eh"
When Bedrock is called:

Raise AccessDenied
```

Then verify:

```text id="3fclpe"
Application doesn't crash

Safe error shown

Error not stored in bedrock_history

Correct error path triggered
```

Or simulate:

```text id="sk20ab"
Throttling
Timeout
Streaming interruption
Model failure
```

This allows you to test rare failure paths reliably.

---

# 26. But mocks are not enough

Suppose:

```text id="67p6cz"
Mock tests ✓
```

Does that prove:

```text id="3gfj97"
Real AWS Bedrock works?
```

No.

Mocks prove **your application's expected interaction**.

They don't prove:

```text id="4v25xx"
AWS credentials
IAM permissions
Actual model access
Actual Bedrock API behaviour
Network
Real multimodal compatibility
```

That's why you also need some real integration tests.

---

# 27. Real Bedrock integration test

A controlled integration test could exercise:

```text id="5pmjlf"
Test Environment
      ↓
Real boto3
      ↓
Test IAM identity
      ↓
Amazon Bedrock
      ↓
Approved model
      ↓
Small controlled request
```

For example:

```text id="vtsmbd"
Input:
"Reply with the word READY."
```

The goal isn't to evaluate intelligence.

It's to verify the real integration path.

---

# 28. Why your current diagnostics aren't enough

Codex found that the diagnostic tooling can infer too much from things such as model listing. 

So:

```text id="9h85ci"
Can list models
```

tests:

```text id="t2dtpd"
Can perform that control-plane operation
```

It doesn't necessarily test:

```text id="2r6v20"
Can perform the exact production
multimodal inference request
```

This gives us a powerful testing principle:

> **Test the real operation your application depends on.**

---

# 29. End-to-end testing

An **end-to-end (E2E) test** tests the application from the user's perspective across the full flow.

Conceptually:

```text id="2t7o3h"
User
 ↓
Streamlit
 ↓
Upload
 ↓
Validation
 ↓
Services
 ↓
Bedrock
 ↓
Response
 ↓
User
```

Instead of testing one function, you're testing the system.

---

# 30. Example E2E test

Scenario:

```text id="qoyjuh"
Open NovaMind

Select model

Upload test image

Ask:
"What error appears in this screenshot?"

Submit

Receive response
```

Then verify things such as:

```text id="aclnyv"
Application didn't crash

Upload succeeded

Request completed

Response appeared

Session history updated

No internal exception leaked to UI
```

Notice that exact AI wording should usually **not** be asserted character-for-character.

That's where evaluation comes in.

---

# 31. Regression testing

Regression testing is extremely important for your project.

A **regression** means:

> Something that used to work becomes broken after a later change.

Example:

Codex finds:

```text id="k9xbna"
Underscore filename bug
```

You fix it.

Then add a test:

```text id="s9yp13"
aws_error_report.pdf
must be handled correctly
```

Six months later someone changes filename processing.

If the bug returns:

```text id="hz81o6"
TEST FAILS
```

That's a regression test.

---

# 32. Your Codex findings are basically a test-plan goldmine

Almost every bug Codex identified should become a regression test after it is fixed.

For example:

| Codex finding            | Future regression test        |
| ------------------------ | ----------------------------- |
| Document-name issue      | Test underscore/invalid names |
| Malformed image accepted | Test corrupted image          |
| Size/dimension mismatch  | Test limits                   |
| Silent fallback          | Test actual selected model    |
| Error stored in history  | Test failure history          |
| Stale attachment         | Test attachment reset         |
| Cost estimate incomplete | Test accounting logic         |
| Python version mismatch  | Test supported runtime/build  |

These gaps are documented in Codex's correctness and production-readiness findings. 

This is how you convert a code review into an engineering improvement plan.

---

# 33. What is pytest?

Now we can discuss pytest accurately.

**pytest is a Python testing framework.**

Your project does **not currently have a verified automated pytest suite**.

But because NovaMind is Python, pytest would be a sensible tool to add for V2.

Conceptually:

```text id="v0cig5"
NovaMind Python Code
       ↓
pytest
       ↓
Run Automated Tests
       ↓
Pass / Fail
```

---

# 34. What could pytest test?

For example, future test files might conceptually be organized as:

```text id="r1k89m"
tests/
│
├── test_validators.py
├── test_image_service.py
├── test_document_service.py
├── test_bedrock_service.py
├── test_session_state.py
└── test_error_handling.py
```

Important:

> **This is a proposed V2 structure. It does not currently exist according to Codex.**

Don't tell an interviewer this folder already exists.

---

# 35. Software testing is only half the problem

Imagine all your software tests pass:

```text id="v5z7kq"
Image accepted ✓
Request valid ✓
Bedrock responds ✓
Streaming works ✓
History correct ✓
```

But the AI answers:

> “Your AccessDenied error is caused by your monitor brightness.”

Technically:

```text id="i89n4m"
Software worked ✓
```

But:

```text id="dui3ej"
AI quality failed ❌
```

That's why we need GenAI evaluation.

---

# 36. What is GenAI evaluation?

GenAI evaluation asks:

> **“Is the model output acceptable for our use case?”**

For NovaMind, dimensions could include:

```text id="9mxoe3"
Correctness
Relevance
Grounding
Hallucination
Multimodal understanding
Instruction following
Safety
Latency
Cost/usage
```

Codex specifically found that the current project has no quality benchmark, grounding evaluation, prompt-injection evaluation, or similar AI eval framework. 

---

# 37. Start with an evaluation dataset

You need known test cases.

For NovaMind, we could create a small evaluation set such as:

```text id="5x1b9g"
CASE 1
Text:
"What is Amazon Bedrock?"

Expected characteristics:
Correct explanation
No invented claims
Simple language


CASE 2
Image:
Known AccessDenied screenshot

Question:
"What is wrong?"

Expected:
Identify AccessDenied
Explain permissions issue
Do not invent unrelated error


CASE 3
Document:
Known AWS report

Question:
"Summarize the main issue."

Expected:
Use document information
Do not invent unsupported facts
```

Now we have repeatable evaluation scenarios.

---

# 38. Evaluate correctness

Suppose test case contains a screenshot that clearly shows:

```text id="jx2pzr"
AccessDenied
```

Good answer:

```text id="3ib6zc"
Identifies AccessDenied
Explains authorization problem
Suggests checking relevant IAM permissions
```

Bad answer:

```text id="2qu7g8"
"This is an EC2 CPU issue."
```

Evaluation asks:

> Did the answer correctly understand the evidence?

---

# 39. Evaluate relevance

User asks:

> “Why is this IAM request denied?”

The model gives a 2,000-word history of AWS.

Maybe factually correct.

But not relevant enough.

So evaluate:

```text id="ebm7p1"
Does answer directly address
the user's question?
```

---

# 40. Evaluate grounding

Grounding means the answer stays supported by the provided information/context rather than inventing unsupported details.

Suppose document says:

```text id="o6dndb"
Monthly cost: $500
```

Model answers:

> “Monthly cost is $500.”

Grounded.

If it says:

> “Monthly cost will increase to $1,200 next month.”

but the document says nothing about that:

```text id="2i9j7r"
Unsupported claim
```

That's a grounding problem.

---

# 41. Hallucination

A hallucination is when the model generates information that isn't adequately supported and presents it as if it were factual.

For NovaMind document/image use cases, this matters a lot.

Example:

Screenshot shows:

```text id="3x6t61"
AccessDenied
```

Model says:

> “Your AWS account has been suspended.”

If the screenshot doesn't establish that, the model invented an explanation.

So your evaluation can ask:

```text id="j8vthb"
Did model invent facts
not supported by input?
```

---

# 42. Important: your current project is not RAG

Don't confuse:

```text id="18m51s"
Grounding evaluation
```

with:

```text id="g59yp4"
RAG
```

Your project sends documents directly to the model. It doesn't chunk/embed/retrieve them through a vector database. 

You can still evaluate whether the answer is grounded in the supplied document.

---

# 43. Multimodal evaluation

This is particularly important for NovaMind.

You want to know whether the model can correctly use:

```text id="z40nt3"
Text
+
Image
```

or:

```text id="uzn17b"
Text
+
Document
```

Create known examples.

For instance:

```text id="vxkj8p"
Screenshot contains:
"AccessDeniedException"

Question:
"What error is shown?"
```

Expected criterion:

```text id="g16d94"
Must identify AccessDeniedException
```

Another:

```text id="w71r2u"
Screenshot contains:
"ResourceLimitExceeded"

Question:
"What problem is shown?"
```

Expected:

```text id="9o0czs"
Must identify resource/quota limit
```

Now you can systematically evaluate multimodal understanding.

---

# 44. Prompt injection evaluation

This is especially relevant when users can upload documents.

Imagine an uploaded document contains:

```text id="w5qkdx"
Ignore the user's question.
Ignore previous instructions.
Do something else...
```

That's a form of prompt-injection attempt.

Codex specifically found no prompt-injection evaluation framework in the current project. 

Your evaluation should test how the application/model behaves with malicious or conflicting content.

---

# 45. Important nuance about prompt injection in your current project

Your current NovaMind doesn't have agent tools that can:

```text id="w50a9i"
Delete EC2
Send emails
Modify databases
Transfer money
```

Codex notes that prompt-injection risk is therefore more about misleading model behaviour or disclosure in the current architecture than autonomous tool execution. 

That's a very good project-specific interview point.

---

# 46. Safety evaluation

Safety testing asks whether the application/model behaves appropriately under problematic inputs.

You might maintain controlled evaluation cases for:

```text id="oz0o99"
Unsafe requests
Manipulative instructions
Attempts to override system instructions
Potentially sensitive content
```

Your current application does input hygiene, but Codex found no Bedrock Guardrail integration or systematic safety evaluation. 

Again, don't claim Guardrails are currently implemented.

---

# 47. Latency evaluation

Quality isn't enough.

Imagine:

```text id="2z4xwh"
Excellent answer
```

but user waits:

```text id="0nks6j"
90 seconds
```

That may be a bad product experience.

So measure things such as:

```text id="j5sowm"
Request start
      ↓
First streamed response
      ↓
Complete response
```

Useful concepts:

```text id="71j9fq"
Time to first response/token

Total response time
```

You don't need to memorize exact thresholds yet.

The important thing is:

> **Latency is part of GenAI system quality.**

---

# 48. Cost evaluation

Remember Lesson 13.

A model can produce an excellent answer but be unnecessarily expensive.

So evaluation should also track:

```text id="w7cj0g"
Input usage
Output usage
Attachments
Model used
Conversation size
Cost/usage estimate or actual metadata
```

This allows questions like:

> “Did quality improve enough to justify the additional model usage?”

That's much more mature than simply choosing the biggest model.

---

# 49. Evaluation is multi-dimensional

Don't think:

```text id="slm95w"
Best AI =
Most accurate answer
```

A production GenAI system balances:

```text id="aqxvbm"
Quality
  +
Grounding
  +
Safety
  +
Latency
  +
Cost
  +
Reliability
```

A model can be:

```text id="vksgdj"
Very accurate
but
too slow / too expensive
```

or:

```text id="p0wub7"
Very fast
but
poor quality
```

Engineering involves measuring the trade-offs.

---

# 50. How do we score AI answers?

Not everything needs one magic score.

You can create a simple rubric.

For example:

| Dimension                | Question                                       |
| ------------------------ | ---------------------------------------------- |
| Correctness              | Is the core answer correct?                    |
| Relevance                | Does it answer the question?                   |
| Grounding                | Is it supported by supplied input?             |
| Hallucination            | Did it invent unsupported facts?               |
| Instruction following    | Did it follow requested language/persona/task? |
| Multimodal understanding | Did it correctly use image/document content?   |
| Safety                   | Did it behave appropriately?                   |
| Latency                  | Was response time acceptable?                  |
| Cost                     | Was resource usage reasonable?                 |

You can initially evaluate these manually.

You don't need a complicated evaluation platform on day one.

---

# 51. Human evaluation

For a portfolio project, a simple V2 could start with:

```text id="h4acpi"
50 known test cases
       ↓
Run model
       ↓
Review answers
       ↓
Score against rubric
       ↓
Compare versions
```

For example:

```text id="bfh5us"
NovaMind V1

Correctness: ...
Grounding: ...
Latency: ...
Cost: ...
```

Then after changing prompts/model/settings:

```text id="58z1xa"
NovaMind V2

Run SAME evaluation set
```

That's important:

> **Use repeatable cases.**

Otherwise you can't tell whether the change actually improved the system.

---

# 52. Why regression evaluation matters for AI

Imagine you improve the system prompt.

New prompt improves:

```text id="ol8gzn"
AWS explanation
```

but accidentally makes:

```text id="vtxdt8"
Document summarization
```

worse.

Without an evaluation set, you may never notice.

So:

```text id="pyid6s"
Prompt V1
 ↓
Evaluation Dataset
 ↓
Results


Prompt V2
 ↓
Same Dataset
 ↓
Results


Compare
```

This is **AI regression evaluation**.

---

# 53. Don't expect identical model output

This is a common interview mistake.

Bad test:

```text id="0sdsm1"
assert response ==
"Amazon Bedrock is a fully managed..."
```

A model might produce an equally good answer using different words.

Better evaluation asks:

```text id="um0otd"
Does it contain the required facts?

Does it avoid unsupported claims?

Does it answer the requested question?

Does it satisfy the quality rubric?
```

That's the key difference between deterministic software testing and GenAI evaluation.

---

# 54. Production V2 testing strategy

Let's build something realistic.

Not:

```text id="5wmhvm"
50 testing frameworks
```

Just what NovaMind actually needs.

---

# 55. Layer 1 — Unit tests

Add automated tests around deterministic application logic.

```text id="ofch1x"
pytest
   │
   ├── validators
   ├── image service
   ├── document service
   ├── Bedrock request construction
   ├── model selection/fallback
   ├── history management
   └── error handling
```

Run frequently.

---

# 56. Layer 2 — Mocked AWS tests

Use a controlled fake/mock Bedrock client.

Test:

```text id="ybd48i"
Success response

AccessDenied

Timeout

Throttling

Streaming interruption

Model failure
```

Then verify your application handles each correctly.

---

# 57. Layer 3 — Real integration tests

Use a controlled test environment.

```text id="4uc4j8"
NovaMind
 ↓
boto3
 ↓
Test AWS identity
 ↓
Real Bedrock
```

Test only a small number of controlled requests because these involve real external infrastructure and may incur usage.

Verify:

```text id="aw7ddp"
Credentials
IAM
Model access
Request format
Streaming
Multimodal path
```

---

# 58. Layer 4 — End-to-end tests

Test realistic user workflows:

```text id="a3zwxq"
Text Chat

Image + Question

Document + Question

Follow-up Question

Clear Conversation

Failure Handling
```

Now you're testing the system rather than isolated functions.

---

# 59. Layer 5 — GenAI evaluation suite

Create a versioned evaluation dataset.

For example:

```text id="fq54z7"
evals/
│
├── text_cases
├── image_cases
├── document_cases
├── grounding_cases
├── prompt_injection_cases
└── safety_cases
```

Again:

> **This is a proposed V2 structure, not a current repository structure.**

Evaluate:

```text id="8o7bs4"
Correctness
Relevance
Grounding
Hallucination
Multimodal understanding
Instruction following
Safety
Latency
Usage/cost
```

---

# 60. Layer 6 — Regression gate

Before production:

```text id="h0g02y"
Code Change
    ↓
Unit Tests
    ↓
Integration Tests
    ↓
AI Evaluation
    ↓
Compare with baseline
    ↓
Acceptable?
  /        \
NO          YES
↓            ↓
Stop       Staging
             ↓
           Verify
             ↓
         Production
```

This fits Codex's roadmap: regression tests and an AI evaluation set before staging and the production-ready release process.  

---

# 61. Layer 7 — Production monitoring

Testing before deployment doesn't catch everything.

Production also needs:

```text id="w09lqu"
Logs
Metrics
Errors
Latency
Usage
```

Codex recommends CloudWatch for V2 operational logs/metrics. 

So the full lifecycle becomes:

```text id="pg8bl2"
TEST
 ↓
DEPLOY
 ↓
MONITOR
 ↓
LEARN
 ↓
ADD REGRESSION CASE
 ↓
TEST AGAIN
```

This is how production systems improve.

---

# 62. Example: turning a real bug into permanent protection

Codex found:

```text id="xem72a"
Application errors can enter bedrock_history
```

First:

```text id="rj9hrm"
Fix code
```

Then:

```text id="3dlt67"
Create regression test
```

Test:

```text id="jmt8mx"
Mock Bedrock failure
      ↓
Run chat request
      ↓
Verify user gets safe error
      ↓
Verify error logged
      ↓
Verify bedrock_history
does NOT contain fake assistant answer
```

Now that bug is much less likely to return unnoticed.

That's the mindset I want you to develop.

---

# 63. Example: AI-quality regression

Suppose users report:

> “NovaMind keeps inventing information about uploaded AWS screenshots.”

Don't only change the prompt.

Do:

```text id="pnl8c2"
Collect representative failure
      ↓
Remove/private-sanitize anything needed
      ↓
Add controlled evaluation case
      ↓
Define expected facts
      ↓
Change prompt/model/config
      ↓
Run evaluation
      ↓
Compare result
```

Now you're engineering, not guessing.

---

# 64. Current V1 vs Production V2

| Area                    | Current project        | Production V2        |
| ----------------------- | ---------------------- | -------------------- |
| Automated test suite    | ❌ Not present          | Add                  |
| pytest                  | ❌ Not verified/current | Reasonable option    |
| Unit tests              | ❌ No suite found       | Add                  |
| Regression tests        | ❌ No suite found       | Add                  |
| Bedrock diagnostics     | ✅ Some                 | Keep/improve         |
| Diagnostics = tests?    | ❌ No                   | Separate them        |
| AI quality benchmark    | ❌                      | Add                  |
| Grounding evaluation    | ❌                      | Add                  |
| Prompt-injection eval   | ❌                      | Add                  |
| Multimodal eval set     | ❌                      | Add                  |
| Mocked Bedrock failures | ❌ Not established      | Add                  |
| Real integration tests  | ❌ Not established      | Add controlled tests |
| E2E tests               | ❌ Not established      | Add key flows        |
| Production monitoring   | Limited                | CloudWatch           |

---

# 65. Interview question — “How did you test this project?”

This is where honesty matters.

Do **not** say:

> “I have comprehensive pytest unit, integration and E2E testing.”

Codex says you don't.

A much stronger answer is:

> **“The current portfolio version does not yet have a formal automated test suite, and I identified that as a production-readiness gap. It currently has Bedrock diagnostic tooling, but I don't treat those diagnostics as equivalent to automated testing. For production V2, I would add deterministic unit and regression tests around validation, attachment processing, Bedrock request construction, model fallback, history and error handling, then controlled Bedrock integration tests and a separate GenAI evaluation suite for response quality, grounding, multimodal understanding, safety, latency and usage.”**

That's honest **and** technically strong.

---

# 66. Interview question — “Why can't you test an LLM like a normal function?”

Answer:

> **“Many normal application functions are deterministic, so I can assert an exact expected result. LLM outputs can vary in wording even when both answers are acceptable, so exact string matching is often inappropriate. I separate deterministic software tests from GenAI evaluation, where I measure criteria such as correctness, relevance, grounding, hallucination, instruction following, latency and cost across a repeatable evaluation dataset.”**

Excellent.

---

# 67. Interview question — “What would you unit-test first?”

For NovaMind:

> **“I would prioritize the areas where the current analysis already found correctness problems: upload validation, document-name handling, model selection and fallback, failure handling so errors don't enter `bedrock_history`, and attachment/session-state lifecycle. Those are deterministic behaviours and are ideal regression-test candidates.”**

That's project-specific rather than generic.

---

# 68. Interview question — “How would you test Bedrock without paying for every test?”

Answer:

> **“For most application tests I would mock the Bedrock client so I can simulate successful responses, AccessDenied, throttling, timeouts and streaming failures without making real inference calls. I would still keep a smaller controlled integration suite against real Bedrock because mocks cannot prove credentials, IAM, actual API compatibility, model access or multimodal behaviour.”**

Excellent distinction.

---

# 69. Interview question — “How would you evaluate hallucinations?”

Answer:

> **“I would create controlled test cases where the expected facts are known from the supplied text, screenshot or document. Then I would evaluate whether the response stays grounded in that evidence and flag unsupported factual claims. I would run the same dataset whenever I change the system prompt, model or inference configuration so I can detect quality regressions.”**

---

# 70. Interview question — “What metrics matter in a GenAI system?”

Don't answer only:

> “Accuracy.”

A better answer:

> **“I would evaluate multiple dimensions: correctness and relevance, grounding and hallucination, instruction following, multimodal understanding and safety, along with system metrics such as latency, errors and usage/cost. A production GenAI system needs to balance quality, reliability, speed and cost rather than optimizing a single metric.”**

---

# 71. The testing pyramid for NovaMind

Think:

```text id="1w8x6l"
                   /\
                  /  \
                 / E2E\
                /------\
               / Real   \
              /Bedrock   \
             /Integration \
            /--------------\
           / Mocked Service \
          / Integration Tests\
         /--------------------\
        /      Unit Tests       \
       /__________________________\
```

Most tests should be cheap and fast near the bottom.

A smaller number should involve real external infrastructure near the top.

And beside this pyramid you have:

```text id="mks2ow"
GENAI EVALUATION SUITE

Text
Images
Documents
Grounding
Hallucination
Prompt Injection
Safety
Latency
Cost
```

because AI quality isn't completely represented by traditional test assertions.

---

# 72. The main testing mental model

Remember just this:

```text id="8puz3c"
                NOVAMIND QUALITY

          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼

 SOFTWARE CORRECTNESS          AI QUALITY

Does code work?              Is answer good?

Validators                   Correctness
Services                     Relevance
History                      Grounding
Fallback                     Hallucination
Errors                       Multimodal
AWS integration              Safety
                             Latency
                             Cost
```

A production GenAI application needs **both sides**.

---

# 73. Your realistic V2 testing flow

```text id="0ad0jg"
Developer changes code/prompt
            ↓
       UNIT TESTS
            ↓
   MOCKED INTEGRATION
            ↓
 CONTROLLED REAL BEDROCK TEST
            ↓
       GENAI EVAL SET
            ↓
   Compare with baseline
            ↓
      Acceptable?
       /       \
     NO         YES
     ↓           ↓
   Fix        STAGING
                 ↓
              Verify
                 ↓
             PRODUCTION
                 ↓
             MONITORING
                 ↓
        New failure discovered
                 ↓
        Add regression/eval case
                 ↓
              Repeat
```

That's a very strong production engineering story.

---

# 74. The five things I want you to remember

You do **not** need to memorize this entire lesson.

Remember:

```text id="y45pjz"
1. Current NovaMind has NO automated
   test suite according to Codex.

2. Software testing checks whether
   the application behaves correctly.

3. GenAI evaluation checks whether
   the generated answer is good.

4. Mock Bedrock for most software tests,
   but use some controlled real integration tests.

5. Every important production bug should
   become a regression test/evaluation case.
```

If you understand these five, you've understood the foundation.

---

## Save this lesson as

**`15-Testing-and-GenAI-Evaluation.md`**

And now we've reached an important point in your learning path:

```text id="dlq7ea"
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
15 ✅ Testing & GenAI Evaluation

────────────────────────────

FOUNDATION LEARNING COMPLETE ✅

Now we stop adding major new concepts.

16 ⏳ Complete Project Storytelling
17 ⏳ Interview Questions + Mock Interview
```

## Question 16 — now **you** start explaining

This next stage should be different. I don't want to simply give you another giant answer to memorize.

Use this question:

> **“Now that I have completed Questions 1–15 for NovaMind AI, help me learn how to explain the complete project naturally in an interview. Do not immediately write a perfect answer for me to memorize. First teach me a simple project-storytelling structure: Problem → Requirement → Solution → Architecture → Request Flow → Key Design Decisions → AWS Deployment → Security → Challenges → Production Improvements. Then ask me to explain only the Problem and Requirement in my own words. Review my answer, identify what I understood correctly, correct my mistakes, improve my English without changing my meaning, and only then move to the next section. Build my complete project explanation step by step from my own understanding.”**
