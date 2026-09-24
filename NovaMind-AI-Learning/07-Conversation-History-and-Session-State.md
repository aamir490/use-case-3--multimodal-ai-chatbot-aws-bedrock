# 07 — Conversation History & Session State

## Question

> **Can you explain how conversation history and session state work in my current NovaMind AI project? Explain `chat_history` vs `bedrock_history`, what Streamlit session state is, how follow-up questions get previous context, whether Amazon Bedrock itself remembers the conversation, what happens when the session is lost/restarted, and use a simple multi-turn conversation example from my project.**

---

# Answer

This is an important concept because it answers a common question:

> **“How does my chatbot remember what I said earlier?”**

The short answer for your current project is:

> **NovaMind AI maintains the conversation inside the Streamlit application. For later questions, the application sends previous conversation history to Amazon Bedrock along with the new question.**

Codex found that your application maintains two different histories:

```text
chat_history
bedrock_history
```

and that the session state is held by the application rather than in a persistent database. 

Let's understand this from zero.

---

# 1. What is a conversation history?

Imagine this conversation:

```text
User:
What is AWS IAM?

AI:
IAM is AWS Identity and Access Management.

User:
Can you explain it with an example?
```

The second question contains:

> **“it”**

What does **“it”** mean?

The AI needs the earlier conversation to understand that **“it” refers to AWS IAM**.

If the model received only:

```text
Can you explain it with an example?
```

there may not be enough context.

Instead, your application can send:

```text
User:
What is AWS IAM?

Assistant:
IAM is AWS Identity and Access Management.

User:
Can you explain it with an example?
```

Now the model has the context.

That previous information is the **conversation history**.

---

# 2. What is Streamlit Session State?

Your application uses Streamlit.

Normally, Streamlit reruns application code as the user interacts with the interface.

But your chatbot needs to preserve information between those interactions.

For example:

```text
Selected model
Conversation history
Uploaded attachment state
Settings
Counters
```

This is where **Streamlit Session State** is useful.

Think of it as temporary application memory associated with the user's current Streamlit session.

```text
             STREAMLIT SESSION STATE
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
 chat_history   bedrock_history    Settings
```

Codex found that your application initializes histories, settings, counters, and pending attachment state in the session. 

---

# 3. Session State is NOT a database

This distinction matters.

Your current architecture is not:

```text
Streamlit
    ↓
DynamoDB / PostgreSQL
    ↓
Persistent conversation history
```

Codex found no persistent conversation database in the current implementation. 

Instead:

```text
Current implementation

Streamlit Application
       ↓
Session State
       ↓
Temporary conversation state
```

So think:

**Session state = current application-session memory.**

**Database = durable/persistent storage.**

Your project currently relies on the first one for conversation history.

---

# 4. Why are there TWO histories?

This is one of the most interesting design choices in your project.

Codex found:

```text
chat_history
```

and:

```text
bedrock_history
```

They don't have exactly the same purpose. 

Think:

```text
                Conversation
                     │
             ┌───────┴────────┐
             ▼                ▼
       chat_history      bedrock_history
             │                │
             ▼                ▼
      Human/UI view      Model/API view
```

Let's understand both.

---

# 5. What is `chat_history`?

`chat_history` is the application's **human-readable/display-oriented conversation history**.

Codex found it is used for things including readable display and export and can contain UI-oriented information such as timestamps, filenames, and thumbnails. 

Conceptually, it might represent:

```text
User
10:30 PM

[aws-error.png]

Why am I getting this error?


Assistant
10:30 PM

The screenshot shows an AWS AccessDenied error...
```

This is useful for the **application/UI side**.

Think:

```text
chat_history
     ↓
"What should the human see?"
```

---

# 6. What is `bedrock_history`?

`bedrock_history` has a different purpose.

It stores the conversation in the structured form needed for subsequent model interactions. 

Conceptually:

```text
[
    USER MESSAGE,
    ASSISTANT MESSAGE,
    USER MESSAGE,
    ASSISTANT MESSAGE
]
```

Rather than focusing on UI information such as:

```text
Timestamp
Thumbnail
Display formatting
```

