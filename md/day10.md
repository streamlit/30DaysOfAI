For today's challenge, our goal is to combine everything we've learned about chat elements and session state to create a chatbot that remembers the conversation. We need to store messages in `st.session_state` and display them using `st.chat_message`. Once that's done, we will have a working chatbot that maintains conversation history across interactions.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Initialize Message Storage

```python
st.title(":material/chat: My First Chatbot")

# Initialize the messages list in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
```

* **`st.session_state.messages = []`**: We create an empty list to store our conversation. This list will hold dictionaries with `"role"` (user/assistant) and `"content"` (the message text). This format is the **industry standard** used by OpenAI, Anthropic, and most chat APIs, so learning it here applies everywhere!
* **`if "messages" not in ...`**: This check ensures we only initialize once, specifically when the app first loads. Without it, the list would reset to empty on every interaction, wiping out the conversation history.

#### 2. Display Chat History

```python
# Display all messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
```

* **`for message in st.session_state.messages`**: We loop through every message stored in our session state.
* **`st.chat_message(message["role"])`**: Creates the appropriate chat bubble (user or assistant) based on the role stored in the message dictionary.

#### 3. Handle New Messages

```python
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
```

* **`:=` (Walrus operator)**: This assigns the input value to `prompt` and checks if it's not empty in one line.
* **`.append(...)`**: Adds the new user message to our persistent message list before displaying it.

#### 4. Generate and Store Response

```python
    with st.chat_message("assistant"):
        response = call_llm(prompt)
        st.write(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
```

* **`call_llm(...)`**: Calls Snowflake Cortex using the `ai_complete()` function to generate a response.
* **Second `.append(...)`**: Stores the assistant's response in the same format, completing the conversation turn.

> :material/lightbulb: **Why SQL-based `ai_complete()`?** We use the SQL-based `ai_complete()` function instead of the Python `Complete()` API because it works universally across all deployment environments (Streamlit in Snowflake, Community Cloud, and local). The Python SDK can have SSL certificate issues in external environments, while the SQL approach is reliable everywhere.

When this code runs, you will have a chatbot where messages persist across interactions, building a visible conversation history.

---

### :material/search: What's Missing? Room for Improvement

While this chatbot works, it has some notable limitations:

**Current Limitations:**
- :material/cancel: **No visual feedback**: Users see nothing while waiting for the response (can feel like the app froze)
- :material/cancel: **Responses appear all at once**: The entire response shows up suddenly, not gradually like modern chat apps
- :material/cancel: **No conversation insights**: Can't see how many messages have been exchanged
- :material/cancel: **No way to start fresh**: Conversation history accumulates with no clear button
- :material/cancel: **Generic appearance**: All messages look the same (no personality or customization)
- :material/cancel: **No error handling**: If the API fails, the app crashes

Don't worry! We'll address all of these issues in the upcoming lessons, transforming this basic chatbot into a production-ready application! :material/rocket_launch:

---

### :material/library_books: Resources
- [Build Conversational Apps](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
- [Cortex Complete Function](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
