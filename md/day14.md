Building on previous chatbots, today we're adding **visual polish with avatars** and **robust error handling** to create a production-ready chatbot. Users can now personalize the appearance of their chat, and the app will handle API failures gracefully without crashing.

---

### :material/settings: How It Works: Step-by-Step

Day 14 keeps everything from previous days and adds **custom avatars** and **error handling**.

#### What's Kept from Previous Days:
- :material/check_circle: Streaming responses with custom generator (Day 12)
- :material/check_circle: Spinner showing "Processing" status (Day 12)
- :material/check_circle: System prompt customization (Day 13)
- :material/check_circle: Full conversation history (Day 11)
- :material/check_circle: Sidebar with conversation stats (Day 11)
- :material/check_circle: Clear History button (Day 11)
- :material/check_circle: Welcome message (Day 11)
- :material/check_circle: Chat interface with `st.chat_message()` (Days 8-11)

#### What's New: Avatars & Error Handling

#### 1. Avatar Configuration

```python
USER_AVATAR = ":material/account_circle:"
ASSISTANT_AVATAR = ":material/smart_toy:"

user_avatar = st.selectbox(
    "Your Avatar:",
    [":material/account_circle:", "🧑‍💻", "👨‍🎓", "👩‍🔬", "🦸", "🧙"],
    index=0
)
```

* **Default avatars**: We define emoji constants for consistent styling.
* **User choice**: The selectbox lets users personalize their chat experience by picking their preferred emoji.
* **Both avatars**: User and assistant avatars are independently customizable.

#### 2. Debug Mode Toggle

```python
st.subheader(":material/bug_report: Debug Mode")
simulate_error = st.checkbox(
    "Simulate API Error",
    value=False,
    help="Enable this to test the error handling mechanism"
)
```

* **Testing tool**: A checkbox that allows you to trigger an error on demand.
* **Educational value**: Demonstrates how error handling works without waiting for a real failure.
* **Default off**: Normal operation by default (`value=False`).
* **Help text**: Provides context for what the toggle does.

#### 3. Using Avatars in Chat Messages

```python
for message in st.session_state.messages:
    avatar = user_avatar if message["role"] == "user" else assistant_avatar
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
```

* **Dynamic avatar selection**: Based on the message role, we pick the appropriate avatar.
* **`avatar=` parameter**: Streamlit's `st.chat_message` accepts emojis, image URLs, or image file paths for custom avatars.

#### 4. Error Handling with Try/Except and Streaming

```python
try:
    # Simulate error if debug mode is enabled
    if simulate_error:
        raise Exception("Simulated API error: Service temporarily unavailable (429)")
    
    # Custom generator for reliable streaming
    def stream_generator():
        # Build the full conversation history for context
        conversation = "\n\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in st.session_state.messages
        ])
        full_prompt = f"{conversation}\n\nAssistant:"
        
        response_text = call_llm(full_prompt)
        for word in response_text.split():
            yield word + " "
            time.sleep(0.02)
    
    with st.spinner("Processing"):
        response = st.write_stream(stream_generator)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    
except Exception as e:
    error_message = f"I encountered an error: {str(e)}"
    st.error(error_message)
    st.info(":material/lightbulb: **Tip:** This might be a temporary issue. Try again in a moment, or rephrase your question.")
```

* **`try/except` block**: Wraps the entire streaming process to catch any errors (network issues, rate limits, invalid responses).
* **Simulated error**: When debug mode is enabled, raises a test exception to demonstrate error handling.
* **`st.error(...)`**: Displays a red error box with the exception message.
* **`st.info(...)`**: Provides helpful guidance to users, maintaining a good experience even during failures.
* **Custom generator**: Simulates streaming by yielding words with delays.
* **`call_llm()`**: Uses the SQL-based `ai_complete()` function for universal compatibility.
* **Spinner wrapper**: Shows "Processing" indicator while generating.

#### 5. Why Error Handling Matters

> :material/warning: **This is crucial!** In production, LLM APIs WILL fail eventually. Apps without error handling will crash and frustrate users. This pattern is essential for any real-world deployment.

LLM APIs can fail for many reasons:
- **Rate limiting**: Too many requests in a short time
- **Network issues**: Temporary connectivity problems
- **Model overload**: High demand causing timeouts
- **Invalid input**: Prompts that trigger safety filters

By handling errors gracefully, we:
- Prevent the app from crashing
- Keep users informed about what happened
- Provide actionable suggestions
- Avoid storing failed responses in chat history

When this code runs, you will have a visually polished chatbot with customizable avatars and robust error handling that maintains a professional user experience. Use the debug toggle to test the error handling mechanism and see how the app gracefully handles failures.

---

### :material/lightbulb: Try It Out

Enable the "Simulate API Error" checkbox in the sidebar and send a message. You'll see:
1. :material/cancel: A red error message showing the simulated error
2. :material/lightbulb: A helpful tip suggesting what to do
3. :material/check_circle: The app continues to work - it didn't crash!

Then disable the checkbox and try again to see normal operation.

---

### :material/library_books: Resources
- [st.chat_message Avatar Parameter](https://docs.streamlit.io/develop/api-reference/chat/st.chat_message)
- [st.error Documentation](https://docs.streamlit.io/develop/api-reference/status/st.error)
- [Python Exception Handling](https://docs.python.org/3/tutorial/errors.html)