it focuses on the structured model conversation.

Think:

```text
bedrock_history
      ↓
"What conversation context
does the model need?"
```

---

# 7. Simplest difference

Remember it this way:

```text
chat_history
     ↓
FOR THE APPLICATION / HUMAN

bedrock_history
     ↓
FOR THE MODEL CONVERSATION
```

Or:

| History           | Main purpose                               |
| ----------------- | ------------------------------------------ |
| `chat_history`    | Display/export-friendly conversation       |
| `bedrock_history` | Structured history used for model requests |



That is the main distinction you should understand.

---

# 8. Let's use a real multi-turn example

Suppose you open NovaMind AI.

Initially:

```text
chat_history = []

bedrock_history = []
```

There is no conversation yet.

---

# 9. Turn 1 — First question

You ask:

> **“What is Amazon Bedrock?”**

The application prepares the request.

Because this is the first question:

```text
Previous bedrock_history
        ↓
      EMPTY

        +

Current Question
"What is Amazon Bedrock?"
```

So the model receives the first user message.

Conceptually:

```text
USER
"What is Amazon Bedrock?"

        ↓

Amazon Bedrock

        ↓

Nova Pro

        ↓

"Amazon Bedrock is..."
```

---

# 10. The first response is stored

Suppose the model answers:

> “Amazon Bedrock is an AWS managed service that provides access to foundation models…”

Your application now has conversation information to preserve.

Conceptually:

### `chat_history`

```text
USER:
What is Amazon Bedrock?

ASSISTANT:
Amazon Bedrock is an AWS managed service...
```

### `bedrock_history`

```text
USER MESSAGE:
What is Amazon Bedrock?

ASSISTANT MESSAGE:
Amazon Bedrock is an AWS managed service...
```

Again, the exact internal structures can differ; the important point from Codex's analysis is that one is display-oriented while the other is structured for model conversations. 

---

# 11. Turn 2 — Follow-up question

Now you ask:

> **“Which models can I use in it?”**

Notice something important.

You didn't say:

> “Which models can I use in Amazon Bedrock?”

You said:

> **“Which models can I use in it?”**

For the model to understand **“it”**, it needs previous context.

This is where `bedrock_history` matters.

---

# 12. The application sends previous context

Conceptually, your application now builds:

```text
PREVIOUS HISTORY

User:
"What is Amazon Bedrock?"

Assistant:
"Amazon Bedrock is..."

        +

NEW QUESTION

User:
"Which models can I use in it?"
```

and sends that conversation context with the new request.

Codex found that previous model history plus the new message are supplied to Bedrock during subsequent interactions. 

Now the model can understand:

```text
"it"
 ↓
Amazon Bedrock
```

---

# 13. Turn 3 — Upload an image

Now suppose you upload:

```text
aws-error.png
```

and ask:

> **“Is this related to the IAM issue we discussed?”**

Now the request may conceptually include:

```text
Previous Conversation
        +
aws-error.png
        +
Current Question
```

So:

```text
bedrock_history
        │
        │ Previous conversation
        ▼
┌─────────────────────────────┐
│ What is Bedrock?            │
│ Bedrock is...               │
│ Which models...?            │
│ You can use...              │
└─────────────────────────────┘
              +
      aws-error.png
              +
"Is this related to the IAM
 issue we discussed?"
              ↓
        BEDROCK REQUEST
```

This allows the model to use both **conversation context and current multimodal input**.

---

# 14. Does Amazon Bedrock remember everything automatically?

For your current project, the useful mental model is:

**No — your application maintains the history and sends it with subsequent requests.**

Codex explicitly found:

> there is no persistent Bedrock-side conversation ID in this implementation. 

So don't imagine:

```text
Question 1
   ↓
Bedrock stores forever
   ↓
Question 2
   ↓
Bedrock automatically retrieves Question 1
```

Your current application works conceptually like:

```text
Question 1
   ↓
Application stores history
   ↓
Question 2
   ↓
Application sends:

Question 1
Answer 1
Question 2

   ↓
Bedrock
```

That's a major concept.

---

# 15. A simple analogy

