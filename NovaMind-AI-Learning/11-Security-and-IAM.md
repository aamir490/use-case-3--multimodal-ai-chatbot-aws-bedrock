# 11 — Security & IAM in NovaMind AI

## Question

> **Can you teach me security and IAM in my current NovaMind AI project from zero? Explain how my Python application gets permission to call Amazon Bedrock, the difference between authentication and authorization, IAM users vs IAM roles vs policies, why credentials should not be hardcoded, what least privilege means specifically for this project, what security weaknesses Codex found in my current implementation, and how security should work in the production V2. Use the actual NovaMind AI request flow and explain how I should answer security questions in an interview.**

---

# 1. Start with the most important idea

Your NovaMind AI has **two different security questions**:

```text
Question 1:
Who is the USER using NovaMind AI?
        ↓
USER AUTHENTICATION


Question 2:
Is the Python APPLICATION allowed
to call Amazon Bedrock?
        ↓
AWS AUTHORIZATION
```

These are related, but **not the same thing**.

A simple mental model is:

```text
Aamir logs into NovaMind
        ↓
"Who are you?"
        ↓
AUTHENTICATION

NovaMind calls Bedrock
        ↓
"Are you allowed to do this?"
        ↓
AUTHORIZATION
```

This distinction is fundamental.

---

# 2. What is authentication?

**Authentication means proving identity.**

In very simple English:

> **Who are you?**

Examples:

```text
Username + Password
OTP
Google login
Corporate SSO
```

Suppose you visit NovaMind AI.

The application asks:

```text
Who are you?
```

You provide credentials.

The system verifies them.

```text
User
 ↓
Login
 ↓
Identity verified
 ↓
Authenticated
```

That's **authentication**.

---

# 3. What does your CURRENT project do?

Your current NovaMind AI has a **demo sign-in mechanism**.

Codex explicitly identified this as demo authentication rather than a production identity system. 

So conceptually:

```text
CURRENT V1

User
 ↓
Demo Login
 ↓
Streamlit Application
```

That's fine for demonstrating the project.

But it shouldn't be described as enterprise-grade authentication.

---

# 4. What is authorization?

Authorization answers a different question:

> **What are you allowed to do?**

Suppose you're authenticated as:

```text
Aamir
```

That proves your identity.

But it doesn't automatically mean you're allowed to:

```text
Delete S3 buckets
Create EC2 instances
Invoke Bedrock models
Delete databases
Modify IAM users
```

Authorization determines which actions are permitted.

---

# 5. Authentication vs Authorization

Remember:

| Concept            | Question                    |
| ------------------ | --------------------------- |
| **Authentication** | Who are you?                |
| **Authorization**  | What are you allowed to do? |

Example:

```text
Airport

Passport
   ↓
Who are you?
   ↓
AUTHENTICATION


Boarding pass
   ↓
Are you allowed on this flight?
   ↓
AUTHORIZATION
```

Now apply this to NovaMind.

```text
USER
 ↓
Login
 ↓
Authentication


PYTHON APPLICATION
 ↓
Calls AWS Bedrock
 ↓
IAM checks permissions
 ↓
Authorization
```

---

# 6. Where does IAM enter your project?

Let's use the actual NovaMind flow.

You upload:

```text
aws-error.png
```

and ask:

> “Why am I getting this error?”

You already know:

```text
User
 ↓
Streamlit
 ↓
validators.py
 ↓
image_service.py
 ↓
bedrock_service.py
 ↓
boto3
```

Now something important happens.

Your Python code wants AWS to perform a Bedrock operation.

AWS needs to determine:

> **“Which AWS identity is making this request, and is that identity allowed to invoke the requested Bedrock resource/action?”**

That's where AWS credentials and IAM permissions matter.

Codex identified IAM as the authorization layer around the application's AWS calls; it does not transport the model input/output itself. 

---

# 7. Complete security flow

Conceptually:

```text
USER
 │
 │ Login
 ▼
NOVA MIND AI
 │
 │ User authentication
 ▼
STREAMLIT
 │
 ▼
Python Services
 │
 ▼
bedrock_service.py
 │
 ▼
boto3
 │
 │ AWS credentials identify
 │ the application
 ▼
AWS IAM
 │
 │ Is this identity allowed
 │ to invoke Bedrock?
 │
 ├── NO ──→ AccessDenied
 │
 └── YES
       │
       ▼
 AMAZON BEDROCK
       │
       ▼
 FOUNDATION MODEL
       │
       ▼
    Response
```

The key thing is:

