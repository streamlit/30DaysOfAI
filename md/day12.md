Building on Day 11's foundation (conversation history and sidebar stats), today we're adding **streaming responses** to create a more dynamic and responsive chat experience. Instead of waiting for the complete response, users will see the AI's reply appear word-by-word in real-time, just like modern chat applications.

---

### :material/settings: How It Works: Step-by-Step

Day 12 focuses on adding one key enhancement: **streaming responses**.

#### What's Kept from Previous Days:
- :material/check_circle: Welcome message on initialization (Day 11)
- :material/check_circle: Full conversation history passed to LLM (Day 11)
- :material/check_circle: Sidebar with conversation stats (Day 11)
- :material/check_circle: Clear History button (Day 11)
- :material/check_circle: Chat interface with `st.chat_message()` (Days 8-11)

#### What's New: Streaming Responses

```python
# Build the full conversation history for context
conversation = "\n\n".join([
    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
    for msg in st.session_state.messages
])
full_prompt = f"{conversation}\n\nAssistant:"

# Generate stream
def stream_generator():
    response_text = call_llm(full_prompt)
    for word in response_text.split(" "):
        yield word + " "
        time.sleep(0.02)

# Display assistant response with streaming
with st.chat_message("assistant"):
    with st.spinner("Processing"):
        response = st.write_stream(stream_generator)

# Add assistant response to state
st.session_state.messages.append({"role": "assistant", "content": response})
st.rerun()  # Force rerun to update sidebar stats
```

**What changed from Day 11:**

* **Moved conversation building**: Now happens outside the generator, in the main flow
* **Custom generator function**: Creates a Python generator that simulates streaming by yielding words from the response.
* **`call_llm(full_prompt)`**: Uses the SQL-based `ai_complete()` function to get the full response from the LLM.
* **Simulated streaming**: Since `ai_complete()` returns the complete response, we split it by spaces using `.split(" ")` and yield words one at a time.
* **`time.sleep(0.02)`**: Small delay (20ms) between words creates smooth, visible streaming effect.
* **`st.spinner("Processing")`**: Wraps the streaming to show a loading indicator while fetching the initial response.
* **`st.write_stream(stream_generator)`**: Streamlit's streaming display function, fed by our custom generator.
* **`response = ...`**: Returns the complete text once streaming finishes, which we store in message history.
* **`st.rerun()`**: Forces app rerun to immediately update sidebar stats after each response.

**Why this approach:**

- **Universal compatibility**: The SQL-based `ai_complete()` works across all deployment environments (SiS, Community Cloud, local)
- **Better UX**: Users see words appear in real-time rather than waiting for the complete response
- **Perceived speed**: Even though generation time is the same, streaming *feels* much faster
- **Natural conversation**: The typing effect mimics human-to-human chat
- **Simple implementation**: Easy to understand and customize the streaming delay

When this code runs, you will have a chatbot with conversation history **plus** real-time streaming responses for a professional, modern chat experience.

---

### :material/library_books: Resources
- [Cortex Complete Streaming](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#streaming-responses)
- [st.write_stream Documentation](https://docs.streamlit.io/develop/api-reference/write-magic/st.write_stream)
- [Build Conversational Apps](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
