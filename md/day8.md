Welcome to Week 2! Let's reflect on what we've learned so far. 

In Week 1, you built linear apps: Input → Process → Output. Now we'll learn to use chat elements to build a chatbot. This is where Streamlit really shines, but it requires the app to eventually "remember" context.

For today's challenge, our goal is to focus purely on the chat user interface (UI). Here, we'll render a visual chat conversation using chat elements before we worry about memory or API calls. Once that's done, we'll have the visual skeleton of a chatbot. Although it won't be a full functional chatbot but it's a great start towards that path.

---

### :material/settings: How It Works: Step-by-Step

We will use two specific commands: `st.chat_message()` for bubbles and `st.chat_input()` for the text box.

#### 1. Visualizing Static Messages

```python
import streamlit as st

with st.chat_message("user"):
    st.write("Hello! Can you explain what Streamlit is?")

with st.chat_message("assistant"):
    st.write("Streamlit is an open-source Python framework for building data apps.")
    st.bar_chart([10, 20, 30, 40]) 
```

* **`st.chat_message("role")`**: Creates the message container. Streamlit automatically assigns an avatar and alignment based on the role ("user" vs "assistant").
* **`st.bar_chart(...)`**: Demonstrates that chat bubbles can contain rich media (charts, images, dataframes), not just plain text.

#### 2. The Chat Input Widget

```python
prompt = st.chat_input("Type a message here...")
```

* **`st.chat_input(...)`**: Creates the text entry box pinned to the bottom of the screen. It handles the layout automatically so it doesn't overlap with the message history.
* **`prompt`**: Stores the string the user typed. It remains `None` until the user hits "Enter."

#### 3. Reacting to Input (The "Glitchy" Loop)

```python
if prompt:
    # Display the user's new message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Display a mock assistant response
    with st.chat_message("assistant"):
        st.write(f"You just said:\n\n '{prompt}' \n\n(I don't have memory yet!)")
```

* **`if prompt:`**: Ensures this code runs only after the user submits text.
* **`st.write(prompt)`**: Immediately echoes the input back to the screen in a user bubble.

**Observation for Day 8:**
If you type a message, you will see it appear. However, if you type a second message, the first one disappears. This is because Streamlit redraws the screen on every interaction, and we haven't told it to store the history yet.

To fix this "disappearing message" problem, we need to master the most important concept in Streamlit app development: **Session State**, which we'll cover tomorrow.

---

### :material/library_books: Resources
- [st.chat_message Documentation](https://docs.streamlit.io/develop/api-reference/chat/st.chat_message)
- [st.chat_input Documentation](https://docs.streamlit.io/develop/api-reference/chat/st.chat_input)
- [Build a Basic LLM Chat App](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
