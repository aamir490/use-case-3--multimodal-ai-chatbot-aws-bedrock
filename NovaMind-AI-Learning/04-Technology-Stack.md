# 04 — Technology Stack

## Question

> **Can you explain the complete technology stack used in my current NovaMind AI project? For each technology, explain what it is, exactly where and why it is used in my project, and what would happen if we removed it. Separate the application technologies from AWS services.**

---

# Answer

Now we already understand:

```text
01 — What is NovaMind AI?       ✅
02 — Current Architecture       ✅
03 — Application Flow           ✅
04 — Technology Stack           ← WE ARE HERE
```

For this lesson, we will focus only on technologies that Codex found in your **current repository**, not technologies we might add later.

At the highest level, your stack is:

```text
NOVAMIND AI

APPLICATION TECHNOLOGIES
│
├── Python
├── Streamlit
├── boto3
├── Pillow (PIL)
├── PyMuPDF
├── python-dotenv
└── pytest

AWS
│
├── Amazon Bedrock
│   ├── Amazon Nova Pro
│   ├── Amazon Nova Lite
│   └── Claude 3.5 Sonnet
│
└── AWS IAM

DEPLOYMENT / OPERATIONS
│
├── Linux / Ubuntu EC2 host
├── Python virtual environment
├── systemd
└── Nginx
```

Codex identified these directly from the repository and its deployment documentation. 

Let's understand each one.

---

# Part 1 — Application Technologies

## 1. Python

### What is Python?

Python is the main **programming language** used to build NovaMind AI.

Your project is fundamentally a Python application.

For example:

```text
mod_chatbot_frontend.py

services/
├── bedrock_service.py
├── image_service.py
└── document_service.py

utils/
└── validators.py
```

These are Python modules. 

### Where is Python used?

Almost everywhere in your application:

```text
Python
│
├── Streamlit application
├── Input validation
├── Image processing
├── Document processing
├── Bedrock integration
├── Conversation management
├── Configuration
├── Cost calculations
└── Tests
```

### Why is Python needed?

Because it ties the entire application together.

Think of Python as the **foundation of the application code**.

```text
Python
   │
   ├── Streamlit
   ├── boto3
   ├── Pillow
   ├── PyMuPDF
   └── Application Logic
```

### What happens if we remove Python?

The current application simply cannot run.

You would have to rewrite the project in another programming language.

So:

> **Python = core programming language of NovaMind AI.**

---

# 2. Streamlit

### What is Streamlit?

Streamlit is a Python framework used to create interactive web applications.

In NovaMind AI, it provides the user-facing application and application server.

Codex found that the current project does **not** have a separate React frontend or REST backend. 

### Where is it used?

Primarily through:

```text
mod_chatbot_frontend.py
```

Streamlit handles things such as:

```text
Login
Chat interface
File upload
Model selection
Persona selection
Language selection
Settings
Conversation display
Streaming response
Session state
```



### Why is Streamlit needed?

It gives users a web interface without you needing to separately build something like:

```text
React frontend
       +
FastAPI backend
```

For this project's current architecture, Streamlit simplifies development considerably.

### What happens if we remove Streamlit?

Your Bedrock-related Python logic could theoretically still exist, but **the current web application would stop working**.

You would need another interface/framework to replace it.

So:

> **Streamlit = web UI + Python application server for the current project.**

---

# 3. boto3

This is one of the most important technologies for your AWS interviews.

### What is boto3?

**boto3 is the AWS SDK for Python.**

SDK = Software Development Kit.

It lets Python code communicate with AWS APIs.

### Where is boto3 used?

The important flow is:

```text
services/bedrock_service.py
        ↓
      boto3
        ↓
Amazon Bedrock Runtime
```

Codex found that normal chat uses the Bedrock Runtime `converse_stream` operation, while a connection check uses `converse`. 

### Why is boto3 needed?

Your application needs a programmatic way to say:

> “Bedrock, invoke this model with this conversation and attachment.”

boto3 provides that connection.

```text
Python Application
       ↓
     boto3
       ↓
AWS APIs
       ↓
Amazon Bedrock
```

