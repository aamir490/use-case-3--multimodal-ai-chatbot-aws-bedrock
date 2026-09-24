# 12 — AWS Deployment

## Question

> **Can you teach me how my current NovaMind AI project is deployed on AWS from zero? Start from my code on my laptop and explain the complete path until a user can open the application in a browser. Explain EC2, the Python virtual environment, dependencies, Streamlit process, port 8501, security groups, AWS credentials/IAM role, Bedrock connectivity, and the current manual deployment flow identified by Codex. Then explain what happens when I update my code, what can go wrong during deployment, and how the production V2 deployment should differ. Keep current implementation and proposed V2 clearly separated.**

---

# 1. First understand what "deployment" means

While developing NovaMind AI, your project exists as files such as:

```text
Laptop
│
├── mod_chatbot_frontend.py
├── services/
│   ├── bedrock_service.py
│   ├── image_service.py
│   └── document_service.py
│
├── utils/
│   └── validators.py
│
└── requirements/dependencies
```

You can run the application on your computer.

But another person on the internet cannot automatically access a program running on your laptop.

**Deployment means putting the application into an environment where it can run and be reached by its intended users.**

For your documented current architecture, that hosting target is **Amazon EC2**. However, Codex explicitly noted that the repository does **not prove that an EC2 deployment is currently running**. So we should say:

> **“The repository documents EC2 as the deployment target.”**

rather than:

> **“Codex verified my production EC2 application is running.”**



That distinction matters.

---

# 2. Current deployment in one picture

The documented flow is approximately:

```text
YOUR LAPTOP
    │
    │ Source Code
    ▼
Git Repository
    │
    │ git clone / git pull
    ▼
AWS EC2 INSTANCE
    │
    ├── Python
    ├── Virtual Environment
    ├── Dependencies
    ├── NovaMind Source Code
    └── Streamlit Process
             │
             │ Port 8501
             ▼
          NETWORK
             │
             ▼
         USER BROWSER


Meanwhile:

Streamlit / Python
       │
       ▼
services/bedrock_service.py
       │
       ▼
      boto3
       │
       ▼
AWS Credentials / IAM authorization
       │
       ▼
 AMAZON BEDROCK
       │
       ▼
Foundation Model
```

That's the core deployment story.

Now we'll understand each piece.

---

# 3. What is EC2?

EC2 stands for:

**Amazon Elastic Compute Cloud**

Don't let the name make it complicated.

For this project, think of EC2 as:

> **A virtual computer/server running inside AWS.**

Your laptop has:

```text
CPU
Memory
Operating system
Storage
Network
Python
Applications
```

An EC2 instance also provides a computing environment where software can run.

So conceptually:

```text
Laptop
│
│ Development
│
▼
Code
│
│ Deploy
▼
EC2
│
│ Runs application
▼
Users
```

---

# 4. What actually runs on EC2?

A common beginner misunderstanding is:

> "My project is deployed on Bedrock."

That's not quite right.

In this architecture, there are two separate things:

```text
EC2
↓
Runs YOUR Streamlit/Python application


Amazon Bedrock
↓
Provides managed foundation-model inference
```

Your application code runs on the application server.

The foundation model is accessed through Bedrock.

Conceptually:

```text
                  AWS

        ┌──────────────────────┐
        │        EC2           │
        │                      │
User ──►│ Streamlit            │
        │ Python Services      │
        │ boto3                │
        └──────────┬───────────┘
                   │
                   │ AWS API
                   ▼
        ┌──────────────────────┐
        │   Amazon Bedrock     │
        │                      │
        │ Foundation Model     │
        └──────────────────────┘
```

You are **not hosting the foundation-model weights on your EC2 instance**. Codex's stack analysis identifies EC2 as a documented application-hosting target and Bedrock Runtime as the managed inference service. 

---

# 5. How does your code get from laptop to EC2?

Your documented deployment is manual.

One common path described by the project is conceptually:

```text
Laptop
   │
   │ Push code
   ▼
Git repository
   │
   │ Clone / pull
   ▼
EC2
```