> **IAM does not analyze your prompt. IAM determines whether the AWS request is authorized.**

---

# 8. What is IAM?

IAM stands for:

**Identity and Access Management**

It is AWS's system for controlling:

```text
WHO
can do
WHAT
on
WHICH AWS RESOURCES
```

For NovaMind, think:

```text
WHO?
NovaMind application's AWS identity

WHAT?
Invoke a Bedrock model

WHERE?
Amazon Bedrock / allowed model resources
```

---

# 9. IAM User vs IAM Role vs IAM Policy

These three terms cause a lot of confusion.

Let's separate them.

```text
IAM USER
= AWS identity

IAM ROLE
= Assumable AWS identity

IAM POLICY
= Permission rules
```

Now we'll understand them individually.

---

# 10. What is an IAM User?

An IAM user is a long-lived identity created inside an AWS account.

For example:

```text
IAM User
   ↓
aamir-dev
```

An IAM user can be given permissions.

Historically, programmatic users could also have long-lived access keys.

For local development, developers sometimes work with credentials configured in their AWS environment.

But that doesn't mean credentials should be written directly into Python source code.

---

# 11. What is an IAM Role?

A role is also an AWS identity, but it's designed to be **assumed** by an authorized principal/service rather than representing one permanently logged-in person with embedded long-lived keys.

This becomes very useful when your application runs on AWS infrastructure.

Imagine NovaMind running on EC2.

Instead of doing this:

```text
EC2
 │
 │ Hardcoded access key
 │ Hardcoded secret key
 ▼
Bedrock
```

the preferred architecture is conceptually:

```text
EC2
 │
 │ Attached IAM Role
 ▼
Temporary AWS credentials
 │
 ▼
boto3
 │
 ▼
Bedrock
```

The application can obtain AWS credentials through the AWS runtime credential mechanism rather than storing permanent secrets in your source code.

---

# 12. What is an IAM Policy?

An IAM policy describes **permissions**.

Think of it as a rules document.

Conceptually:

```text
IAM Role
   ↓
IAM Policy
   ↓
"Allow this Bedrock action"
```

A simplified conceptual policy might say:

```text
Effect:
Allow

Action:
Required Bedrock inference operation

Resource:
Approved model/profile resource
```

Don't focus on memorizing JSON yet.

Understand:

> **Role = identity the application operates as.**

> **Policy = permissions attached to/available to that identity.**

---

# 13. Very simple analogy

Imagine a company office.

### IAM User

```text
Aamir
```

An employee identity.

### IAM Role

```text
Server Operator
```

A role someone or something can assume under defined conditions.

### IAM Policy

```text
Server Operator can:
✓ View servers
✓ Restart application

Cannot:
✗ Delete company database
```

Policy defines permissions.

The same idea applies to AWS.

---

# 14. How does boto3 know the AWS credentials?

This is another important interview question.

Your code doesn't need to look like:

```python
boto3.client(
    "bedrock-runtime",
    aws_access_key_id="...",
    aws_secret_access_key="..."
)
```

and it shouldn't embed secrets that way.

Boto3 supports AWS's normal credential provider mechanisms.

The exact source depends on the environment.

For example:

```text
LOCAL DEVELOPMENT

Python
 ↓
boto3
 ↓
Configured AWS credentials/profile
 ↓
AWS
```

Whereas on AWS compute with a role:

```text
AWS HOST
 ↓
IAM Role
 ↓
Temporary credentials
 ↓
boto3 automatically discovers them
 ↓
AWS
```

Codex identified the use of standard AWS credential mechanisms and absence of hardcoded AWS keys as one of your project's strengths. 

---

# 15. Why shouldn't credentials be hardcoded?

Imagine you wrote:

```python
AWS_ACCESS_KEY = "..."
AWS_SECRET_KEY = "..."
```

and then pushed it to:

```text
GitHub
```

Now you've potentially exposed credentials.

Anyone who obtains valid credentials could attempt AWS operations permitted by those credentials.

The risk becomes:

```text
Source Code
    ↓
AWS Credentials
    ↓
GitHub / copy / leak
    ↓
Unauthorized AWS usage
```

That's why:

> **Code and credentials should be separated.**

---

# 16. Why are IAM roles better for an AWS-hosted application?

Consider two approaches.

### Approach A

```text
EC2
 ↓
Credentials stored manually
 ↓
Python
 ↓
AWS
```

Now you need to manage those credentials.

They can be:

```text
Copied
Leaked
Mishandled
Left in configuration
```

### Approach B