### What if we remove boto3?

The application's **current implementation would lose its mechanism for calling Bedrock**.

You would have to replace it with another supported AWS API/client approach.

So:

> **boto3 = bridge between your Python code and AWS APIs.**

---

# 4. Pillow / PIL

### What is Pillow?

Pillow is a Python library for working with images.

You will often see:

```python
from PIL import Image
```

PIL refers to the Python Imaging Library API; Pillow is the maintained package used today.

### Where is it used?

Codex found it in the image-processing path:

```text
services/image_service.py
```

The image service handles image checks, dimensions, processing and thumbnails. 

Conceptually:

```text
Uploaded image
      ↓
Pillow
      ↓
Inspect / process image
      ↓
Image Service
```

### Why is it needed?

Because NovaMind AI supports images.

For example:

```text
aws-error.png
```

Pillow helps your Python application work with that image before it is sent onward in the model request.

### What if we remove Pillow?

The current image-processing implementation would break or need replacement.

Text chat might still be possible, but the current image features wouldn't work correctly.

So:

> **Pillow = image-processing library.**

---

# 5. PyMuPDF

Now let's look at documents.

### What is PyMuPDF?

PyMuPDF is a Python library for working with PDF documents.

### Where is it used?

Codex found it in:

```text
services/document_service.py
```

Your document service handles document validation, API formatting, preview extraction and naming. 

There's an important detail here.

Codex found that for PDFs, local extraction is used for **preview purposes**, while the full document bytes are sent to Bedrock. 

So don't say:

> “PyMuPDF extracts the document and that extracted text is what my model analyzes.”

That would misrepresent the current implementation.

### Why is PyMuPDF needed?

In the current implementation, it supports the application's local PDF/document handling and preview behavior.

### What if we remove it?

The existing PDF preview/extraction-related functionality would need to be changed or replaced.

It does **not necessarily mean Bedrock itself could no longer process documents**; we're talking specifically about your application's current local document-processing implementation.

So:

> **PyMuPDF = local PDF processing/preview support.**

---

# 6. python-dotenv

### What is it?

`python-dotenv` is a Python package used to load environment variables from a `.env` file.

For example, applications often have configuration such as:

```text
AWS_REGION=...
APP_SETTING=...
```

rather than hardcoding values directly in Python source code.

### Where is it used?

Codex identified `python-dotenv` as one of the runtime dependencies and noted that `.env.example` documents expected environment variables.  

### Why is it needed?

It helps separate **configuration** from **application code**.

Conceptually:

```text
.env
  ↓
python-dotenv
  ↓
Python Application
```

### What happens if we remove it?

If the application depends on loading `.env` configuration this way, you'd need another method of supplying that configuration.

So:

> **python-dotenv = local environment/configuration loader.**

---

# 7. pytest

### What is pytest?

pytest is a Python testing framework.

Instead of manually opening your chatbot after every code change and hoping everything works, automated tests can verify expected behavior.

### Where is it used?

Codex identified a `tests/` directory and `pytest` as a development dependency.  

### Why is pytest needed?

It helps detect regressions.

For example:

```text
Developer changes image validation
          ↓
Run pytest
          ↓
Existing tests execute
          ↓
PASS / FAIL
```

### What happens if we remove pytest?

The application can still run.

But you lose the project's current automated test framework, making changes riskier and forcing more manual verification.

This is an important distinction:

**Runtime technology:** needed while users use the application.

**Development technology:** primarily helps developers build/test it.

pytest belongs mainly to the second category.

---

# Part 2 — AWS Technologies

Now let's separate these from your Python libraries.

```text
Application
      ↓
AWS
├── IAM
└── Amazon Bedrock
```

---

# 8. AWS IAM

### What is IAM?

IAM stands for:

**Identity and Access Management**

It controls authentication/authorization for AWS resources and API actions.

### Where is IAM used in NovaMind AI?

Your Python application uses boto3 to call Bedrock.

AWS must determine whether the application's AWS identity has permission to invoke the model.

```text
Python
  ↓
boto3
  ↓
AWS authorization
  ↓
Amazon Bedrock
```

