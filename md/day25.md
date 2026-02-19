For today's challenge, our goal is to build a complete voice-enabled conversational AI assistant. Users can record voice messages, which are transcribed using Snowflake's `AI_TRANSCRIBE`, and the assistant responds with context-aware answers using conversation history. The entire interaction happens through a clean interface with persistent chat history.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Session State Initialization

```python
# Initialize conversation with welcome message
if "voice_messages" not in st.session_state:
    st.session_state.voice_messages = []

if len(st.session_state.voice_messages) == 0:
    st.session_state.voice_messages = [
        {
            "role": "assistant",
            "content": "Hello! :material/waving_hand: I'm your voice-enabled AI assistant..."
        }
    ]

# Track processed audio to prevent reprocessing
if "processed_audio_id" not in st.session_state:
    st.session_state.processed_audio_id = None
```

* **`voice_messages`**: Stores the entire conversation history
* **Welcome message**: Always starts with a friendly greeting
* **`processed_audio_id`**: Prevents duplicate processing after `st.rerun()`
* **Persistence**: All state persists across Streamlit reruns

#### 2. Sidebar Layout

```python
with st.sidebar:
    st.title(":material/record_voice_over: Voice-Enabled Assistant")
    st.subheader(":material/mic: Record Your Message")
    audio = st.audio_input("Click to record")
    
    st.header(":material/settings: Settings")
    # Database configuration, stage status, clear chat
```

* **Compact design**: All controls in sidebar
* **Material icons**: Modern UI with Streamlit material icons
* **Recording first**: Audio input prominently placed at top
* **Settings below**: Database config and stage management

#### 3. Stage Configuration for AI_TRANSCRIBE

```python
# Create stage with server-side encryption (required for AI_TRANSCRIBE)
session.sql(f"""
CREATE STAGE {full_stage_name}
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
""").collect()
```

* **Server-side encryption**: `SNOWFLAKE_SSE` is **required** (client-side not supported)
* **Directory table**: `ENABLE = true` for file tracking
* **Auto-recreation**: Stage is dropped and recreated if encryption is wrong
* **Manual button**: Users can force stage recreation in settings

#### 4. Conversation Display (Before Processing)

```python
# Display chat history FIRST (before processing)
st.subheader(":material/voice_chat: Conversation")
for msg in st.session_state.voice_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Create a container for processing status (appears below)
status_container = st.container()
```

* **Persistent display**: Conversation rendered before audio processing
* **Prevents disappearing**: Spinners appear in separate `status_container` below
* **Chat messages**: Uses Streamlit's native `st.chat_message` widget
* **Always visible**: Conversation header and messages remain during processing

#### 5. Audio Processing with Deduplication

```python
if audio is not None:
    audio_bytes = audio.read()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    
    if audio_hash != st.session_state.processed_audio_id:
        st.session_state.processed_audio_id = audio_hash
        # Process audio...
```

* **Content-based hash**: Uses MD5 hash of audio bytes for unique identification
* **Prevents loops**: Same audio won't be processed multiple times
* **Rerun-safe**: Works correctly across Streamlit reruns
* **Reset**: Hash is cleared when no audio is present

#### 6. Transcription with AI_TRANSCRIBE

```python
with status_container:
    with st.spinner(":material/mic: Transcribing audio..."):
        # Upload to stage
        audio_stream = io.BytesIO(audio_bytes)
        session.file.put_stream(
            audio_stream,
            f"{stage_name}/{filename}",
            overwrite=True,
            auto_compress=False
        )
        
        # Transcribe
        sql_query = f"""
        SELECT SNOWFLAKE.CORTEX.AI_TRANSCRIBE(
            TO_FILE('{stage_name}', '{filename}')
        ) as transcript
        """
        result = session.sql(sql_query).collect()
        transcript = json.loads(result[0]['TRANSCRIPT']).get('text', '')
```

