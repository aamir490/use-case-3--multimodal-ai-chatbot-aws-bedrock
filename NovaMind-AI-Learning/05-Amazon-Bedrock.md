# 05 — Amazon Bedrock in NovaMind AI

## Question

> **Can you explain exactly how Amazon Bedrock works in my NovaMind AI project from zero? Explain what Bedrock is, what a foundation model is, how boto3 connects my Python application to Bedrock, what `converse` and `converse_stream` mean, how the selected model receives text/images/documents, and how the response comes back to my application. Use examples from my actual project and explain it in very simple English.**

---

# Answer

This is one of the most important parts of your project because **Amazon Bedrock is where your Generative AI inference happens**.

We'll build the idea from zero.

## 1. Start with one simple question: Who generates the answer?

Suppose a user uploads an AWS error screenshot and asks:

> **“Why am I getting this error?”**

You have several technologies involved:

```text
Streamlit
Python
boto3
IAM
Amazon Bedrock
Nova Pro
```

Which one actually generates the answer?

**The selected foundation model**, for example **Amazon Nova Pro**.

The responsibilities are different:

```text
Streamlit
   ↓
Collects input and displays output

Python code
   ↓
Prepares and controls the request

boto3
   ↓
Communicates with AWS

IAM
   ↓
Controls whether the AWS request is authorized

Amazon Bedrock
   ↓
Provides managed access to the model

Nova Pro
   ↓
Processes the supplied content
and generates the answer
```

Understanding these differences is the foundation for understanding Bedrock in your project. Codex found that your repository contains no local model weights or GPU-serving infrastructure; model inference is performed through Bedrock. 

---

# 2. What is a foundation model?

Before Bedrock, understand **foundation model**.

A foundation model is a large AI model trained on very large amounts of data and capable of performing many different tasks.

For example:

```text
Foundation Model
│
├── Answer questions
├── Summarize text
├── Explain code
├── Understand documents
├── Analyze images
├── Generate content
└── Continue conversations
```

In your repository, Codex identified model IDs corresponding to:

```text
Amazon Nova Pro
Amazon Nova Lite
Claude 3.5 Sonnet
```



Your application lets the user select a model.

Conceptually:

```text
NovaMind AI

Choose Model:

○ Nova Pro
○ Nova Lite
○ Claude 3.5 Sonnet
```

The selected model becomes the model your Bedrock request targets.

---

# 3. Then what exactly is Amazon Bedrock?

A common mistake would be saying:

> “Amazon Bedrock is my LLM.”

That's not quite right.

In your architecture, **Bedrock is the AWS managed service through which your application accesses supported foundation models**.

Think:

```text
                 Amazon Bedrock
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          Nova Pro  Nova Lite  Claude
```

Your application doesn't download Nova Pro onto your EC2 instance.

It doesn't run the model inside Streamlit.

It doesn't manage a GPU server for the model.

Instead:

```text
NovaMind AI
     ↓
Amazon Bedrock API
     ↓
Selected Foundation Model
```

That is why Codex noted that your repository contains **no model weights or GPU-serving infrastructure**. 

---

# 4. Why do you need Bedrock?

Imagine trying to build your application without a managed model service.

You might have to deal with model-serving infrastructure yourself:

```text
Download / obtain model
        ↓
Provision compute/GPU
        ↓
Load model
        ↓
Serve inference endpoint
        ↓
Scale infrastructure
        ↓
Operate model-serving stack
```

That's not what this project does.

Instead:

```text
Your Python Application
        ↓
Amazon Bedrock
        ↓
Foundation Model
```

Your project focuses on building the **AI application around the model**, while Bedrock provides the managed model-access layer.

---

# 5. But how does Python communicate with Bedrock?

Now we reach:

**boto3**

Remember:

> **boto3 is the AWS SDK for Python.**

Your project is written in Python.

Therefore, it needs a Python interface for making AWS API calls.

Conceptually:

```text
Python Application
       ↓
     boto3
       ↓
 AWS Bedrock Runtime API
       ↓
 Amazon Bedrock
```

In your project, this responsibility lives primarily in:

```text
services/bedrock_service.py
```

Codex identified this module as responsible for constructing model requests, streaming responses, fallback handling, and model-history updates. 

---

# 6. Bedrock vs boto3

This distinction is worth learning carefully.