```text
EC2
 ↓
IAM Role
 ↓
Temporary credentials
 ↓
boto3
 ↓
AWS
```

This removes the need to embed long-lived application credentials in source code.

For an AWS-hosted application, that's a much stronger pattern.

---

# 17. What is least privilege?

This is one of the most common AWS interview concepts.

**Least privilege means:**

> Give an identity only the permissions it needs to perform its job, and no more.

Suppose NovaMind only needs to invoke approved Bedrock models.

A bad mental model would be:

```text
NovaMind Role
     ↓
AdministratorAccess
```

Why?

Because then the application could potentially have permissions unrelated to its job.

It doesn't need:

```text
Delete EC2
Create IAM users
Delete S3 buckets
Modify VPC
Delete databases
```

to answer a chatbot question.

---

# 18. Least privilege specifically for NovaMind

The application's job is approximately:

```text
Receive question
      ↓
Prepare request
      ↓
Invoke approved Bedrock model
      ↓
Receive response
```

Therefore its AWS permissions should match that responsibility.

Conceptually:

```text
NovaMind IAM Role
       │
       ├── Required Bedrock inference permissions
       │
       └── Only resources/models actually needed
```

Not:

```text
NovaMind IAM Role
       ↓
Full AWS Administrator
```

That's least privilege.

---

# 19. What did Codex find about your IAM setup?

This is important because we must separate:

```text
What the architecture says
```

from:

```text
What the deployment documentation actually recommends
```

Codex found that the architecture describes IAM in terms of least privilege, but deployment guidance recommends broader Bedrock access. 

So there is a mismatch.

Conceptually:

```text
Architecture says:

Least privilege
      ↓
Only necessary permissions


Deployment guidance:

Broad Bedrock permissions
```

That's a production-readiness gap.

---

# 20. Security weakness #1 — Demo authentication

Codex identified the current login as demo authentication. 

For a portfolio demo:

```text
Fine
```

For a public production application:

```text
Insufficient
```

Why?

Because production needs stronger answers to:

```text
Who is this user?
How was their identity verified?
What can they access?
Can their access be revoked?
```

---

# 21. Security weakness #2 — Limited abuse controls

Remember that every legitimate Bedrock request may consume billable inference.

Suppose someone automates:

```text
Request
Request
Request
Request
...
```

Without appropriate controls:

```text
Public Application
       ↓
Large request volume
       ↓
Bedrock usage
       ↓
Potential cost
```

Codex therefore identified missing authentication, quota and spending controls as an important production gap. 

This demonstrates an important lesson:

> **Security and cost are connected in GenAI applications.**

---

# 22. Security weakness #3 — HTML preview handling

Codex found that document preview content is inserted into HTML rendered with unsafe HTML enabled. 

In simple terms:

```text
User uploads document
        ↓
Extracted preview content
        ↓
Application inserts it into HTML
        ↓
Browser renders it
```

The security concern is that **untrusted user content and executable/rendered page markup shouldn't be casually mixed**.

You don't need to memorize a web-security exploit here.

Understand the boundary:

> Uploaded content should be treated as untrusted data.

---

# 23. Security weakness #4 — No explicit Bedrock Guardrail integration

Codex found no Bedrock Guardrail integration. 

Important:

Don't say:

> “Without Guardrails the application is completely insecure.”

That's incorrect.

Instead:

> **The application currently doesn't implement that additional model-safety/control layer.**

Security exists at multiple layers:

```text
User authentication
        ↓
Application validation
        ↓
AWS authorization
        ↓
AI safety controls
```

IAM and Guardrails solve different problems.

---

# 24. IAM is NOT an AI safety system

This distinction is very important.

Suppose someone asks:

> “Write something inappropriate.”

IAM doesn't analyze that content and decide whether the response is safe.

IAM asks:

```text
Is this AWS identity allowed
to invoke this AWS operation?
```

So:

```text
IAM
 ↓
AWS permissions
```

while AI safety mechanisms deal with different concerns.

Don't mix them up.

---

# 25. Security weakness #5 — HTTPS/public deployment

Codex found that the current documented deployment is demo-oriented and doesn't establish a complete HTTPS production path. 

Why does HTTPS matter?

Imagine:

```text
Browser
   ↓
Question / Document
   ↓
Internet
   ↓
Server
```

Those inputs could contain sensitive information.

HTTPS provides encrypted transport between client and the public endpoint.

So production architecture needs:

```text
Browser
   ↓
HTTPS
   ↓
Application
```

---

# 26. Security in V2

Now let's connect everything.