So Git serves as a way of moving/versioning your application source.

For example:

```text
Laptop version:

NovaMind V1
     │
     ▼
Git Repository
     │
     ▼
EC2 gets V1
```

This is different from CI/CD.

At this point, a human is still performing the deployment steps.

---

# 6. Why does EC2 need Python?

Your application is written in Python.

Therefore the server needs an appropriate Python runtime.

Conceptually:

```text
NovaMind Python Code
        +
Compatible Python Runtime
        ↓
Application can execute
```

Codex found a documentation issue here: some project documentation advertises Python 3.9 while source syntax requires Python 3.10+. 

This is a real deployment problem.

Imagine:

```text
Documentation:
"Use Python 3.9"

Engineer:
Installs Python 3.9

Code:
Uses newer Python syntax

Result:
Application fails
```

That's why runtime versions matter.

---

# 7. What is a Python virtual environment?

You've probably used:

```text
venv
```

many times.

Now understand **why**.

Imagine EC2 contains several Python applications:

```text
Application A
needs package X version 1

Application B
needs package X version 2
```

Installing everything globally can create conflicts.

A virtual environment gives your application an isolated Python package environment.

Conceptually:

```text
EC2
│
├── System Python
│
└── NovaMind virtual environment
      │
      ├── Streamlit
      ├── boto3
      ├── Pillow
      ├── pypdf
      └── other project dependencies
```

The important idea is:

> **The virtual environment isolates the Python dependencies used by NovaMind from the server's general Python environment.**

---

# 8. What are dependencies?

Your Python files contain code that relies on external libraries.

For example, your current stack includes:

```text
Streamlit
boto3 / botocore
Pillow
pypdf
```



Your source code alone isn't enough.

The server also needs the libraries your code imports.

So deployment includes:

```text
Source Code
     +
Python
     +
Dependencies
     =
Runnable Application
```

This is why dependency installation is part of deployment.

---

# 9. Why does dependency reproducibility matter?

Codex found that your current dependency specifications use lower-bound-style constraints rather than a completely locked environment. 

Imagine:

```text
You deploy today
      ↓
Package version A


You rebuild months later
      ↓
Package version B
```

Version B may behave differently.

Then you get the classic problem:

> "But it worked before."

This is why dependency management is part of production engineering.

---

# 10. Now the Streamlit process starts

Once:

```text
Python installed
      +
Virtual environment created
      +
Dependencies installed
      +
Project code available
```

you can start the application.

Conceptually:

```text
streamlit run mod_chatbot_frontend.py
```

Now Python executes your Streamlit application.

The process remains running on the server and waits for requests.

---

# 11. What does "process" mean?

This is simple but important.

Your Python file is just a file:

```text
mod_chatbot_frontend.py
```

When Python/Streamlit starts executing it, you have a running **process**.

Think:

```text
FILE
↓
Instructions sitting on disk


PROCESS
↓
Those instructions actively executing
in memory/CPU
```

If the process stops:

```text
Source code still exists
        ↓
But application isn't serving users
```

That's why:

> **Having code on EC2 does not mean the application is running.**

---

# 12. What is port 8501?

This confuses many beginners.

Think of the EC2 instance as a building.

The server can run many applications.

Ports are like numbered doors.

For example:

```text
EC2 SERVER

Door 22
SSH

Door 80
HTTP

Door 443
HTTPS

Door 8501
Streamlit application
```

Streamlit commonly listens on:

```text
8501
```

So conceptually:

```text
User Browser
     │
     ▼
EC2-IP:8501
     │
     ▼
Streamlit
```

The browser connects to the server's network address and the port where Streamlit is listening.

---

# 13. But AWS networking must allow that traffic

Running Streamlit on port 8501 isn't enough.

AWS networking also needs to permit incoming traffic.

That's where the **security group** enters the picture.

Think of an EC2 security group as a network-level gatekeeper around the instance.

Conceptually:

```text
Internet
   │
   ▼
Security Group
   │
   │ Is this inbound traffic allowed?
   │
 ┌─┴───────────┐
 NO            YES
 │              │
Reject          ▼
             EC2:8501
                │
                ▼
            Streamlit
```