Imagine you want to send a parcel.

**boto3 is like the delivery mechanism.**

**Bedrock is the managed AWS service you're communicating with.**

**Nova Pro is the AI model doing the actual inference.**

So:

```text
Python
  │
  │ uses
  ▼
boto3
  │
  │ calls
  ▼
Amazon Bedrock
  │
  │ provides access to
  ▼
Nova Pro
  │
  │ generates
  ▼
AI Response
```

Therefore, don't say:

> “boto3 generates my response.”

It doesn't.

---

# 7. What happens when your application starts?

Codex found that your application creates a Bedrock Runtime client using boto3. It also performs a connection check using the Bedrock `converse` operation. 

Conceptually:

```text
NovaMind AI starts
      ↓
Python / boto3
      ↓
Create Bedrock Runtime client
      ↓
Application can make Bedrock Runtime calls
```

The **Runtime** part matters because your application is invoking models for inference.

---

# 8. What is `converse`?

Now we're getting closer to the actual API.

Bedrock's **Converse API** provides a conversation-oriented interface for interacting with supported models.

Instead of your application having completely different conversation logic for every supported model, it can work with a more consistent message structure.

Conceptually:

```text
Application
     ↓
Converse API
     ↓
Selected supported model
```

Your request can contain conversation-style information such as:

```text
User message
Assistant message
User message
...
```

plus system instructions and inference settings.

Codex found that your project uses `converse` specifically for a connection check. 

---

# 9. What is `converse_stream`?

This is what your normal chatbot interaction uses.

Codex found:

```text
Normal chat
    ↓
converse_stream
```

while:

```text
Connection check
    ↓
converse
```



The important difference for your project is **streaming**.

Imagine the model generates:

> “The screenshot indicates an IAM AccessDenied error because your role does not have permission…”

With a non-streaming style, the application may wait for the completed response before displaying it.

Conceptually:

```text
Request
   ↓
Model generating...
   ↓
Model generating...
   ↓
Complete
   ↓
Full answer displayed
```

With streaming:

```text
Request
   ↓
"The screenshot..."
   ↓
"The screenshot indicates..."
   ↓
"The screenshot indicates an IAM..."
   ↓
"The screenshot indicates an IAM AccessDenied..."
   ↓
...
```

The user sees the answer progressively.

That's why your normal chatbot path uses:

**`converse_stream`**. 

---

# 10. What exactly is sent to Bedrock?

This is where everything we've learned starts connecting.

Your application doesn't simply send:

```text
"Why am I getting this error?"
```

Depending on the interaction, Codex found the request can involve:

```text
System instructions
        +
Previous conversation history
        +
Current user message
        +
Optional image/document
        +
Inference settings
```



Think of the request as a package:

```text
┌─────────────────────────────┐
│ BEDROCK REQUEST             │
│                             │
│ Selected model              │
│                             │
│ System instructions         │
│                             │
│ Previous messages           │
│                             │
│ Current user question       │
│                             │
│ Optional attachment         │
│   ├── image                 │
│   └── document              │
│                             │
│ Inference settings          │
│   ├── temperature           │
│   └── max output tokens     │
└─────────────────────────────┘
```

---

# 11. How does text work?

Let's start with the easiest case.

User asks:

> **“Explain AWS IAM in simple English.”**

There is no image or document.

Conceptually:

```text
User question
     ↓
Streamlit
     ↓
Bedrock Service
     ↓
Build request
     ↓
boto3
     ↓
converse_stream()
     ↓
Amazon Bedrock
     ↓
Selected Model
     ↓
Generated text
```

This is ordinary text-based inference.

---

# 12. How does an image work?

Now suppose the user uploads:

```text
access-denied.png
```

and asks:

> “Explain this error.”

Earlier we learned that the image goes through validation and image processing.

Eventually, the model request contains both:

```text
IMAGE
+
TEXT QUESTION
```

Conceptually:

```text
┌──────────────────────────┐
│ User Message             │
│                          │
│ Image:                   │
│ access-denied.png        │
│                          │
│ Text:                    │
│ "Explain this error."    │
└──────────────────────────┘
              ↓
         Amazon Bedrock
              ↓
      Selected model
              ↓
      Generated answer
```

Codex found that the service constructs a user message with the attachment block first and then the user's text. 