Codex's recommended V2 includes an authenticated user, HTTPS entry, identity integration, strict attachment validation, quotas/accounting, least-privilege AWS access, and CloudWatch logs/metrics. 

Conceptually:

```text
                         USER
                           │
                           ▼
                   AUTHENTICATION
                  Identity provider
                           │
                    Identity verified
                           │
                           ▼
                         HTTPS
                           │
                           ▼
                 STREAMLIT APPLICATION
                           │
                    Strict validation
                           │
                    Usage / quotas
                           │
                           ▼
                 bedrock_service.py
                           │
                           ▼
                         boto3
                           │
                           ▼
                    IAM ROLE / POLICY
                           │
                   Least privilege
                           │
                           ▼
                    AMAZON BEDROCK
                           │
                           ▼
                  FOUNDATION MODEL
                           │
                           ▼
                       RESPONSE


Application / AWS telemetry
          │
          ▼
      CloudWatch
```

That's the V2 security story.

---

# 27. One subtle correction: Cognito

In Lesson 9 we discussed **Amazon Cognito** as a sensible AWS identity option.

Codex's report specifically recommends **identity integration**, but doesn't mandate Cognito as the only implementation. 

So in an interview, it's safer to say:

> **“For V2 I would introduce real identity integration; on AWS, Cognito would be one reasonable option.”**

rather than:

> “Codex says Cognito is required.”

It doesn't.

This is exactly how you avoid claiming more than your architecture analysis supports.

---

# 28. Complete real example

Let's combine everything.

A production V2 user uploads:

```text
aws-error.png
```

and asks:

> “Why am I getting this AccessDenied error?”

### Step 1 — User authentication

```text
User
 ↓
Identity system
 ↓
Authenticated
```

Question:

> **Who are you?**

---

### Step 2 — Secure connection

```text
Browser
 ↓
HTTPS
 ↓
NovaMind
```

Protect transport.

---

### Step 3 — Application validation

```text
aws-error.png
 ↓
validators.py
 ↓
image_service.py
```

Check that the uploaded input is acceptable.

---

### Step 4 — Usage control

Conceptually:

```text
Authenticated user
       ↓
Within allowed usage?
     /       \
   NO         YES
   ↓           ↓
Reject       Continue
```

---

### Step 5 — Construct AI request

```text
bedrock_service.py

Previous history
+
Image
+
Question
+
System instructions
+
Inference settings
```

---

### Step 6 — boto3

Python uses boto3 to call Bedrock.

```text
Python
 ↓
boto3
```

---

### Step 7 — AWS identity

On an AWS-hosted deployment, the application should operate through an appropriate IAM role/credential mechanism.

```text
Application
 ↓
IAM Role
```

---

### Step 8 — IAM authorization

AWS evaluates:

> Is this application identity allowed to perform this Bedrock operation?

```text
Allowed?
 /    \
NO    YES
↓      ↓
403   Bedrock
```

---

### Step 9 — Bedrock inference

```text
Bedrock
 ↓
Selected Foundation Model
 ↓
Understand screenshot + question
 ↓
Generate response
```

---

### Step 10 — Monitoring

Operational information can be sent to:

```text
CloudWatch
```

for monitoring/troubleshooting.

That's your security flow from the user all the way to AWS.

---

# 29. Common interview trap

Interviewer:

> **“How did you secure access to Bedrock?”**

Don't answer:

> “I used Cognito.”

Why?

Because Cognito-style user authentication and Bedrock AWS authorization are different layers.

A better answer is:

> **“For the AWS side, the application should use an IAM role with least-privilege Bedrock permissions, and boto3 uses the AWS credential chain rather than hardcoded credentials. User authentication is a separate application-level concern.”**

Excellent distinction.

---

# 30. Another interview trap

Interviewer:

> **“Why not store AWS access keys in `.env`?”**

A `.env` file is better than literally embedding secrets in Python and committing them, but for an application running on AWS, an IAM role is generally a stronger architecture.

Why?

Because:

```text
.env credentials
      ↓
Still credentials you must store/manage
```

whereas:

```text
IAM Role
    ↓
Temporary credentials
    ↓
AWS-managed credential mechanism
```

reduces long-lived secret management in the application.

---

# 31. Another interview question

> **“What happens if the IAM role doesn't have Bedrock permission?”**

The application may be perfectly healthy.

Streamlit may work.

Python may work.

boto3 may work.

But:

```text
Application
     ↓
Bedrock request
     ↓
IAM evaluation
     ↓
DENIED
     ↓
AccessDenied-type failure
```

