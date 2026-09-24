# 13 — Cost & Scalability

## Question

> **Can you teach me cost and scalability in my current NovaMind AI project from zero? Explain what parts of the architecture create cost, how Bedrock usage relates to input/output tokens and multimodal attachments, why growing `bedrock_history` can increase request size and cost, why my current cost counter is only approximate, what happens if 10, 100, or 1,000 users use the application, what Bedrock manages versus what my EC2/Streamlit application must scale, and what bottlenecks could appear. Then explain how I should think about cost control and scaling in production V2 without adding unnecessary AWS services, and show me how to answer cost/scalability questions in an interview.**

---

# 1. First: cost and scalability are different

These two concepts are related, but don't mix them up.

### Cost

Cost asks:

> **“How much does running my application consume/cost?”**

For example:

```text
More Bedrock requests
        ↓
More model usage
        ↓
Potentially higher cost
```

### Scalability

Scalability asks:

> **“Can my application continue working properly when usage increases?”**

For example:

```text
10 users
   ↓
100 users
   ↓
1,000 users
   ↓
Can the system still handle them?
```

So remember:

```text
COST
= How much resource/money usage?


SCALABILITY
= Can the system handle increasing load?
```

---

# 2. Where does cost come from in NovaMind?

At a high level, your documented architecture has two major operational areas:

```text
NovaMind AI
   │
   ├── Application infrastructure
   │       ↓
   │      EC2
   │
   └── AI inference
           ↓
      Amazon Bedrock
```

There can also be smaller surrounding costs depending on the deployed environment, but these are the two important concepts for your current architecture.

Codex describes EC2 as the documented hosting target and Bedrock Runtime as the managed foundation-model inference service. 

---

# 3. EC2 cost

EC2 is the server running your Streamlit/Python application in the documented deployment.

Conceptually:

```text
EC2
 │
 ├── Streamlit
 ├── Python
 ├── Your services
 └── boto3
```

Running compute infrastructure creates infrastructure cost.

An important idea is that EC2-style compute cost and Bedrock inference usage are **different cost sources**.

For example:

```text
EC2
↓
Application hosting


Bedrock
↓
AI model inference
```

Don't say in an interview:

> “Bedrock hosts my Streamlit application.”

It doesn't in this architecture.

---

# 4. Bedrock cost

Now we reach the more interesting GenAI part.

When NovaMind sends an inference request:

```text
NovaMind
   ↓
Amazon Bedrock
   ↓
Foundation Model
```

model usage occurs.

Your current application exposes models including Nova Pro, Nova Lite and Claude 3.5 Sonnet identifiers. 

Different models can have different usage characteristics and pricing.

So:

```text
Model A
```

and:

```text
Model B
```

should not automatically be assumed to have identical cost.

---

# 5. What are input and output tokens?

For text models, a useful mental model is:

```text
INPUT
Everything you send to model

OUTPUT
Everything model generates
```

Text is represented internally in smaller units commonly called **tokens**.

Don't think:

```text
1 token = exactly 1 word
```

That's not reliable.

Think:

> **Tokens are units the model uses to process text.**

---

# 6. What counts as input in NovaMind?

This is where many beginners make a mistake.

They think only this is input:

```text
User:
"What is Amazon Bedrock?"
```

But your request can contain much more.

Conceptually:

```text
BEDROCK REQUEST

System instructions
        +
Previous bedrock_history
        +
Current user question
        +
Optional image/document
        +
Other request configuration
```

Codex confirmed that the application sends previous history, the new message, optional attachment content, system instructions, and inference settings as part of the model interaction. 

So the user's visible new question may be short while the actual model request is much larger.

---

# 7. What is output?

Suppose you ask:

> “Explain this AWS error.”

The foundation model generates:

```text
The error indicates that...
```

That generated response is model output.

Your `max output` setting controls how much output the model is allowed to generate; Codex specifically noted that this setting limits **output**, not the size of all input/context sent to the model. 

That's an important distinction.

---

# 8. Why can a long answer cost more?

Conceptually:

```text
Short output
↓
Less generated content


Long output
↓
More generated content
```

So model-selection and output length can affect inference usage.

This is one reason why:

```text
max output
```

can matter for cost control.

But it doesn't solve your entire cost problem because your **input context can also grow**.

---

# 9. The biggest current cost issue: `bedrock_history`

Remember Lesson 7.

Your application has:

```text
chat_history
```

for display/export and:

```text
bedrock_history
```

for model context.

Codex found that previous model history is resent with later requests and there is no proper context-budget/history-trimming strategy. 

Let's see why this matters.

---

# 10. First message

User asks:

```text
Q1:
"What is Amazon Bedrock?"
```

Request is roughly:

```text
System Instructions
+
Q1
```

The model generates:

```text
A1
```

---

# 11. Second message

User asks:

```text
Q2:
"Which models can I use?"
```

NovaMind wants the model to understand what the conversation is about.

So it can send:

```text
System Instructions
+
Q1
+
A1
+
Q2
```

The request is now larger.

---

# 12. Third message

Now:

```text
System Instructions
+
Q1
+
A1
+
Q2
+
A2
+
Q3
```

And later:

```text
Q1 + A1
Q2 + A2
Q3 + A3
Q4 + A4
Q5 + A5
...
+
New Question
```

This is what context growth means.

---

# 13. Why can this increase cost?

Because you're not necessarily paying/consuming inference only for:

```text
New Question
```

The model also has to process the context supplied with the request.

Conceptually:

```text
Small history
     ↓
Smaller request


Large history
     ↓
Larger request
```

Therefore repeated context can increase model input usage.

This is exactly why Codex classified unbounded history as a cost/resource problem. 

---

# 14. Attachments make this more important

NovaMind isn't text-only.

It supports:

```text
Text
Images
Documents
```

And Codex found that attachment content can remain in `bedrock_history` and be resent with later requests. 

Imagine:

```text
Turn 1

Large document
+
Question
```

Then:

```text
Turn 2

Previous history
+
New question
```

Then:

```text
Turn 3

Previous history
+
New question
```

The application can repeatedly carry more context than the latest visible question suggests.

That affects:

```text
Request size
Server memory
Model context usage
Potential inference cost
```

---

# 15. Important nuance about multimodal pricing

Don't memorize:

> “Every image costs exactly X tokens.”

or:

> “Every PDF costs exactly Y.”

Codex's project analysis does **not** establish exact current pricing formulas for each model or modality.

The safe project-specific understanding is:

> **Images and documents contribute additional model input/work, and the current local cost estimator doesn't completely account for those attachments.**

Codex explicitly identified incomplete attachment accounting as a weakness of the current cost estimate. 

Exact pricing is model/provider-specific and can change.

---

# 16. Why is your current cost counter only approximate?

Your application displays approximate token/cost counters.

But Codex found that they are not complete accounting based on the actual Bedrock usage information and do not fully represent attachment-related input. 

So:

```text
NovaMind UI:

Estimated cost = $X
```

should be interpreted as:

```text
Application estimate
```

not:

```text
Exact AWS invoice
```

---

# 17. Real example

Suppose a user has:

```text
System prompt
+
10 previous Q&A turns
+
Uploaded PDF
+
Current question
+
Long generated answer
```

Your local calculation might estimate some text usage.

But the actual model interaction can involve additional usage associated with:

```text
Previous context
Attachments
Selected model
Actual generated output
```

Therefore:

```text
Local Estimate
       ≠
Guaranteed Actual Billing
```

That's the key lesson.

---

# 18. What should V2 do?

Codex recommends **actual usage accounting** as part of the production V2. 

Where the model/API provides usage information, the application should use that operational information rather than relying entirely on rough local estimates.

Conceptually:

```text
Bedrock Response
      ↓
Actual Usage Metadata
      ↓
Usage Accounting
      ↓
Monitoring / Controls
```

---

# 19. Now let's understand scalability

Imagine NovaMind works perfectly for:

```text
1 user
```

Does that prove it works for:

```text
1,000 simultaneous users?
```

No.

That's the scalability question.

---

# 20. What happens with 10 users?

Let's use a conceptual example rather than pretend Codex load-tested exact numbers.

Suppose 10 users are active.

Each user has:

```text
Browser
 ↓
Streamlit Session
 ↓
Conversation State
```

and they may independently call:

```text
Bedrock
```

So:

```text
          EC2 / STREAMLIT

User 1 ──────┐
User 2 ──────┤
User 3 ──────┤
...          ├──► Application
User 10 ─────┘
                   │
                   ▼
                Bedrock
```

This **may** work perfectly depending on request patterns, instance capacity, application behavior, and service limits.

We cannot claim an exact capacity because Codex did not perform a load test.

That's an important interview habit:

> **Don't invent performance numbers.**

---