Important: Codex's report establishes the EC2/8501 deployment pattern, but it does not give us enough verified repository evidence to claim a specific current security-group rule set. 

So understand security groups conceptually, but don't invent exact current inbound rules.

---

# 14. Complete browser flow

Suppose the server is running.

The user opens the application.

Conceptually:

```text
USER
 │
 │ Browser request
 ▼
Internet
 │
 ▼
EC2 network endpoint
 │
 ▼
Security Group
 │
 │ Traffic allowed?
 ▼
Port 8501
 │
 ▼
Streamlit Process
 │
 ▼
mod_chatbot_frontend.py
 │
 ▼
NovaMind UI
 │
 ▼
USER SEES CHATBOT
```

At this point the user can see the application.

Notice:

**Bedrock has not necessarily been called yet.**

Simply loading the interface and invoking an AI model are separate operations.

---

# 15. Now the user asks a question

Suppose:

```text
User:
"What is Amazon Bedrock?"
```

Now the application flow you've already learned begins:

```text
Browser
 ↓
Streamlit
 ↓
Python application
 ↓
bedrock_service.py
 ↓
boto3
 ↓
AWS
```

But AWS now asks:

> **Is this caller allowed to invoke Bedrock?**

---

# 16. AWS credentials / IAM role

We covered this deeply in Question 11.

Your Python application needs an AWS identity.

Conceptually there are different development/deployment credential patterns.

For local development:

```text
Laptop
 ↓
Configured AWS credentials/profile
 ↓
boto3
 ↓
Bedrock
```

For AWS-hosted application architecture, the preferred conceptual pattern is:

```text
EC2
 ↓
IAM Role
 ↓
Temporary credentials
 ↓
boto3
 ↓
Bedrock
```

The current repository's deployment documentation contains some inconsistency between role-based access and `aws configure`, which Codex specifically called out. 

So don't claim the current documentation has one perfectly consistent credential strategy.

---

# 17. What happens when boto3 calls Bedrock?

Conceptually:

```text
bedrock_service.py
       ↓
     boto3
       ↓
AWS credentials identify caller
       ↓
IAM evaluates permissions
       ↓
Allowed?
   /        \
 NO         YES
 ↓           ↓
Error      Bedrock Runtime
              ↓
       Foundation Model
```

If permission is missing:

```text
AccessDenied
```

can occur.

If permission exists:

Bedrock processes the inference request.

---

# 18. What does "Bedrock connectivity" actually mean?

It isn't just:

> "The internet works."

For NovaMind to successfully use Bedrock, several things have to line up:

```text
Application running
       ↓
boto3 configured
       ↓
Valid AWS identity
       ↓
Correct AWS region/configuration
       ↓
Required IAM permission
       ↓
Requested model/profile available
       ↓
Bedrock API call succeeds
```

Your project contains diagnostic tooling around Bedrock/model access, but Codex warns that those diagnostics don't perfectly prove the same path used by every real application request. 

So:

```text
Diagnostic PASS
```

doesn't necessarily mean:

```text
Every chatbot request is guaranteed to work.
```

---

# 19. Complete current request architecture

Now put both deployment and AI inference together:

```text
                        USER
                          │
                          │ Browser
                          ▼
                      INTERNET
                          │
                          ▼
                   SECURITY GROUP
                          │
                          ▼
                     EC2 : 8501
                          │
                          ▼
                       STREAMLIT
                mod_chatbot_frontend.py
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
        Validators      Image       Document
                        Service      Service
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                   Bedrock Service
                          │
                          ▼
                        boto3
                          │
                          ▼
                  AWS AUTHORIZATION
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
                      STREAMLIT
                          │
                          ▼
                        USER
```

That's the deployment + application flow you should understand.

---

# 20. What is the CURRENT manual deployment flow?

Codex summarized the documented deployment approximately as:

```text
Prepare server
    ↓
Install Python / venv
    ↓
Install dependencies
    ↓
Configure AWS credentials or role
    ↓
Ensure model access
    ↓
Run diagnostics
    ↓
Start Streamlit
    ↓
Expose/use port 8501
```

Updates are essentially based on pulling changed code and restarting the application. 

The deployment documentation uses a manual background-process approach such as `nohup`; Codex specifically found no mature automated restart/rollback/HTTPS release mechanism in the repository. 

This is important because earlier we discussed process supervision as a **V2 improvement**. Don't claim the current implementation already has a verified `systemd` deployment.

---

# 21. What happens when you change your code?

Imagine you modify:

```text
services/bedrock_service.py
```

on your laptop.

The EC2 instance does **not automatically know** about that change.

You might have:

```text
Laptop
Version 2

EC2
Version 1
```

until deployment occurs.

---

# 22. Current update process

Conceptually:

```text
LAPTOP
 │
 │ Change code
 ▼
Test locally
 │
 ▼
Git commit
 │
 ▼
Git push
 │
 ▼
Repository
 │
 │
 │ Manually connect to EC2
 ▼
EC2
 │
 ▼
git pull
 │
 ▼
Restart Streamlit
 │
 ▼
V2 running
```

The key word is:

**manually**.

There isn't a repository-defined CI/CD system automatically doing all of this. Codex found no CI/CD implementation. 

---

# 23. Why do you need to restart?

Suppose the currently running Python process loaded:

```text
Version 1
```

into memory.

You run:

```text
git pull
```

Now disk contains:

```text
Version 2
```

But the existing process may still be running the previous application state/code.

So:

```text
git pull
   ↓
Files updated
```

is not always equivalent to:

```text
New application version running
```

A restart/reload step makes the running process start using the intended version.

---

# 24. What can go wrong during deployment?

This is where deployment knowledge becomes useful in interviews.

Imagine:

```text
Code works on laptop
```

but:

```text
Fails on EC2
```

Why?

There are many possible layers.

---

# 25. Failure 1 — Wrong Python version

Remember Codex's finding:

```text
Documentation
Python 3.9

Code
Requires 3.10+ syntax
```



Possible result:

```text
Application won't start
```

This is a **runtime compatibility failure**.

---

# 26. Failure 2 — Missing dependency

Suppose code contains:

```python
import streamlit
```

but Streamlit isn't installed in the active environment.

Result:

```text
ModuleNotFoundError
```

So you check:

```text
Correct virtual environment?
       ↓
Dependencies installed?
       ↓
Correct versions?
```

---

# 27. Failure 3 — Wrong virtual environment

Imagine:

```text
Environment A
 ↓
Dependencies installed

Environment B
 ↓
Application accidentally started here
```

Now packages appear to be "missing" even though you remember installing them.

This is why knowing which Python/venv the process uses matters.

---

# 28. Failure 4 — Streamlit isn't running

Everything can exist correctly:

```text
EC2 ✓
Python ✓
Dependencies ✓
Code ✓
```

but:

```text
Streamlit process ❌
```

Then the application isn't serving requests.

This is a **process problem**, not a Bedrock problem.

---

# 29. Failure 5 — Port/network access problem

Streamlit might be running perfectly:

```text
EC2
Streamlit
Port 8501
✓
```

but the user cannot reach it.

Then investigate the network path:

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
```

If the traffic isn't allowed/reachable, the browser can't access the app.

This is different from the application crashing.

---

# 30. Failure 6 — IAM AccessDenied

Maybe the UI works:

```text
User opens NovaMind
✓
```

but asking a question fails.

Then:

```text
Streamlit ✓
Python ✓
Network to app ✓

Bedrock call ❌
```

One possible cause:

```text
IAM permission
```

This is why troubleshooting should identify **which layer failed**.

---

# 31. Failure 7 — Wrong model or model availability

Codex found that your project exposes several model choices and also identified model-selection/fallback issues.  

So an application can successfully connect to AWS but still fail at model invocation.

That's different from:

```text
No AWS credentials
```

or:

```text
No internet/network
```

Again: identify the layer.

---

# 32. Failure 8 — Dependency update breaks application

Because current dependencies aren't fully locked, you could redeploy later and receive newer library versions. 

Then:

```text
Same source code
      +