This is why we describe NovaMind AI as **multimodal**.

The application can work with more than just text.

---

# 13. Does Pillow understand the screenshot?

No.

This is an important distinction.

```text
Pillow
   ↓
Image handling / processing

Foundation Model
   ↓
Understanding the supplied image
and generating the response
```

So if someone asks:

> “Which technology analyzes the meaning of the screenshot?”

Don't answer:

> “Pillow.”

Pillow supports image processing in your Python application. The selected multimodal foundation model performs the AI interpretation of the image supplied in the request.

---

# 14. How does a document work?

Suppose the user uploads:

```text
AWS-report.pdf
```

and asks:

> **“Summarize this document.”**

The path becomes:

```text
AWS-report.pdf
      ↓
Streamlit
      ↓
Validators
      ↓
Document Service
      ↓
Bedrock Service
      ↓
boto3
      ↓
Amazon Bedrock
      ↓
Selected Foundation Model
      ↓
Summary
```

Codex found an important implementation detail:

**The full document bytes are sent to Bedrock.**

The local PDF text extraction is used for preview purposes. 

---

# 15. This is why your project is NOT RAG

This becomes much easier to understand now.

Your current document path is essentially:

```text
Document
   ↓
Bedrock Request
   ↓
Foundation Model
   ↓
Answer
```

There is no:

```text
Document
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Database
   ↓
Similarity Search
   ↓
Retrieve relevant chunks
   ↓
LLM
```

Codex explicitly classified the project as **direct document prompting, not RAG**. 

That's an important interview distinction.

---

# 16. What happens to conversation history?

Suppose:

**Question 1:**

> “What is IAM?”

Model answers.

Then:

**Question 2:**

> “Can you explain it with an example?”

For Question 2 to make sense, the model needs relevant context from the previous conversation.

Your application maintains:

```text
bedrock_history
```

for the structured model conversation. 

Conceptually:

```text
Previous:

User:
"What is IAM?"

Assistant:
"IAM stands for..."

             +

Current:

User:
"Explain it with an example."

             ↓

        Bedrock Request
```

So your application sends previous conversation context along with the new request.

---

# 17. Does Bedrock permanently remember the conversation?

For **this project**, don't think of Bedrock as a database storing your conversation.

Your application maintains conversation state in Streamlit session state and supplies the relevant history in subsequent requests. 

So:

```text
WRONG MENTAL MODEL

Bedrock
  ↓
"Bedrock permanently remembers
all of my users' chats."
```

Instead:

```text
YOUR CURRENT PROJECT

Streamlit Session State
        ↓
Stores conversation history
        ↓
Application sends history
with subsequent request
        ↓
Bedrock
```

---

# 18. What happens inside the selected model?

At a very high level, the model receives the supplied input/context and generates output.

You do **not** need to pretend that your application controls the model's internal neural-network processing.

From your application's perspective:

```text
Prepared Request
       ↓
Amazon Bedrock
       ↓
Selected Foundation Model
       ↓
Inference
       ↓
Generated Output
```

The important interview concept is:

**Inference** means using an already-trained model to generate a result from new input.

Your project is primarily doing **model inference**, not training the foundation models.

---

# 19. How does the answer come back?

Now Nova Pro starts generating an answer.

Because your normal chat path uses `converse_stream`, the response comes back progressively.

Conceptually:

```text
Nova Pro
   ↓
Amazon Bedrock
   ↓
Streaming events
   ↓
boto3
   ↓
bedrock_service.py
   ↓
Streamlit placeholder
   ↓
Browser
   ↓
User
```

Codex found that `bedrock_service.py` processes streaming events and the Streamlit interface updates while generation continues. 

---

# 20. Complete Bedrock flow using our real example

Now let's put everything together.

User uploads:

**`access-denied.png`**

and asks:

> **“Why am I getting this error and how can I fix it?”**

User selects:

**Nova Pro**

The complete Bedrock-related flow is:

```text
USER
 │
 │ access-denied.png
 │ +
 │ "Why am I getting this error?"
 ▼
STREAMLIT
mod_chatbot_frontend.py
 │
 ▼
VALIDATION / IMAGE PROCESSING
 │
 ▼
BEDROCK SERVICE
services/bedrock_service.py
 │
 │ Builds request:
 │
 ├── System instructions
 ├── Previous conversation
 ├── Image
 ├── User question
 └── Inference settings
 │
 ▼
boto3
 │
 │ converse_stream()
 ▼
AWS AUTHORIZATION
 │
 │ IAM determines whether
 │ the request is permitted
 ▼
AMAZON BEDROCK
 │
 │ Access selected model
 ▼
AMAZON NOVA PRO
 │
 │ Performs inference
 ▼
GENERATED RESPONSE
 │
 │ Streaming events
 ▼
AMAZON BEDROCK
 │
 ▼
boto3
 │
 ▼
BEDROCK SERVICE
 │
 │ Processes response stream
 ▼
STREAMLIT
 │
 │ Updates response progressively
 ▼
USER
```

That's the central Generative AI flow of your current NovaMind AI application.

---

# 21. One analogy to remember everything

Imagine a restaurant.

### You = Customer

You ask:

> “Please make me a pizza.”

### Streamlit = Waiter/UI

Receives what you want.

### Your Python services = Preparation staff

They organize the order and attachments.

### boto3 = Communication mechanism

Carries the AWS API request.

### IAM = Security check

Determines whether you're authorized to place that AWS request.

### Amazon Bedrock = Managed model-access service

Provides the mechanism for invoking the selected supported foundation model.

### Nova Pro = Chef

Actually produces the result.

### `converse_stream` = Food arriving progressively

Instead of waiting for everything before seeing anything, output is delivered incrementally.

It's not technically exact in every detail, but it's a useful mental model.

---

# 22. Five distinctions you should understand

### Bedrock vs Foundation Model

```text
Bedrock
→ Managed AWS service for model access

Nova Pro
→ Foundation model that generates the response
```

### boto3 vs Bedrock

```text
boto3
→ Python AWS SDK

Bedrock
→ AWS service boto3 communicates with
```

### `converse` vs `converse_stream` in your project

```text
converse
→ Used by your project's connection check

converse_stream
→ Used for normal streaming chat
```



### Pillow vs multimodal model

```text
Pillow
→ Processes images in your application

Foundation Model
→ Interprets supplied multimodal content
```

### Document prompting vs RAG

```text
Your current project:

Document → Bedrock → Model

NOT:

Document → Embeddings → Vector DB
→ Retrieval → Model
```

---

# 23. Interview Answer

Once you genuinely understand the above, you could explain:

> **“In NovaMind AI, I use Amazon Bedrock as the managed Generative AI service for accessing foundation models such as Amazon Nova Pro, Nova Lite and Claude 3.5 Sonnet. My Python application communicates with the Bedrock Runtime using boto3. The Bedrock service constructs a request containing the current user message, optional image or document, previous conversation history, system instructions and inference settings. For normal chat, the application uses the ConverseStream operation, so generated text can be streamed progressively back to the Streamlit interface. IAM controls whether the application's AWS identity is authorized to invoke Bedrock. The selected foundation model performs the actual inference, while my application is responsible for preparing the request, maintaining conversation state and displaying the response.”**

Don't memorize this word-for-word yet.

The important thing is that if an interviewer interrupts with:

> “What exactly does boto3 do?”

or:

> “Does Bedrock store your conversation?”

or:

> “Where is Nova Pro running?”

you understand the architecture well enough to answer.

---

## Save this lesson as

**`05-Amazon-Bedrock.md`**

Your learning folder is now:

```text
NovaMind-AI-Learning/
│
├── 01-Project-Overview.md
├── 02-Project-Architecture.md
├── 03-Application-Flow.md
├── 04-Technology-Stack.md
├── 05-Amazon-Bedrock.md
│
└── images/
    └── NovaMind-AI-Current-Architecture.png
```

## Question 6 — Recommended Next

Now that you understand how Bedrock works, the next concept I would study is **multimodal processing**, because text, images, and documents are central features of this project:

> **“Can you explain how multimodal processing works in my NovaMind AI project? Explain from zero what multimodal AI means, then separately show how text, images, and documents are processed in my actual project before they reach Amazon Bedrock. Explain the role of `validators.py`, `image_service.py`, `document_service.py`, and `bedrock_service.py`, and clearly explain what processing happens in my application versus what understanding is done by the foundation model.”**

Save that next lesson as **`06-Multimodal-Processing.md`**.