Imagine you're talking to someone who gets a new sheet of paper every time you ask a question.

### First request

You give them:

```text
What is IAM?
```

They answer.

Your application keeps a copy.

### Second request

Instead of giving them only:

```text
Give me an example.
```

your application gives them:

```text
Earlier:

User: What is IAM?
Assistant: IAM is...

Now:

User: Give me an example.
```

Now they understand the context.

That's roughly the mental model for your current conversation-history flow.

---

# 16. Why not just use `chat_history` for everything?

Because the UI and the model have different needs.

Your UI may care about:

```text
Timestamp
Filename
Thumbnail
Display information
Export formatting
```

The model request cares about:

```text
Role
Content
Attachment blocks
Previous user messages
Previous assistant messages
```

So separating them is useful.

```text
                    CONVERSATION
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        chat_history          bedrock_history
              │                     │
      Display concerns         Model concerns
```

Codex actually listed the separate histories as one of the project's strengths because it avoids forcing UI metadata into the model request structure. 

---

# 17. Where are these histories stored?

Currently:

```text
Streamlit Session State
```

Conceptually:

```text
st.session_state
       │
       ├── chat_history
       │
       ├── bedrock_history
       │
       ├── settings
       │
       ├── counters
       │
       └── pending attachment state
```

Codex found that this state is maintained by the application server rather than durable storage. 

---

# 18. What happens when Streamlit reruns?

Streamlit applications commonly rerun Python code when users interact with widgets.

Without session state, imagine:

```text
User asks Question 1
        ↓
Application reruns
        ↓
Everything resets
        ↓
History lost
```

Session state allows important values to survive those normal reruns within the active session.

Conceptually:

```text
Run 1

session_state
├── Question 1
└── Answer 1


User asks Question 2

        ↓

Streamlit reruns

        ↓

session_state still contains:

├── Question 1
├── Answer 1
└── now Question 2
```

That's why session state is so useful for a Streamlit chatbot.

---

# 19. But what if the session itself is lost?

This is different from a normal Streamlit rerun.

Because your current project doesn't persist conversations to a database, losing the session can mean losing that conversation state.

Codex describes the history as **server-memory session state rather than durable storage**. 

So conceptually:

```text
Active Session

chat_history
bedrock_history
      ↓
Available
```

But if the relevant session state disappears:

```text
Session lost/reset
       ↓
In-memory history unavailable
       ↓
New conversation begins without
the previous context
```

---

# 20. What if the application server restarts?

Same fundamental problem.

Imagine:

```text
EC2 / Streamlit

RAM
│
├── User A conversation
└── User B conversation
```

If the application process/server holding that state is restarted, in-memory session data isn't the same as having the conversations safely persisted in a database.

Because your current architecture has no persistent conversation store, Codex specifically identified persistence as something the current system doesn't provide. 

For now, just understand the limitation.

We'll discuss improvements later.

---

# 21. What does “Clear Conversation” do?

Codex found that the clear/new-conversation behavior clears conversation histories and counters. 

Conceptually:

Before:

```text
chat_history

Q1
A1
Q2
A2


bedrock_history

Q1
A1
Q2
A2
```

User chooses clear/new conversation.

After:

```text
chat_history = []

bedrock_history = []
```

The next question effectively starts a new conversation context.

---

# 22. What about Sign Out?

Codex found that signing out clears the session. 

So again, don't think:

> “I'll sign in tomorrow and Bedrock will automatically remember yesterday's conversation.”

That is not what this current architecture provides.

---

# 23. One important limitation: history grows

Here's another consequence of your design.

Imagine:

```text
Question 1 + Answer 1
Question 2 + Answer 2
Question 3 + Answer 3
...
Question 30 + Answer 30
```

Because previous history is included with subsequent requests, the amount of context sent can grow.

Codex identified that the current project does **not** have a proper context-window budgeting or history-trimming strategy. 

Conceptually:

```text
Request 1

Q1
```

then:

```text
Request 2

Q1
A1
Q2
```

then:

```text
Request 3

Q1
A1
Q2
A2
Q3
```

and so on.

