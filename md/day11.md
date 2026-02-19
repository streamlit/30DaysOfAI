For today's challenge, our goal is to enhance our chatbot with better history management. We need to add a welcome message, display conversation statistics in the sidebar, and provide a way to clear the chat history. Once that's done, we will have a more polished chatbot experience with visible conversation tracking.

**Note:** We also add `st.rerun()` after the assistant's response to ensure the sidebar stats update immediately.

---

### :material/bug_report: The Problem from Day 10

In Day 10, we stored messages in session state, so they appeared in the UI. But the LLM didn't actually see that history:

**Example Conversation (Day 10 behavior):**
```
User: "What's the capital of France?"
AI: "Paris"

User: "What's the population?"
AI: "What location are you asking about?" ❌
```

You can **see** your previous question on screen, but the AI can't! This creates a confusing experience where the chat interface looks like it remembers, but the AI has no memory.

**Why?** Because we were only sending the current prompt to the LLM:
```python
response = call_llm(prompt)  # Only sends current message!
```

### :material/check_circle: The Solution (Day 11)

Today, we fix this by passing the **full conversation history** to the LLM:

**Same Conversation (Day 11 behavior):**
```
User: "What's the capital of France?"
AI: "Paris"

User: "What's the population?"
AI: "Paris has approximately 2.1 million people in the city proper..." ✅
```

Now the AI can answer follow-up questions, reference earlier topics, and maintain context throughout the conversation!

**How?** By building and sending the complete conversation:
```python
# Build the full conversation history for context
conversation = "\n\n".join([
    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
    for msg in st.session_state.messages
])
full_prompt = f"{conversation}\n\nAssistant:"

response = call_llm(full_prompt)  # Sends entire conversation!
```

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Initialize with a Welcome Message

```python
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your AI assistant. How can I help you today?"}
    ]
```

* **Pre-populated list**: Instead of an empty list, we start with a welcome message from the assistant. This makes the chatbot feel more inviting when users first load the app.

#### 2. Sidebar Statistics and Controls

```python
with st.sidebar:
    st.header("Conversation Stats")
    user_msgs = len([m for m in st.session_state.messages if m["role"] == "user"])
    assistant_msgs = len([m for m in st.session_state.messages if m["role"] == "assistant"])
    st.metric("Your Messages", user_msgs)
    st.metric("AI Responses", assistant_msgs)
```

* **List comprehension**: The syntax `[m for m in messages if m["role"] == "user"]` creates a new list containing only messages where the role is "user". It's a compact way to filter a list. If you're new to this, it's equivalent to a for-loop with an if-statement inside.
* **`st.metric(...)`**: Displays the counts in a visually appealing metric card format.

#### 3. Clear History Button

```python
    if st.button("Clear History"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your AI assistant. How can I help you today?"}
        ]
        st.rerun()
```

* **Reset to initial state**: When clicked, we replace the messages list with just the welcome message.
* **`st.rerun()`**: Forces the app to rerun immediately, refreshing the display to show the cleared state.

#### 4. Enhanced Message Display

```python
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
```

* **`st.markdown(...)`**: We use markdown instead of `st.write()` to support rich formatting like **bold**, *italics*, and bullet points in responses.

#### 5. Adding a Loading Indicator with `st.spinner`

We introduce `st.spinner` to show users that the AI is working on their request:

```python
with st.spinner("Thinking..."):
    # Build conversation history and get response
    response = Complete(...)
```

* **`st.spinner(...)`**: Displays an animated spinner with custom text while the code inside its context runs. This provides visual feedback during LLM processing, which can take a few seconds.
* **Better UX**: Without this, users might think the app is frozen when waiting for a response. The spinner clearly indicates the AI is "thinking."
* **Note**: In Day 12, when we add streaming, we'll remove the spinner since streaming provides its own visual feedback!

#### 6. Passing Conversation History to the LLM

This is the **critical step** that gives your chatbot actual memory:

```python
# Build the full conversation history for context
conversation = "\n\n".join([
    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
    for msg in st.session_state.messages
])
full_prompt = f"{conversation}\n\nAssistant:"

response = call_llm(full_prompt)
```

* **Why this matters**: Without this, the LLM only sees the current message and can't remember what was said before. The chatbot would appear to have no memory, even though you're storing the history in the UI.
* **Building context**: We reconstruct the entire conversation as a formatted string with clear "User:" and "Assistant:" labels.
* **Full prompt**: The complete conversation history plus the new user message is sent to the LLM, enabling it to maintain context and answer follow-up questions.
* **`call_llm()`**: Uses the SQL-based `ai_complete()` function that works across all deployment environments.

#### 7. Updating Sidebar Stats with st.rerun()

After adding the assistant's response to session state, we force an immediate rerun:

```python
# Add assistant response to state
st.session_state.messages.append({"role": "assistant", "content": response})
st.rerun()  # Force rerun to update sidebar stats
```

* **`st.rerun()`**: Forces the app to rerun immediately, ensuring the sidebar statistics update right away
* **Without this**: The sidebar metrics would lag by one message, only updating on the next user interaction
* **Better UX**: Users see the conversation count update instantly after each AI response

When this code runs, you will see a chatbot with a welcoming initial message, a sidebar showing conversation statistics (that update immediately), a button to reset the conversation, and **true conversation memory** that allows follow-up questions.

---

### :material/library_books: Resources
- [st.metric Documentation](https://docs.streamlit.io/develop/api-reference/data/st.metric)
- [st.rerun Documentation](https://docs.streamlit.io/develop/api-reference/execution-flow/st.rerun)
- [Session State Management](https://docs.streamlit.io/develop/concepts/architecture/session-state)