Different dependency
      =
Different behavior
```

That's a reproducibility problem.

---

# 33. Failure 9 — New code contains a bug

Suppose:

```text
V1 works
```

You deploy:

```text
V2
```

V2 crashes.

What now?

Current deployment doesn't establish a mature automated rollback process. 

So recovery is more manual.

That's a major difference between:

```text
"Application deployed"
```

and:

```text
"Production release process"
```

---

# 34. Failure 10 — No strong monitoring

Imagine the app fails at 2 AM.

How do you know?

Or users report:

> "NovaMind is slow."

You need to answer:

```text
Is EC2 healthy?
Is Streamlit alive?
Are Bedrock calls failing?
What's the latency?
What error occurred?
When did it start?
```

The current repository doesn't establish mature production observability; CloudWatch appears among proposed/future concepts rather than the current implemented architecture. 

---

# 35. Troubleshooting mindset

Don't immediately say:

> "Bedrock is broken."

Walk through layers.

```text
USER CAN'T OPEN APP

Browser
 ↓
Network / Security Group
 ↓
EC2
 ↓
Streamlit process
 ↓
Python application


APP OPENS BUT AI DOESN'T ANSWER

Streamlit
 ↓
bedrock_service.py
 ↓
boto3
 ↓
AWS credentials
 ↓
IAM permissions
 ↓
Bedrock/model
```

This is a very important interview skill.

---

# STOP: Everything above describes the CURRENT documented approach

Now we move to:

# Production V2

Don't mix these two in an interview.

---

# 36. Why isn't the current deployment fully production-ready?

Codex found that the manual EC2 approach is adequate for a demo, but lacks a mature story for:

```text
Repeatable releases
Automatic restart/process supervision
Rollback
HTTPS
Production observability
Automated testing/release flow
```



So V2 doesn't necessarily mean:

> "Throw away EC2."

Codex's recommended V2 can still use a supervised Streamlit deployment on EC2. 

That's important.

---

# 37. V2 — Secure HTTPS entry

Current demo-oriented idea:

```text
User
 ↓
EC2 : 8501
 ↓
Streamlit
```

Production should expose a secure HTTPS path:

```text
User
 ↓
HTTPS
 ↓
Secure reverse proxy / entry layer
 ↓
Streamlit
```

Codex specifically recommended an HTTPS reverse-proxy pattern. 

Port 8501 can remain an **internal application port** rather than the public security architecture being designed around direct access to Streamlit.

---

# 38. V2 — Supervised Streamlit process

Current documented deployment uses a manual/background-process approach.

V2 should use process supervision.

Conceptually:

```text
EC2 boots
 ↓
Process supervisor
 ↓
Starts Streamlit
 ↓
Streamlit crashes?
 ↓
Controlled restart
```

Codex explicitly recommends a supervised Streamlit process. 

The important requirement is **process supervision**; Codex does not require one specific product in the report.

---

# 39. V2 — Repeatable release process

Current:

```text
Developer
 ↓
git pull
 ↓
restart
```

V2:

```text
Code Change
    ↓
Automated Tests
    ↓
AI Evaluation
    ↓
Build / Release
    ↓
Staging
    ↓
Verify
    ↓
Production
```

Codex's roadmap places testing and staging before the final production-ready step. 

---

# 40. V2 — Rollback

Suppose:

```text
V1 ✓
 ↓
Deploy V2
 ↓
V2 ❌
```

Production operations need a clear answer to:

> **How do we restore the previous known-good version?**

Conceptually:

```text
V2 failure detected
      ↓
Rollback
      ↓
Known-good V1
```

Codex explicitly included rollback capability in its V2 recommendation. 

---

# 41. V2 — CloudWatch

Codex recommends:

```text
Application
     │
     ├── Logs
     └── Metrics
          ↓
     CloudWatch
```



Now instead of:

> "The chatbot doesn't work."

you can investigate operational evidence.

For example:

```text
Request arrives
     ↓