# 21. What happens with 100 users?

Now pressure increases.

Potential issues include:

```text
More active sessions
       ↓
More session state
       ↓
More memory usage


More uploads
       ↓
More in-memory attachment data
       ↓
More memory pressure


More simultaneous requests
       ↓
More application work
       ↓
CPU/memory/network pressure


More Bedrock calls
       ↓
Higher inference usage
       ↓
Higher cost / possible service limits
```

The key word is **potential**.

Without load testing, we don't know exactly at which number your system becomes constrained.

---

# 22. What about 1,000 users?

The same pattern becomes more significant.

Conceptually:

```text
1,000 users
     │
     ├── Sessions
     ├── Conversation histories
     ├── Uploaded files
     ├── Streaming connections
     └── Bedrock requests
             ↓
         Application
             ↓
           Bedrock
```

At that point, assuming a single application instance will definitely be fine would be irresponsible without measurement.

But also don't say:

> “At 1,000 users it definitely crashes.”

We haven't measured that either.

The correct answer is:

> **Capacity must be determined through monitoring and load testing.**

---

# 23. What does Bedrock scale for you?

This distinction is extremely important.

Amazon Bedrock provides **managed model serving**.

Your project does not operate:

```text
GPU clusters
Model weights
Inference servers
Model-serving runtime
```

for the selected foundation model.

That is a major reason you chose Bedrock.

Codex specifically points out that Bedrock handles managed model serving, but that this does **not** mean the Streamlit application tier automatically scales. 

---

# 24. What does Bedrock NOT scale for you?

Bedrock doesn't magically scale:

```text
Your Streamlit server
Your Python process
Your session state
Your application memory
Your upload handling
Your network entry
```

So:

```text
Managed Bedrock
      ≠
Entire application automatically scalable
```

This is one of the most important answers in this lesson.

---

# 25. Think of two separate scaling layers

```text
              NOVAMIND

                  │
        ┌─────────┴─────────┐
        ▼                   ▼
 APPLICATION TIER       AI INFERENCE
        │                   │
 EC2 + Streamlit        Amazon Bedrock
        │                   │
 YOU must think          AWS manages the
 about capacity          model-serving layer
```

Even though Bedrock manages its service, your account/model may still be subject to service quotas and other limits.

Managed does not mean:

> “Infinite requests at any speed.”

---

# 26. Bottleneck #1 — EC2 resources

Your EC2 instance has finite:

```text
CPU
Memory
Network capacity
```

Suppose active sessions increase.

Eventually:

```text
More users
   ↓
More application work
   ↓
More resource consumption
```

The EC2 application tier can become a bottleneck before the managed model-serving architecture itself does.

---

# 27. Bottleneck #2 — Streamlit process

Your current application is a Streamlit-based layered monolith.

That keeps the architecture simple.

But all UI/application concerns are running through that application tier.

Potential pressure includes:

```text
Concurrent sessions
Streaming responses
Uploads
Session state
Application logic
```

Again, the exact capacity is unknown without measurement.

---

# 28. Bottleneck #3 — In-memory session state

Remember:

```text
chat_history
bedrock_history
pending attachments
settings
counters
```

are associated with application session state. 

If you have:

```text
1 user
```

that's small.

If you have many simultaneous users, there can be much more application state.

Especially if users maintain:

```text
Long conversations
+
Attachments
```

Memory pressure can increase.

---

# 29. Bottleneck #4 — Attachment handling

Codex notes that uploads are kept in memory, which is reasonable for the project's current scope. 

But imagine many users simultaneously upload documents/images.

Conceptually:

```text
User 1 → document
User 2 → image
User 3 → document
...
User N → document
```

Those uploads consume application resources.

This doesn't mean:

> “You must add S3 immediately.”

It means:

> **Understand the current architecture's resource behavior.**

---

# 30. Bottleneck #5 — Growing conversation context

This problem affects **both cost and scalability**.

```text
Longer history
    ↓
Larger requests
    ↓
More application memory
    +
More model input
```

So one design flaw can affect several dimensions:

```text
Cost
Scalability
Reliability
```

That's why Codex made bounded history a high-priority production improvement. 

---

# 31. Bottleneck #6 — Bedrock quotas/service limits

Even though Bedrock is managed, applications still need to account for the limits associated with the service/model/account configuration.

Conceptually:

```text
Application
 ↓
Many simultaneous model calls
 ↓
Bedrock service limits
 ↓
Possible throttling / rejected requests
```

