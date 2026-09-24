# 03 — Application Flow

## Question

> **Using one real example from my project, can you explain the complete request/application flow step by step—from when a user submits a question or uploads an image/document until the final AI response appears on the screen? Explain what happens internally at every stage and which project files/services are involved.**

---

# Answer

Now that you understand **what NovaMind AI is** and its **architecture**, the next thing is understanding what actually happens when somebody uses it.

We'll use one realistic example throughout.

### Example

Suppose the user uploads an AWS error screenshot:

**`access-denied.png`**

and asks:

> **“Why am I getting this error and how can I fix it?”**

Assume the user selects **Amazon Nova Pro**.

At a high level, the request travels like this:

```text
User
 ↓
Streamlit UI
 ↓
Upload Validation
 ↓
Image Service
 ↓
Bedrock Service
 ↓
boto3
 ↓
Amazon Bedrock
 ↓
Nova Pro
 ↓
Streaming Response
 ↓
Streamlit
 ↓
User
```

Let's now go inside every stage.

---

# Step 1 — User opens NovaMind AI

The user first opens your Streamlit application in a browser.

The main application file is:

```text
mod_chatbot_frontend.py
```

Despite the word `frontend` in the filename, this isn't a React-style frontend talking to a separate backend.

This Python/Streamlit file is the main application entry point. Codex found that it handles the UI, demo authentication, settings, session state, upload workflow, streaming display, summaries, and cost estimates. 

Conceptually:

```text
Browser
   ↓
mod_chatbot_frontend.py
   ↓
Streamlit renders application
```

The user sees things such as the chat interface, upload controls, model selection, language/persona settings, and conversation history.

---

# Step 2 — User selects settings

Suppose the user selects:

```text
Model       → Nova Pro
Language    → English
Temperature → selected value
Persona     → selected persona
```

These aren't separate AWS services.

They're application settings that influence how the request is constructed.

Codex found that the effective system instructions combine the selected persona/custom prompt with the selected language instruction. 

So eventually your request contains more than:

```text
"Why am I getting this error?"
```

It also contains instructions/settings controlling how the model should respond.

---

# Step 3 — User uploads the screenshot

The user chooses:

```text
access-denied.png
```

Streamlit receives the upload.

Now your application needs to determine:

> What kind of file did the user upload, and can we process it?

This is where:

```text
utils/validators.py
```

becomes relevant.

Codex found that `validators.py` routes uploads to the appropriate service, sanitizes filenames/input, formats sizes, and supports transcript generation. 

Conceptually:

```text
access-denied.png
       ↓
mod_chatbot_frontend.py
       ↓
utils/validators.py
       ↓
"This is an image"
       ↓
Image processing path
```

---

# Step 4 — Image Service processes the image

Because this is an image, the request reaches:

```text
services/image_service.py
```

Its job is **not to understand the AWS error**.

That's the model's job later.

The image service deals with things such as image size/signature checks, dimensions, image processing, and thumbnails. 

Think:

```text
Uploaded image
      ↓
Image Service
      ↓
Validate
      ↓
Inspect/process
      ↓
Prepare image bytes
      ↓
Return result to application
```

The application can also prepare a preview so the user can see the uploaded image.

---

# Step 5 — The upload becomes a pending attachment

At this point, the user has uploaded an image, but that doesn't necessarily mean an AI request has already been sent.

The application keeps the attachment ready for the message.

Then the user submits:

> “Why am I getting this error and how can I fix it?”

Codex's analysis describes this sequence as upload validation/preparation followed by submission of the user's question. 

Now we have:

```text
Question
   +
Image
```

ready to become an AI request.

---

# Step 6 — User's text is prepared

The application also processes the user's text.

Codex found that the text is trimmed and capped at approximately **10,000 characters**. 

Conceptually:

```text
Raw user text
      ↓
Clean / limit input
      ↓
Prepared question
```

Now the application has:

```text
Prepared Question
        +
Validated Image
```

---

# Step 7 — Conversation history is considered

Suppose this isn't the user's first question.

Maybe earlier they asked:

> “What is IAM?”

and now they upload the screenshot.

Your application maintains conversation history.

Codex identified two histories:

```text
chat_history
```

and

```text
bedrock_history
```

They serve different purposes. 

### `chat_history`

Used for things such as:

* Displaying conversations
* Timestamps
* Filenames
* Thumbnails
* Transcript/export

### `bedrock_history`

