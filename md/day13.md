Building on Day 12's streaming chatbot, today we're adding **customizable personalities** using system prompts. Users can give the bot different personas—from a pirate to a teacher to a comedian—and watch how the same AI responds completely differently based on its "character."

---

### :material/settings: How It Works: Step-by-Step

Day 13 keeps everything from Day 12 (streaming with custom generator) and adds **system prompt customization**.

#### What's Kept from Day 12:
- :material/check_circle: Streaming responses with `st.write_stream()` (Day 12)
- :material/check_circle: Custom generator for reliable streaming (Day 12)
- :material/check_circle: Spinner showing "Processing" status (Day 12)
- :material/check_circle: Full conversation history passed to LLM (Day 11)
- :material/check_circle: Sidebar with conversation stats (Day 11)
- :material/check_circle: Clear History button (Day 11)
- :material/check_circle: Welcome message (Day 11)

#### What's New: System Prompts & Personalities

#### 1. Initialize System Prompt and Messages Early

```python
# Initialize system prompt if not exists
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful pirate assistant named Captain Starlight. You speak with pirate slang, use nautical metaphors, and end sentences with 'Arrr!' when appropriate. Be helpful but stay in character."

# Initialize messages with a personality-appropriate greeting
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ahoy! Captain Starlight here, ready to help ye navigate the high seas of knowledge! Arrr!"}
    ]
```

* **Early initialization**: Set up both the system prompt and messages before creating the sidebar widgets.
* **Session state**: Ensures the prompt persists across reruns and can be updated by preset buttons.
* **Personality-appropriate greeting**: The welcome message matches the default pirate persona.

#### 2. Preset Personality Buttons (at the top)

```python
with st.sidebar:
    st.header(":material/theater_comedy: Bot Personality")
    
    # Preset personalities
    st.subheader("Quick Presets")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(":material/sailing: Pirate"):
            st.session_state.system_prompt = "You are a helpful pirate assistant..."
            st.rerun()
    
    with col2:
        if st.button(":material/library_books: Teacher"):
            st.session_state.system_prompt = "You are Professor Ada, a patient and encouraging teacher..."
            st.rerun()
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button(":material/mood: Comedian"):
            st.session_state.system_prompt = "You are Chuckles McGee, a witty comedian assistant..."
            st.rerun()
    
    with col4:
        if st.button(":material/smart_toy: Robot"):
            st.session_state.system_prompt = "You are UNIT-7, a helpful robot assistant..."
            st.rerun()
```

* **Preset buttons first**: Placed at the top for better UX - users see presets before the text area.
* **Quick switches**: Each button updates `st.session_state.system_prompt` with a predefined personality.
* **`st.rerun()`**: Refreshes the app so the text area below shows the new value.
* **Four personas**: Pirate (Captain Starlight), Teacher (Professor Ada), Comedian (Chuckles McGee), and Robot (UNIT-7).

#### 3. The System Prompt Text Area (below presets)

```python
st.divider()

st.text_area(
    "System Prompt:",
    height=200,
    key="system_prompt"
)
```

* **`key="system_prompt"`**: Automatically binds to `st.session_state.system_prompt` - no need for `value` parameter.
* **No conflict warning**: Using only `key` (not both `key` and `value`) avoids Session State API conflicts.
* **Editable**: Users can modify preset prompts or write completely custom ones.
* **Below presets**: Better flow - click a preset above, see/edit result below.

#### 4. Injecting the System Prompt with Streaming

```python
# Custom generator for reliable streaming
def stream_generator():
    # Build the full conversation history for context
    conversation = "\n\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in st.session_state.messages
    ])
    
    # Create prompt with system instruction
    full_prompt = f"""{st.session_state.system_prompt}

Here is the conversation so far:
{conversation}

Respond to the user's latest message while staying in character."""
    
    response_text = call_llm(full_prompt)
    for word in response_text.split(" "):
        yield word + " "
        time.sleep(0.02)

with st.spinner("Processing"):
    response = st.write_stream(stream_generator)
```

* **System prompt first**: The personality instruction goes at the top of the prompt, setting the tone for everything that follows.
* **"Stay in character"**: This explicit reminder helps the LLM maintain consistency throughout the conversation.
* **Custom generator**: Simulates streaming by yielding words with delays.
* **`call_llm()`**: Uses the SQL-based `ai_complete()` function for universal compatibility.
* **`split(" ")`**: Splits response by spaces (not `split()` which splits on all whitespace).
* **Spinner wrapper**: Shows "Processing" indicator while generating, providing visual feedback before streaming begins.

#### 5. Why System Prompts Matter

System prompts are powerful because they:
- **Define behavior**: Tell the LLM *how* to respond, not just *what* to respond to
- **Set tone and style**: Formal, casual, humorous, or technical. It's all controllable
- **Enable role-playing**: Create specialized assistants for different use cases
- **Provide constraints**: Limit responses to certain topics or formats

When this code runs, you will have a chatbot with a personality selector in the sidebar. Try switching between personas and notice how the same question gets answered differently based on the system prompt!

---

### :material/library_books: Resources
- [Prompt Engineering Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#best-practices)
- [st.text_area Documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.text_area)
- [System Prompts Best Practices](https://docs.anthropic.com/claude/docs/system-prompts)