Codex did not give us measured quota numbers for this project, so don't invent them.

The interview concept is:

> **Managed service scalability does not eliminate quotas and rate limits.**

---

# 32. Bottleneck #7 — Network and streaming connections

Your application streams model output back to the browser.

That improves UX.

But active streams also mean the application is managing ongoing connections/work while responses are being generated.

With:

```text
1 stream
```

that's trivial.

With:

```text
many concurrent streams
```

you need to understand the application tier's behavior under load.

Again:

**measure, don't guess.**

---

# 33. Bottleneck #8 — One application instance

Your current documented deployment is essentially:

```text
Users
  ↓
One EC2-hosted Streamlit application
```

Codex specifically says that the Streamlit server's capacity still matters even though Bedrock handles managed model serving. 

So the application server can become the scaling boundary.

---

# 34. Cost grows differently from traffic

Here's another important concept.

Suppose:

```text
100 users
```

does that mean exactly:

```text
100 × same cost?
```

Not necessarily.

Why?

Because users behave differently.

User A:

```text
2 short questions
```

User B:

```text
20 long questions
+ large document
+ long conversation history
```

Their AI usage can be very different.

So a better mental model is:

```text
Cost
≈
Number of requests
×
Size/type of model input
×
Generated output
×
Selected model/pricing
```

This is conceptual, not an exact billing formula.

---

# 35. Cost per USER matters more than only total users

Imagine:

```text
1,000 users
```

but each makes one tiny request.

Compare that with:

```text
100 users
```

each making hundreds of large multimodal requests.

The second scenario could potentially consume more AI resources.

So production planning should consider:

```text
Users
+
Requests per user
+
Request size
+
Conversation length
+
Attachments
+
Output size
+
Model choice
```

not just:

```text
Number of users
```

---

# 36. Production V2 — Start with measurement

A common mistake is:

> “We might get 1,000 users, so let's immediately build Kubernetes.”

No.

First:

```text
Measure
   ↓
Find bottleneck
   ↓
Improve bottleneck
   ↓
Measure again
```

This fits the simple, requirement-driven architecture approach Codex recommended. 

---

# 37. V2 Cost Control #1 — Bound conversation context

Current:

```text
Entire growing history
        ↓
Bedrock
```

V2:

```text
Conversation History
        ↓
Context Budget
        ↓
Bounded context
        ↓
Bedrock
```

This helps control:

```text
Request size
Model input usage
Memory pressure
```

Codex explicitly recommends bounded context. 

---

# 38. V2 Cost Control #2 — Usage accounting

Current:

```text
Approximate counter
```

V2:

```text
Bedrock interaction
      ↓
Actual usage information where available
      ↓
Usage accounting
```

Now you can understand usage rather than only estimate it.

---

# 39. V2 Cost Control #3 — User quotas

Once users have real identities, you can associate usage with them.

Conceptually:

```text
User A
 ↓
Usage = X

User B
 ↓
Usage = Y
```

Then:

```text
User
 ↓
Check quota
 ↓
Within limit?
 /       \
YES       NO
 ↓         ↓
Bedrock   Reject / limit
```

Codex explicitly recommends quotas/accounting for V2. 

---

# 40. V2 Cost Control #4 — Sensible model choice

Your project exposes multiple model options.

A production system shouldn't necessarily send every task to the most expensive/capable option simply because it exists.

The architecture question becomes:

> **What model capability does this request actually require?**

But be careful in interviews: your current project allows user model selection; Codex does not establish a sophisticated cost-based routing system.

So describe intelligent routing as a possible future design, **not something currently implemented**.

---

# 41. V2 Cost Control #5 — Control output

You already expose maximum output settings.

Reasonable output limits can prevent unnecessarily large generations.

But remember:

```text
Max output
```

doesn't solve:

```text
Huge input history
```

These are separate.

---

# 42. V2 Cost Control #6 — Attachment limits

Your application already has attachment validation/limits, although Codex identified correctness issues in that validation. 

Why do limits matter?

Because allowing arbitrarily large inputs can affect:

```text
Memory
Request size
Processing
Model usage
Reliability
```

So strict limits are both a correctness and resource-control mechanism.

---

# 43. V2 Scalability #1 — Monitor first

Codex recommends logs/metrics through CloudWatch in its realistic V2. 

You want to know things like:

```text
Application CPU
Memory pressure
Request volume
Error rate
Latency
Bedrock failures
Usage patterns
```