* **`put_stream`**: Uploads audio bytes to Snowflake stage
* **`TO_FILE()`**: References staged file for AI_TRANSCRIBE
* **JSON response**: Returns `{text, audio_duration}`
* **Cleanup**: Staged file is removed after transcription
* **Status container**: Spinner appears below conversation, not replacing it

#### 7. Chat History Memory

```python
# Build conversation history for context
conversation_context = "You are a friendly voice assistant...\n\nConversation history:\n"

# Add previous messages (excluding welcome)
history_messages = [msg for msg in st.session_state.voice_messages 
                   if not (msg["role"] == "assistant" and "Click the microphone button" in msg["content"])]

for msg in history_messages:
    role = "User" if msg["role"] == "user" else "Assistant"
    conversation_context += f"{role}: {msg['content']}\n"

# Add current user message
conversation_context += f"\nUser: {transcript}\n\nAssistant:"
```

* **Full context**: LLM receives entire conversation history
* **Excludes welcome**: Filters out the initial greeting message
* **Formatted prompt**: Clear structure with User/Assistant labels
* **Context-aware**: Assistant can reference previous exchanges

#### 8. Response Generation

```python
with st.spinner(":material/smart_toy: Generating response..."):
    response = call_llm(conversation_context)
    
    st.session_state.voice_messages.append({
        "role": "assistant",
        "content": response
    })

st.rerun()
```

* **Separate spinner**: Shows after transcription completes
* **Snowflake Cortex**: Uses SQL-based `ai_complete()` function with Claude 3.5 Sonnet
* **Universal compatibility**: Works across all deployment environments (SiS, Community Cloud, local)
* **Appends response**: Adds to conversation history
* **Reruns**: Updates UI to show new messages

#### 9. Clear Chat Feature

```python
if st.button(":material/delete: Clear Chat"):
    st.session_state.voice_messages = [
        {
            "role": "assistant",
            "content": "Hello! :material/waving_hand: I'm your voice-enabled AI assistant..."
        }
    ]
    st.rerun()
```

* **Resets to welcome**: Clears history but restores greeting
* **Fresh start**: Users can begin a new conversation
* **Sidebar button**: Easily accessible in settings section

---

### :material/adjust: Key Features

| Feature | Implementation |
|---------|----------------|
| **Voice Input** | `st.audio_input` widget in sidebar |
| **Transcription** | `AI_TRANSCRIBE` with `TO_FILE()` syntax |
| **Chat Memory** | Full conversation history passed to LLM |
| **Persistent UI** | Conversation displays before processing |
| **Deduplication** | MD5 hash prevents reprocessing |
| **Stage Config** | Server-side encryption, directory enabled |
| **Error Handling** | Troubleshooting guide for common issues |
| **Material Icons** | Modern UI with Streamlit material design |

---

### :material/library_books: Key Technical Concepts

**Session State Variables:**
- `voice_messages`: List of conversation messages (role, content)
- `processed_audio_id`: MD5 hash of last processed audio
- `voice_database` / `voice_schema`: Configurable database location

**Audio Processing:**
- Audio bytes → MD5 hash → Check if new → Upload to stage → Transcribe → Respond

**Stage Requirements for AI_TRANSCRIBE:**
- :material/check_circle: Server-side encryption (`SNOWFLAKE_SSE`)
- :material/check_circle: Directory table enabled
- :material/cancel: Client-side encryption not supported

**UI Pattern:**
1. Display conversation first
2. Create status container
3. Process audio in status container
4. Spinners appear below conversation
5. Rerun to show new messages

---

### :material/library_books: Resources

- [st.audio_input Documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input)
- [st.chat_message Documentation](https://docs.streamlit.io/develop/api-reference/chat/st.chat_message)
- [Snowflake AI_TRANSCRIBE Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-audio)
- [Snowflake Cortex Complete](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Streamlit Material Icons](https://streamlit.io/components)