That can eventually affect request size and cost.

Don't worry about solving it yet.

Just understand why it happens.

---

# 24. Attachments make this even more important

Codex found that model history can include attachment content, so previous attachments may also be resent with later requests. 

Imagine:

```text
Turn 1

Image
+
Question
```

Then later:

```text
Turn 2

Previous history
including attachment
+
New question
```

This can increase:

```text
Request size
Memory usage
Model input
Cost
```

That's one reason conversation-history management becomes important in production AI applications.

---

# 25. What about the “Summarize Conversation” feature?

Your project has a conversation-summary feature.

But there's an important implementation detail.

Codex found that the summary operation copies the model history, asks the model for a summary, and then assigns the extended copy back.

Therefore, it **doesn't currently function as context compression**. 

That's an important distinction.

A button called:

> “Summarize Conversation”

doesn't automatically mean:

```text
Long History
    ↓
Summary
    ↓
Delete/replace old history
    ↓
Smaller future context
```

According to Codex's analysis, that's not what the current implementation does.

We'll revisit this when studying improvements.

---

# 26. Complete conversation flow

Here's the whole concept:

```text
                     USER
                       │
                       ▼
                  QUESTION 1
                       │
                       ▼
                  STREAMLIT
                       │
                       ▼
              bedrock_history
                       │
                       ▼
              AMAZON BEDROCK
                       │
                       ▼
                   ANSWER 1
                       │
              ┌────────┴────────┐
              ▼                 ▼
        chat_history      bedrock_history
        UI / export       model context


User asks Question 2:

                 QUESTION 2
                       │
                       ▼
               STREAMLIT
                       │
                       ▼
         Previous bedrock_history
                       +
                 Question 2
                       │
                       ▼
              AMAZON BEDROCK
                       │
                       ▼
                   ANSWER 2
                       │
              ┌────────┴────────┐
              ▼                 ▼
        chat_history      bedrock_history
```

That's the heart of your current conversation-memory architecture.

---

# 27. What you should remember

You don't need to memorize all 26 sections.

Remember these **five concepts**.

### 1. Streamlit Session State

Temporary application memory for the active session.

### 2. `chat_history`

```text
Human / UI history
```

Used for readable display/export-oriented information.

### 3. `bedrock_history`

```text
Model conversation history
```

Used when constructing subsequent Bedrock requests.

### 4. Follow-up questions

```text
Previous history
       +
New question
       ↓
Bedrock
```

That's how the model gets previous context.

### 5. Bedrock doesn't provide persistent conversation memory for this implementation

```text
Application manages history
       ↓
Streamlit session state
```

No persistent conversation database currently exists. 

---

# Interview Explanation

Once you understand it, a concise interview answer would be:

> **“In NovaMind AI, conversation state is managed by the Streamlit application rather than being permanently stored by Amazon Bedrock. I maintain two histories: `chat_history`, which is optimized for UI display and exports, and `bedrock_history`, which stores structured user and assistant messages for model interactions. When the user asks a follow-up question, the application sends the previous Bedrock history along with the new message, which gives the foundation model the context needed to understand references to earlier turns. These histories are currently stored in Streamlit session state rather than a persistent database, so they aren't designed to survive loss of the session or application restart.”**

The key sentence to understand is:

> **“The model appears to remember because my application sends previous context again.”**

That idea will help you understand almost every conversational AI application.

## Save this lesson as

**`07-Conversation-History-and-Session-State.md`**

Your notes are now:

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
│
└── images/
    └── NovaMind-AI-Current-Architecture.png
```

## Question 8 — Next

You've now covered the **core current system**. The next step should be to understand what is actually weak or incomplete before designing V2:

> **“Based strictly on Codex’s analysis of my current NovaMind AI project, can you explain the current problems, limitations, and production-readiness gaps one by one in very simple English? For each problem, explain what the current implementation does, why it can become a problem, give a real example of what could go wrong, and classify it as correctness, security, scalability, reliability, cost, testing, deployment, or documentation. Do not improve or redesign the project yet—only help me understand the problems.”**

That can become **`08-Current-Problems-and-Limitations.md`**.