Then you can answer:

> “What is actually limiting my application?”

rather than guessing.

---

# 44. V2 Scalability #2 — Don't jump to Kubernetes

Suppose monitoring shows:

```text
EC2 CPU = low
Memory = healthy
Latency = healthy
Traffic = small
```

Would Kubernetes solve a current problem?

Probably not.

Codex explicitly says there is no immediate need for Kubernetes in the recommended V2. 

That's a strong interview point.

---

# 45. V2 Scalability #3 — Scale only when requirement appears

Suppose actual monitoring/load testing eventually shows:

```text
Single application instance
          ↓
Cannot handle required concurrency
```

Then you can consider evolving the deployment.

Codex lists containers/multiple replicas as an **optional later improvement**, not a current must-have. 

The reasoning should be:

```text
Measured bottleneck
       ↓
Requirement for more capacity
       ↓
Multiple application instances
```

not:

```text
AWS project
   ↓
Must use ECS/EKS
```

---

# 46. But session state creates an interesting scaling problem

This is important.

Current architecture:

```text
EC2 Instance
    ↓
Streamlit
    ↓
Session State
```

Imagine later you have:

```text
Instance A
Instance B
```

User starts conversation on A:

```text
A
↓
bedrock_history exists
```

Later their request reaches B.

Does B automatically have A's in-memory session data?

Not necessarily.

That's why application state becomes important when scaling horizontally.

This is one reason Codex lists persistent history as an optional improvement if the product requirements justify it. 

Don't solve this yet.

Just understand the relationship:

```text
In-memory state
      +
Multiple instances
      =
State-management question
```

---

# 47. When might S3 become useful?

Not because:

> “S3 is an AWS service.”

But because requirements might change.

Currently:

```text
Uploads
 ↓
Memory
```

If later you need:

```text
Large numbers of uploads
Persistent files
Files available across instances
Asynchronous processing
```

then durable object storage could make sense.

Codex explicitly lists S3 uploads as optional. 

Again:

```text
Requirement first
Technology second
```

---

# 48. When might containers become useful?

If you eventually need:

```text
Repeatable packaged runtime
Multiple application replicas
More sophisticated deployment/scaling
```

containerization may become useful.

But the current V2 does not need to start there.

---

# 49. Current vs V2

| Area            | Current               | Production V2 thinking             |
| --------------- | --------------------- | ---------------------------------- |
| Model inference | Bedrock               | Keep Bedrock                       |
| Model serving   | AWS managed           | Keep managed                       |
| App hosting     | EC2 target            | Can initially keep EC2             |
| History         | Growing               | Bound context                      |
| Attachments     | Can remain in history | Control/bound                      |
| Cost counter    | Approximate           | Better usage accounting            |
| User usage      | Limited controls      | Quotas                             |
| Monitoring      | Limited               | CloudWatch metrics/logs            |
| Capacity        | Not load-tested       | Measure/load-test                  |
| Scaling         | Single app tier       | Scale only when needed             |
| Persistence     | Session state         | Add persistence only if required   |
| S3              | Not required          | Optional if durable uploads needed |
| Containers      | Not current           | Optional when justified            |
| Kubernetes      | Not needed            | Don't add without requirement      |

---

# 50. Interview question — "How does your project control cost?"

For the **current version**, don't pretend it already has production cost controls.

Say:

> **“The current application has approximate token and cost counters, but Codex's analysis showed that these don't fully account for actual Bedrock usage or multimodal attachments. Another cost issue is that `bedrock_history`, including attachments, can grow and be resent with future requests. For production, I would use actual usage information where available, bound conversation context, enforce input/output limits, associate usage with authenticated users, and introduce quotas.”**

Excellent.

It admits the current limitation and explains the engineering response.

---

# 51. Interview question — "Does Bedrock make your application automatically scalable?"

Answer:

> **“No. Bedrock manages the foundation-model serving layer, so I don't manage the model weights or GPU inference infrastructure. But my Streamlit/Python application still has its own CPU, memory, session-state, upload-handling and concurrent-request constraints. I would monitor and load-test that application tier independently and scale it only when measurements show that it's necessary.”**

This is one of the strongest answers from this lesson.

---

# 52. Interview question — "What happens when traffic grows from 10 to 1,000 users?"

Don't say:

> “At 1,000 users my server crashes.”

You don't know that.

Say:

> **“I wouldn't claim a fixed capacity without load testing. As concurrent users increase, I would expect pressure on the Streamlit application through active sessions, in-memory conversation state, uploads, streaming connections and more Bedrock requests. Bedrock manages model serving, but the application tier still needs capacity planning. I would monitor CPU, memory, latency, error rates and request volume, then scale the measured bottleneck rather than prematurely introducing a more complex architecture.”**

Very strong.

---

# 53. Interview question — "How would you scale NovaMind?"

A good answer is:

> **“I would scale in stages. First I would fix unbounded context and usage accounting because those affect both cost and resource consumption. Then I would add monitoring and perform load testing on the current EC2/Streamlit deployment. If a single instance meets the required traffic, I would keep the simpler architecture. If the application tier becomes a measured bottleneck, then I would evaluate multiple instances or containerized deployment. At that point I would also revisit in-memory session state because state needs to work correctly across replicas.”**

Notice:

You didn't immediately say:

> “EKS.”

That's architecture thinking.

---

# 54. Interview question — "What are the main cost drivers?"

Answer:

> **“The two main areas are application infrastructure and AI inference. The EC2 side hosts the Streamlit/Python application, while Bedrock usage comes from model inference. On the AI side, usage depends on factors such as the selected model, the amount of input context, generated output and multimodal attachments. In my current project, conversation history can grow and be resent, so request size can increase over time.”**

---

# 55. Interview question — "Why is conversation history a scalability problem?"

Answer:

> **“Because the application keeps model conversation history and resends it for follow-up questions. As a conversation grows, each request can contain more context, and attachments may also remain in that history. That increases model input and can increase application memory and request size. In production I would enforce a context budget rather than allowing history to grow without bounds.”**

---

# 56. The most important cost formula to remember

Don't memorize AWS pricing numbers.

Remember this conceptual relationship:

```text
AI COST PRESSURE
        ↑
        │
Number of Requests
        ×
Input Size / Context
        ×
Output Size
        ×
Model Choice
        +
Multimodal Usage
```

Again, that's a **mental model**, not AWS's billing formula.

---

# 57. The most important scalability model

Think of NovaMind as two scaling problems:

```text
              NOVAMIND AI

                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼

APPLICATION SCALE        MODEL SCALE

EC2                      Bedrock
Streamlit                Managed inference
Python                   AWS operates serving
Sessions
Uploads
Streaming

YOU must measure         You still respect
and manage this          service limits/quotas
```

If you understand that diagram, you've understood most of this lesson.

---

# 58. Don't overengineer

The production journey should be:

```text
Current architecture
        ↓
Measure usage
        ↓
Bound resources
        ↓
Add cost controls
        ↓
Monitor
        ↓
Load test
        ↓
Identify bottleneck
        ↓
Scale only that bottleneck
```

Not:

```text
Maybe 1,000 users someday
        ↓
EKS + 15 microservices
```

Codex's roadmap follows the same principle: measurable usage and bounded resources come before production scaling decisions. 

---

# 59. What I want you to understand from Question 13

You do **not** need to memorize exact pricing.

You need to understand these five things:

```text
1. Bedrock inference creates AI usage/cost.

2. More context can mean more model input.

3. bedrock_history currently grows and
   attachments can be resent.

4. Bedrock manages model serving,
   NOT your Streamlit application's scaling.

5. Measure first, then scale the
   actual bottleneck.
```

If you can explain those five points naturally, you're already in a much better position for project interviews.

---

## Save this lesson as

**`13-Cost-and-Scalability.md`**

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

14 ⏳ Error Handling & Troubleshooting
15 ⏳ Testing & GenAI Evaluation

Then we stop adding major new project concepts.

16 ⏳ Complete Project Storytelling
17 ⏳ Mock Interview + Feedback
```

### Question 14 — Error Handling & Troubleshooting

> **“Can you teach me error handling and troubleshooting for my current NovaMind AI project from zero? Use the actual request flow and explain what can fail at each layer: browser/Streamlit, session state, upload validation, image/document processing, `bedrock_service.py`, boto3/AWS credentials, IAM permissions, Bedrock/model invocation, streaming responses, and EC2 deployment. For each failure, explain the likely symptom, possible cause, how I would isolate the problem step by step, and what logs/checks I should look at. Also explain the specific error-handling weaknesses Codex found in my current project and how production V2 should improve them. Finally, give me realistic troubleshooting interview scenarios and teach me how to answer them logically instead of memorizing fixes.”**