Bedrock call starts
     ↓
Error occurs
     ↓
Application logs
     ↓
CloudWatch
```

---

# 42. V2 — IAM role and least privilege

The production application should have a clear AWS identity strategy.

Conceptually:

```text
EC2
 ↓
IAM Role
 ↓
Least-privilege policy
 ↓
Required Bedrock access
```

This avoids making deployment depend on manually stored long-lived AWS credentials.

We covered the reasoning in Question 11.

---

# 43. V2 — Authentication before expensive AI access

V1:

```text
Demo Login
 ↓
Application
 ↓
Bedrock
```

V2:

```text
User
 ↓
Real Identity Integration
 ↓
Authenticated
 ↓
Usage / quota controls
 ↓
Application
 ↓
Bedrock
```

This connects deployment security with AI cost/security controls.

Codex includes authenticated access, quotas/accounting, and least-privilege access in its recommended V2. 

---

# 44. Complete V2 deployment architecture

The realistic architecture Codex supports is still relatively simple:

```text
                         USER
                           │
                           ▼
                    HTTPS ENTRY
                           │
                           ▼
                   AUTHENTICATION
                           │
                           ▼
                ┌──────────────────┐
                │       EC2        │
                │                  │
                │ Process          │
                │ Supervision      │
                │      ↓           │
                │   Streamlit      │
                │      ↓           │
                │ Python Services  │
                │      ↓           │
                │     boto3        │
                └──────┬───────────┘
                       │
                       │ IAM Role
                       │ Least Privilege
                       ▼
                 AMAZON BEDROCK
                       │
                       ▼
               FOUNDATION MODEL


EC2 / Application / Bedrock-related telemetry
                    │
                    ▼
              AMAZON CLOUDWATCH
```

Alongside:

```text
SOURCE CODE
    ↓
AUTOMATED TESTS
    ↓
AI EVALUATION
    ↓
RELEASE
    ↓
STAGING
    ↓
VERIFICATION
    ↓
PRODUCTION
    ↓
ROLLBACK IF NEEDED
```

That's much closer to a real production story.

---

# 45. Notice what we did NOT automatically add

We did **not** automatically add:

```text
EKS
Kubernetes
ECS
Lambda
API Gateway
SQS
DynamoDB
OpenSearch
RAG
Microservices
```

Why?

Because Codex's V2 recommendation explicitly says there is no immediate need for Kubernetes, agents, a vector database, or a separate REST backend. 

Production-ready does not mean:

> **maximum number of AWS services.**

It means:

> **reliable architecture appropriate to the requirement.**

---

# 46. V1 vs V2

The simplest comparison:

| Area                   | Current documented approach | Production V2             |
| ---------------------- | --------------------------- | ------------------------- |
| Hosting                | EC2 target                  | EC2 can remain            |
| Application            | Streamlit                   | Keep Streamlit            |
| AI                     | Bedrock                     | Keep Bedrock              |
| Process                | Manual/background approach  | Supervised process        |
| Public access          | Demo-oriented               | HTTPS entry               |
| Auth                   | Demo login                  | Real identity             |
| AWS credentials        | Docs have mixed approach    | Clear role-based strategy |
| IAM                    | Broader guidance            | Least privilege           |
| Deployment             | Manual                      | Repeatable release        |
| Testing before release | Limited                     | Automated                 |
| Staging                | Not established             | Staging verification      |
| Rollback               | Not established             | Defined rollback          |
| Monitoring             | Limited                     | CloudWatch                |
| Dependencies           | Loose/inconsistent          | Reproducible environment  |

---

# 47. How to answer: "How is your project deployed?"

For the **current project**, say:

> **“The repository documents a manual EC2 deployment for the Streamlit application. The source code is placed on the EC2 instance, Python and a virtual environment are configured, project dependencies are installed, AWS credentials or an execution role provide access to Bedrock, and the Streamlit process serves the application on port 8501. The Python backend uses boto3 to call Amazon Bedrock for model inference. Updates currently involve pulling the latest code and restarting the application. I identified that this is suitable for a demo but still lacks a mature automated release, rollback, HTTPS and monitoring setup.”**

Notice that this answer is honest.

You don't claim things Codex couldn't verify.

---

# 48. Interview question: "What happens when you deploy new code?"

Answer naturally:

> **“In the current manual flow, after I push the code to the repository, the server needs to pull the updated version and restart the Streamlit process so the new application code is running. One limitation is that this doesn't provide a strong automated rollback or release-validation mechanism, which is something I would address in the production version.”**

---

# 49. Interview question: "The UI loads but Bedrock doesn't respond. How would you troubleshoot?"

This is a very good interview question.

Answer by layers:

> **“If the UI loads, I know the basic EC2, network and Streamlit path is working. Then I would focus on the Bedrock request path: check application errors, confirm which AWS identity boto3 is using, verify IAM permissions, verify region and model availability, and test the actual Bedrock invocation path. I would avoid immediately assuming the model service itself is the problem.”**

That's a strong troubleshooting answer because you isolate the failure.

---

# 50. Interview question: "The website won't open at all. Where do you start?"

Don't start with Bedrock.

Start:

```text
Browser
 ↓