Codex found that IAM controls permission to invoke models. 

### Why is IAM needed?

Security.

Without proper authorization, arbitrary applications should not be able to consume Bedrock resources in your AWS account.

### What happens if the required IAM permission is removed?

The application may still start.

Streamlit may still appear.

Users may still type messages.

But when the application attempts the Bedrock operation, AWS can reject it with an authorization error.

So:

> **IAM = controls whether your application is allowed to invoke Bedrock.**

---

# 9. Amazon Bedrock

This is the core AWS AI service in this project.

### What is Amazon Bedrock?

Amazon Bedrock is an AWS managed service that provides access to foundation models through APIs.

### Where is it used?

The core path is:

```text
User
 ↓
Streamlit
 ↓
Python Services
 ↓
boto3
 ↓
Amazon Bedrock
 ↓
Foundation Model
```

Codex found no local model weights or GPU-serving infrastructure in your repository. 

### Why is Bedrock needed?

Your application needs access to a foundation model to generate AI responses.

Bedrock provides that managed access.

### What happens if we remove Bedrock?

This is a major one.

Your current application would lose its **Generative AI inference provider**.

The UI could theoretically still exist:

```text
Streamlit
Upload
Settings
```

but the core feature:

```text
Question → AI-generated answer
```

would stop unless another model provider or local model-serving solution replaced Bedrock.

So:

> **Amazon Bedrock = managed Generative AI inference service for NovaMind AI.**

---

# 10. Foundation Models

Amazon Bedrock and the foundation model are related, but they aren't exactly the same thing.

Think:

```text
Amazon Bedrock
     │
     └── access to model
             ↓
       Foundation Model
```

Codex found three selectable model IDs:

```text
Nova Pro
Nova Lite
Claude 3.5 Sonnet
```



### What do they do?

The selected foundation model is what actually processes the supplied content and generates the AI response.

So:

```text
Streamlit        → UI
Python           → application logic
boto3            → AWS SDK
IAM              → authorization
Bedrock          → managed model access
Foundation Model → generates AI output
```

This distinction is extremely useful to understand.

---

# Part 3 — Deployment Technologies

Your repository also documents an AWS deployment path.

Codex found the documented target as:

**Ubuntu EC2 + Python virtual environment + systemd + Nginx**, with DNS/TLS guidance. 

These are different from the application stack.

---

# 11. Amazon EC2

### What is EC2?

EC2 provides a virtual machine in AWS.

Your deployment documentation describes running the Streamlit application on an Ubuntu EC2 instance. 

Conceptually:

```text
AWS
 ↓
EC2
 ↓
Ubuntu
 ↓
Python
 ↓
Streamlit
```

### What if EC2 is removed?

For the documented deployment, you would need somewhere else to run the Streamlit application.

Bedrock does **not** host your Streamlit application.

That's a very useful distinction:

```text
EC2
→ hosts/runs your application

Bedrock
→ provides model inference
```

---

# 12. Python Virtual Environment

Your deployment documentation uses a Python virtual environment.

You've probably seen:

```text
.venv/
```

in your project.

Its purpose is to isolate the project's Python packages.

For example:

```text
NovaMind AI
   ↓
.venv
   ↓
Streamlit
boto3
Pillow
PyMuPDF
...
```

This helps prevent dependency conflicts with unrelated Python projects.

If removed, Python can still run, but dependency management becomes less isolated and more error-prone.

---

# 13. systemd

### What is systemd?

On Linux, systemd can manage your application as a service.

Instead of manually running Streamlit every time:

```text
streamlit run mod_chatbot_frontend.py
```

systemd can keep the application service running and manage startup/restarts according to its configuration.

Codex identified a systemd service in the deployment documentation. 

So:

> **systemd = process/service management for the deployed application.**

---

# 14. Nginx

### What is Nginx?

Nginx is a web server/reverse proxy.

Your deployment documentation places Nginx in front of Streamlit. 

Conceptually:

```text
Internet
   ↓
Nginx
   ↓
Streamlit
```

Nginx receives web traffic and forwards it to the Streamlit application.

The repository's deployment documentation also describes DNS and TLS guidance around this setup. 