Used for the model conversation.

It contains the structured user/assistant messages that can be sent with future Bedrock requests.

So conceptually:

```text
Previous conversation
        +
Current image
        +
Current question
        ↓
Next model request
```

---

# Step 8 — Bedrock Service constructs the request

Now we reach:

```text
services/bedrock_service.py
```

This is one of the most important files in the project.

Codex found that it builds model requests, streams responses, handles fallback behavior, and updates model history. 

The service constructs a user message containing the attachment block, if present, followed by the user's text. 

Conceptually, the model request now looks like:

```text
System Instructions
        +
Previous Conversation
        +
Image
        +
Current Question
        +
Inference Settings
        ↓
Amazon Bedrock Request
```

---

# Step 9 — What are the system instructions?

Remember your persona and language selections?

They become instructions telling the model how it should behave.

For example, conceptually:

```text
"You are an AWS assistant..."

"Respond in English..."

"Explain technical concepts clearly..."
```

These aren't additional AI models.

They're instructions sent to the selected foundation model.

Codex specifically notes that selecting a persona such as “Data Analyst” changes behavioral instructions; it doesn't give the application a separate Python execution tool or specialized trained model. 

---

# Step 10 — Inference settings are added

The application also sends inference settings.

Two examples are:

**Temperature** — influences sampling behavior.

**Maximum output tokens** — limits how much output the model can generate.

Codex specifically cautioned that temperature is not a factual-accuracy control, and maximum output tokens limits the response length rather than the total conversation size. 

Now our request conceptually contains:

```text
┌───────────────────────────┐
│ SYSTEM INSTRUCTIONS       │
│ Persona + Language        │
├───────────────────────────┤
│ PREVIOUS HISTORY          │
├───────────────────────────┤
│ IMAGE                     │
│ access-denied.png         │
├───────────────────────────┤
│ USER QUESTION             │
│ Why am I getting this...? │
├───────────────────────────┤
│ INFERENCE SETTINGS        │
│ Temperature, Max Output   │
└───────────────────────────┘
```

---

# Step 11 — boto3 sends the request to AWS

The Bedrock service doesn't communicate with AWS magically.

It uses:

**boto3 — AWS SDK for Python**

Codex found that normal chat uses:

```text
bedrock-runtime.converse_stream
```



So:

```text
bedrock_service.py
       ↓
boto3
       ↓
Bedrock Runtime API
```

---

# Step 12 — IAM authorizes the AWS call

Before AWS allows the operation, the application's AWS identity needs permission.

That's the IAM part.

Remember:

**IAM doesn't analyze the screenshot.**

It answers the security question:

> Is this AWS identity authorized to invoke the requested Bedrock operation/model?

Codex identified IAM as the authorization mechanism for model invocation. 

So conceptually:

```text
boto3 request
     ↓
AWS authorization check
     ↓
Allowed?
     ↓
YES
     ↓
Bedrock processes request
```

---

# Step 13 — Amazon Bedrock receives the request

Now Amazon Bedrock receives the model request.

This is where another distinction matters.

**Bedrock is the AWS managed service through which you're accessing the foundation model.**

Your project isn't running Nova Pro on your EC2 instance.

Your repository doesn't contain model weights or GPU-serving infrastructure. 

Conceptually:

```text
Your application
       ↓
Amazon Bedrock
       ↓
Selected Foundation Model
```

---

# Step 14 — Nova Pro processes the input

In our example, the user selected:

**Nova Pro**

The model receives the information supplied by the application.

Conceptually:

```text
Previous conversation
+
System instructions
+
Screenshot
+
Question
+
Inference settings
        ↓
     Nova Pro
        ↓
Generated response
```

This is where the actual Generative AI reasoning/generation happens.

---

# Step 15 — The response starts coming back

Your application uses **streaming**.

That means it doesn't necessarily wait until the entire answer has been generated.

Instead, text arrives progressively.

For example:

```text
"The screenshot..."
```

then:

```text
"The screenshot shows an AccessDenied..."
```

then:

```text
"The screenshot shows an AccessDenied error
because the IAM identity..."
```

and so on.

Codex found that response fragments update a Streamlit placeholder while generation continues. 

This is why the chatbot feels responsive.

---

# Step 16 — Streamlit displays the response

The response travels back conceptually as:

```text
Foundation Model
       ↓
Amazon Bedrock
       ↓
ConverseStream
       ↓
boto3
       ↓
Bedrock Service
       ↓
Streamlit
       ↓
Browser
       ↓
User
```