This distinction is important for troubleshooting.

An AWS `AccessDenied` problem doesn't automatically mean:

> “Bedrock is broken.”

It can mean the calling identity isn't authorized.

---

# 32. How to troubleshoot IAM problems

Think in this order:

```text
1. WHO is making the request?
        ↓
2. Which AWS credentials/role
   is boto3 actually using?
        ↓
3. What action is being requested?
        ↓
4. What permissions does the
   identity have?
        ↓
5. Is the relevant resource/model
   allowed and available?
```

Your repository even includes STS/model-access diagnostics, although Codex warns that those diagnostics aren't perfect substitutes for testing the real application path. 

---

# 33. Your security layers

Don't think:

> “IAM = all security.”

Think:

```text
             NOVAMIND SECURITY

Layer 1
User Identity
"Who is using my app?"
        ↓

Layer 2
Secure Transport
"Is traffic protected?"
        ↓

Layer 3
Input Validation
"Is this input acceptable?"
        ↓

Layer 4
Usage Control
"Should this user be allowed
to make this request?"
        ↓

Layer 5
AWS IAM
"Can this application perform
this AWS operation?"
        ↓

Layer 6
AI Safety Controls
"How should model inputs/outputs
be controlled/evaluated?"
        ↓

Layer 7
Monitoring
"What happened and are there
operational/security signals?"
```

That's called **defense in depth**: multiple security layers rather than relying on one mechanism.

---

# 34. The five IAM concepts you really need to remember

Don't memorize this entire lesson.

Remember:

### 1. Authentication

> **Who are you?**

### 2. Authorization

> **What are you allowed to do?**

### 3. IAM Role

> **The AWS identity your hosted application can operate as.**

### 4. IAM Policy

> **Defines allowed/denied AWS actions/resources.**

### 5. Least Privilege

> **Give only the permissions required for the application's job.**

For NovaMind:

```text
NovaMind Application
       ↓
IAM Role
       ↓
Least-privilege policy
       ↓
Required Bedrock access
```

---

# 35. Interview Answer — “How did you handle security?”

Don't memorize it word-for-word yet, but understand the structure:

> **“I separate user authentication from AWS authorization. On the AWS side, the Python application communicates with Amazon Bedrock through boto3, and AWS IAM determines whether the application's AWS identity is authorized to invoke the required Bedrock resources. I avoid hardcoding AWS credentials and prefer an IAM role for AWS-hosted deployment, with least-privilege permissions rather than broad access.**
>
> **The current project is still a demo-oriented implementation, so I identified production gaps including demo authentication, broader-than-needed Bedrock permissions in the deployment guidance, limited usage controls, unsafe document-preview handling, and no explicit Guardrail integration. For V2, I would use real identity integration, HTTPS, stricter input validation, per-user usage controls, least-privilege IAM and operational monitoring.”**

That's an interview answer backed by your actual project rather than a generic AWS security answer.

---

# 36. One final mental model

When your application calls Bedrock, imagine **three people at three doors**:

```text
USER
 │
 ▼
DOOR 1:
"Who are you?"
AUTHENTICATION
 │
 ▼
NOVAMIND
 │
 ▼
DOOR 2:
"Is this input/request allowed
by my application?"
APPLICATION SECURITY
 │
 ▼
boto3
 │
 ▼
DOOR 3:
"Is this AWS identity allowed
to invoke Bedrock?"
IAM AUTHORIZATION
 │
 ▼
AMAZON BEDROCK
 │
 ▼
FOUNDATION MODEL
```

If you understand those three doors, you understand the core security architecture of NovaMind AI.

---

## Save this lesson as

**`11-Security-and-IAM.md`**

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

12 ⏳ AWS Deployment
13 ⏳ Cost & Scalability
14 ⏳ Error Handling & Troubleshooting
15 ⏳ Testing & GenAI Evaluation
16 ⏳ Complete Project Storytelling
17 ⏳ Mock Interview + Feedback
```

### Question 12 — AWS Deployment

> **“Can you teach me how my current NovaMind AI project is deployed on AWS from zero? Start from my code on my laptop and explain the complete path until a user can open the application in a browser. Explain EC2, the Python virtual environment, dependencies, Streamlit process, port 8501, security groups, AWS credentials/IAM role, Bedrock connectivity, and the current manual deployment flow identified by Codex. Then explain what happens when I update my code, what can go wrong during deployment, and how the production V2 deployment should differ. Keep current implementation and proposed V2 clearly separated.”**