Network reachability
 ↓
Security Group
 ↓
EC2 health
 ↓
Port/listener
 ↓
Streamlit process
 ↓
Application logs
```

Because Bedrock has nothing to do with rendering the initial application if the request never reaches Streamlit.

---

# 51. The most important deployment mental model

Don't memorize commands.

Understand the layers:

```text
                 DEPLOYMENT

SOURCE
  ↓
How does code reach the server?

RUNTIME
  ↓
Is correct Python available?

DEPENDENCIES
  ↓
Are required libraries installed?

PROCESS
  ↓
Is Streamlit actually running?

NETWORK
  ↓
Can users reach the application?

AWS IDENTITY
  ↓
Who is boto3 calling AWS as?

AUTHORIZATION
  ↓
Can that identity invoke Bedrock?

AI SERVICE
  ↓
Can Bedrock/model handle request?

OBSERVABILITY
  ↓
Can I understand failures?

RELEASE
  ↓
Can I safely update and rollback?
```

If you understand those layers, you can troubleshoot deployments rather than memorizing deployment commands.

---

# 52. Your complete project flow now

You should now be able to connect almost everything we've studied:

```text
Laptop
 │
 │ Source code
 ▼
Git
 │
 ▼
EC2
 │
 ├── Python
 ├── Virtual Environment
 ├── Dependencies
 │
 ▼
Streamlit Process :8501
 │
 ▼
User Interface
 │
 ▼
Input Validation
 │
 ├── Image Service
 └── Document Service
 │
 ▼
Bedrock Service
 │
 ▼
boto3
 │
 ▼
IAM Authorization
 │
 ▼
Amazon Bedrock
 │
 ▼
Foundation Model
 │
 ▼
Streaming Response
 │
 ▼
Streamlit
 │
 ▼
User
```

That is a major milestone: deployment is no longer separate from your application architecture. You can see the entire system from **source code → server → user → Bedrock → response**.

---

## Save this lesson as

**`12-AWS-Deployment.md`**

Your progress:

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

13 ⏳ Cost & Scalability
14 ⏳ Error Handling & Troubleshooting
15 ⏳ Testing & GenAI Evaluation
16 ⏳ Complete Project Storytelling
17 ⏳ Mock Interview + Feedback
```

### Question 13 — Cost & Scalability

> **“Can you teach me cost and scalability in my current NovaMind AI project from zero? Explain what parts of the architecture create cost, how Bedrock usage relates to input/output tokens and multimodal attachments, why growing `bedrock_history` can increase request size and cost, why my current cost counter is only approximate, what happens if 10, 100, or 1,000 users use the application, what Bedrock manages versus what my EC2/Streamlit application must scale, and what bottlenecks could appear. Then explain how I should think about cost control and scaling in production V2 without adding unnecessary AWS services, and show me how to answer cost/scalability questions in an interview.”**