The user sees the answer being generated on screen.

---

# Step 17 — Conversation histories are updated

Once the interaction progresses, your application updates its conversation histories.

The readable conversation is used for the interface/export, while the structured Bedrock history supports subsequent model requests. 

So after our example, conceptually the application has:

```text
USER:
[access-denied.png]
Why am I getting this error and how can I fix it?

ASSISTANT:
The screenshot indicates...
```

Now the user can ask:

> “Can you show me an example IAM policy?”

The application can send relevant previous history along with that new question.

---

# Complete Request Flow

Now look at the whole thing together:

```text
USER
 │
 │ Upload access-denied.png
 │ Ask: "Why am I getting this error?"
 ▼
STREAMLIT
mod_chatbot_frontend.py
 │
 ├── UI
 ├── Settings
 ├── Session State
 └── Upload Handling
 │
 ▼
VALIDATORS
utils/validators.py
 │
 │ Identify / validate upload
 ▼
IMAGE SERVICE
services/image_service.py
 │
 │ Process / prepare image
 ▼
STREAMLIT APPLICATION
 │
 │ User submits question
 ▼
BEDROCK SERVICE
services/bedrock_service.py
 │
 ├── Previous bedrock_history
 ├── System instructions
 ├── Image
 ├── Question
 └── Inference settings
 │
 ▼
boto3
 │
 │ converse_stream()
 ▼
AWS AUTHORIZATION
 │
 │ IAM permissions
 ▼
AMAZON BEDROCK
 │
 ▼
NOVA PRO
 │
 │ Generates response
 ▼
AMAZON BEDROCK
 │
 │ Streaming response
 ▼
BEDROCK SERVICE
 │
 ▼
STREAMLIT
 │
 │ Displays response progressively
 ▼
USER

Meanwhile:

chat_history    ← UI / export history
bedrock_history ← model conversation history
```

That is the core **end-to-end application flow** Codex found in your current project. 

---

# What changes if the user uploads a document?

Most of the flow remains the same.

Only the file-processing path changes.

For an image:

```text
Upload
 ↓
Validators
 ↓
Image Service
 ↓
Bedrock Service
```

For a document:

```text
Upload
 ↓
Validators
 ↓
Document Service
 ↓
Bedrock Service
```

`document_service.py` performs the document checks, API-format selection, preview extraction, and document naming. 

And remember: Codex found that the full document bytes are sent to Bedrock; the local PDF extraction is for preview purposes. 

This is why this flow is **direct document prompting rather than RAG**. 

---

# The simplest way to remember the request flow

For now, remember:

```text
USER INPUT
   ↓
STREAMLIT
   ↓
VALIDATE / PROCESS
   ↓
BUILD BEDROCK REQUEST
   ↓
BOTO3
   ↓
AMAZON BEDROCK
   ↓
FOUNDATION MODEL
   ↓
STREAM RESPONSE
   ↓
STREAMLIT
   ↓
USER
```

Don't memorize every internal function yet.

If you understand **why the request moves through these stages**, you're learning the project rather than memorizing an interview script.

---

# Interview Explanation

Later, after you understand the flow, you could explain it like this:

> **“When a user submits a question with an optional image or document, the Streamlit application first processes the input. Uploaded files are routed through the validation layer and then to either the image or document service. Once the input is prepared, the Bedrock service constructs a request containing the user's message, optional attachment, conversation history, system instructions, and inference settings. The service uses boto3 and the Bedrock Runtime ConverseStream API to invoke the selected foundation model, with IAM controlling authorization. Bedrock then streams the generated response back to the application, which displays it progressively in Streamlit. Finally, the application updates its conversation histories so follow-up questions can include previous context.”**

Again, **understand this before memorizing it**.

## Save this lesson as

**`03-Application-Flow.md`**

Your learning folder can now be:

```text
NovaMind-AI-Learning/
│
├── 01-Project-Overview.md
├── 02-Project-Architecture.md
├── 03-Application-Flow.md
│
└── images/
    └── NovaMind-AI-Current-Architecture.png
```

### Question 4

The next logical question is:

> **“Can you explain the complete technology stack used in my current NovaMind AI project? For each technology, explain what it is, exactly where and why it is used in my project, and what would happen if we removed it. Separate the application technologies from AWS services.”**

That would become **`04-Technology-Stack.md`**.