---

# Complete Technology Map

Now connect everything:

```text
                     USER
                       │
                    Browser
                       │
                       ▼
                    NGINX
                       │
                       ▼
              STREAMLIT APPLICATION
                       │
              running with PYTHON
                       │
          ┌────────────┼────────────┐
          │            │            │
       Pillow       PyMuPDF     python-dotenv
          │            │            │
          └────────────┼────────────┘
                       │
                Python Services
                       │
                       ▼
                     boto3
                       │
               IAM Authorization
                       │
                       ▼
                AMAZON BEDROCK
                       │
                       ▼
              FOUNDATION MODEL
          Nova Pro / Nova Lite /
            Claude 3.5 Sonnet
                       │
                       ▼
               Generated Response
                       │
                       ▼
                   Streamlit
                       │
                       ▼
                     USER


Deployment host:

AWS EC2
  ↓
Ubuntu
  ↓
Python virtual environment
  ↓
systemd
  ↓
Streamlit

Development/testing:

pytest
```

One nuance: the repository documents this EC2/Nginx deployment path, but Codex also noted that the repository does **not prove the current live production state** of those AWS resources. 

---

# Don't confuse these technologies

This is the part I especially want you to understand.

| Technology         | Main job                                                   |
| ------------------ | ---------------------------------------------------------- |
| **Python**         | Programming language                                       |
| **Streamlit**      | Web UI + application server                                |
| **Pillow**         | Image processing                                           |
| **PyMuPDF**        | Local PDF handling/preview                                 |
| **python-dotenv**  | Environment/config loading                                 |
| **pytest**         | Automated testing                                          |
| **boto3**          | Python SDK for AWS                                         |
| **IAM**            | AWS authorization                                          |
| **Amazon Bedrock** | Managed access to foundation models                        |
| **Nova / Claude**  | Generate AI responses                                      |
| **EC2**            | Runs the deployed application in the documented deployment |
| **systemd**        | Manages the application process                            |
| **Nginx**          | Reverse proxy in front of Streamlit                        |

---

# One question you should now be able to answer

Suppose an interviewer asks:

> **“What is the difference between boto3, Amazon Bedrock and Nova Pro in your project?”**

Don't memorize this—understand it:

```text
boto3
   ↓
How my Python application communicates with AWS

Amazon Bedrock
   ↓
AWS managed service through which the application accesses the model

Nova Pro
   ↓
The foundation model that processes the supplied input
and generates the response
```

That's a very important distinction.

---

# Interview Answer

Later, you could summarize the stack like this:

> **“NovaMind AI is primarily built with Python and Streamlit. Streamlit provides the web interface and application server, while the application logic is separated into services for Bedrock integration, image processing and document processing. Pillow supports image handling, PyMuPDF supports local PDF preview processing, and boto3 is used to communicate with Amazon Bedrock. IAM controls authorization to Bedrock, and the application supports Bedrock foundation models including Amazon Nova Pro, Nova Lite and Claude 3.5 Sonnet. The repository also documents deployment on an Ubuntu EC2 instance using a Python virtual environment, systemd for process management and Nginx as a reverse proxy. pytest is used for automated testing.”**

Again: **don't memorize this yet.**

Understand the responsibility of each technology first.

## Save this lesson as

**`04-Technology-Stack.md`**

Your folder becomes:

```text
NovaMind-AI-Learning/
│
├── 01-Project-Overview.md
├── 02-Project-Architecture.md
├── 03-Application-Flow.md
├── 04-Technology-Stack.md
│
└── images/
    └── NovaMind-AI-Current-Architecture.png
```

### Question 5

Before moving into project problems or improvements, the next important topic should go deeper into the **core GenAI/AWS part**:

> **“Can you explain exactly how Amazon Bedrock works in my NovaMind AI project from zero? Explain what Bedrock is, what a foundation model is, how boto3 connects my Python application to Bedrock, what `converse` and `converse_stream` mean, how the selected model receives text/images/documents, and how the response comes back to my application. Use examples from my actual project and explain it in very simple English.”**

That can become **`05-Amazon-Bedrock.md`**.
