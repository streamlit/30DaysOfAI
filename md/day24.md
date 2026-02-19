For today's challenge, our goal is to build a complete image analysis application using Snowflake's `AI_COMPLETE` function with vision-capable models. Users can upload images within a bordered container and get AI-powered analysis displayed in a separate results container, including descriptions, OCR, object identification, chart analysis, or custom queries.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Session State Initialization

```python
# Initialize state
if "image_database" not in st.session_state:
    st.session_state.image_database = "RAG_DB"
    st.session_state.image_schema = "RAG_SCHEMA"

# Configure stage path
database = st.session_state.image_database
schema = st.session_state.image_schema
full_stage_name = f"{database}.{schema}.IMAGE_ANALYSIS"
stage_name = f"@{full_stage_name}"
```

* **Configurable location**: Database and schema can be changed in sidebar settings
* **Stage naming**: Follows pattern `DATABASE.SCHEMA.IMAGE_ANALYSIS`
* **Stage reference**: Uses `@` prefix for Snowflake stage path
* **Persistent state**: Configuration survives across reruns

#### 2. Sidebar Configuration

```python
with st.sidebar:
    st.header(":material/settings: Settings")
    
    # Database configuration
    with st.expander("Database Configuration", expanded=False):
        database = st.text_input("Database", value=st.session_state.image_database)
        schema = st.text_input("Schema", value=st.session_state.image_schema)
    
    # Model selection
    model = st.selectbox(
        "Select a Model",
        ["claude-3-5-sonnet", "openai-gpt-4.1", "openai-o4-mini", "pixtral-large"],
        help="Select a vision-capable model"
    )
```

* **Material icons**: Modern UI with `:material/settings:`
* **Collapsible settings**: Database config in expander
* **Model dropdown**: Vision-capable models including Claude, OpenAI, and Pixtral
* **Dynamic updates**: Changes trigger `st.rerun()` to update stage paths

#### 3. Stage Configuration with Server-Side Encryption

```python
# Create stage with server-side encryption (required for AI_COMPLETE)
session.sql(f"""
CREATE STAGE {full_stage_name}
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
""").collect()
```

* **Server-side encryption**: `SNOWFLAKE_SSE` is **required** for `AI_COMPLETE` with images
* **Client-side encryption**: Not supported for vision models
* **Directory table**: Enabled for file tracking
* **Auto-recreation**: Stage is dropped and recreated if it exists to ensure correct encryption
* **Status display**: Shows success/error with material icons in sidebar

#### 4. Upload Container with Bordered UI

```python
with st.container(border=True):
    st.subheader(":material/upload: Upload an Image")
    uploaded_file = st.file_uploader(
        "Choose an image", 
        type=["jpg", "jpeg", "png", "gif", "webp"],
        help="Supported formats: JPG, JPEG, PNG, GIF, WebP (max 10 MB)"
    )
```

* **Bordered container**: Clean visual separation for upload section
* **Material icon header**: `:material/upload:` for modern look
* **File type restriction**: Only image formats supported by vision models
* **Help text**: Inline guidance for users

#### 5. Image Preview and File Information

```python
if uploaded_file:
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(uploaded_file, caption="Your Image", use_container_width=True)
    
    with col2:
        st.write(f"**File:** {uploaded_file.name}")
        
        # Format file size intelligently
        size_bytes = uploaded_file.size
        if size_bytes >= 1_048_576:  # 1 MB
            size_display = f"{size_bytes / 1_048_576:.2f} MB"
        elif size_bytes >= 1_024:  # 1 KB
            size_display = f"{size_bytes / 1_024:.2f} KB"
        else:
            size_display = f"{size_bytes} bytes"
        
        st.write(f"**Size:** {size_display}")
```

* **Two-column layout**: Image preview on left, metadata on right
* **Responsive image**: `use_container_width=True` for proper scaling
* **Smart file size display**: Automatically formats as bytes, KB, or MB
* **User feedback**: Clear display of what was uploaded

#### 6. Analysis Type Selection

```python
# Analysis type selection (full width, above button)
analysis_type = st.selectbox("Analysis type:", [
    "General description",
    "Extract text (OCR)",
    "Identify objects",
    "Analyze chart/graph",
    "Custom prompt"
])

# Custom prompt input if selected
custom_prompt = None
if analysis_type == "Custom prompt":
    custom_prompt = st.text_area(
        "Enter your prompt:",
        placeholder="What would you like to know about this image?",
        help="Ask anything about the image content"
    )
```

* **Full-width placement**: Outside columns, above the analyze button
* **Predefined prompts**: Common use cases with optimized prompts
* **Custom option**: Users can ask anything about the image
* **Conditional input**: Text area appears only for custom prompts

#### 7. Upload Image to Snowflake Stage

```python
# Create unique filename
timestamp = int(time.time())
file_extension = uploaded_file.name.split('.')[-1]
filename = f"image_{timestamp}.{file_extension}"

# Upload to stage
image_bytes = uploaded_file.getvalue()
image_stream = io.BytesIO(image_bytes)

session.file.put_stream(
    image_stream,
    f"{stage_name}/{filename}",
    overwrite=True,
    auto_compress=False
)
```

* **Unique naming**: Timestamp-based filenames prevent collisions
* **Preserve extension**: Keeps original format (`.jpg`, `.png`, etc.)
* **`BytesIO` wrapper**: Wraps bytes in file-like object for `put_stream`
* **No compression**: `auto_compress=False` keeps images as-is
* **Spinner feedback**: `:material/upload:` spinner shows upload progress

#### 8. Image Analysis with AI_COMPLETE

```python
# Use AI_COMPLETE with TO_FILE syntax
sql_query = f"""
SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
    '{model}',
    '{prompt.replace("'", "''")}',
    TO_FILE('{stage_name}', '{filename}')
) as analysis
"""

result = session.sql(sql_query).collect()
response = result[0]['ANALYSIS']

# Store results in session state
st.session_state.analysis_response = response
st.session_state.analysis_model = model
st.session_state.analysis_prompt = prompt
st.session_state.analysis_stage = stage_name
```

* **`AI_COMPLETE` syntax**: `AI_COMPLETE(model, prompt, file_reference)`
* **`TO_FILE()`**: References staged file for the vision model
* **Three arguments**: Model name, text prompt, image file reference
* **SQL escaping**: Single quotes in prompt are doubled (`''`)
* **Session state storage**: Persists results for display in separate container
* **Spinner feedback**: `:material/psychology:` spinner shows AI is analyzing

This follows the [official Snowflake syntax](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-file):

```sql
AI_COMPLETE(
    <model>, <predicate>, <file> [, <model_parameters> ]
)
```

#### 9. Results Display in Separate Container

```python
# Display results in a separate bordered container
if "analysis_response" in st.session_state:
    with st.container(border=True):
        st.subheader(":material/auto_awesome: Analysis Result")
        st.markdown(st.session_state.analysis_response)
        
        with st.expander(":material/info: Technical Details"):
            st.write(f"**Model:** {st.session_state.analysis_model}")
            st.write(f"**Prompt:** {st.session_state.analysis_prompt}")
            st.write(f"**Stage:** {st.session_state.analysis_stage}")
```

* **Separate container**: Results appear in new bordered container below upload section
* **Session state driven**: Container only appears after analysis completes
* **Material icons**: `:material/auto_awesome:` for results, `:material/info:` for details
* **Markdown rendering**: Supports formatted model responses
* **Expandable details**: Technical info hidden by default
* **Persistent display**: Results remain visible across reruns

#### 10. Helper Information Section

```python
# Info section when no file is uploaded
if not uploaded_file:
    st.info(":material/arrow_upward: Upload an image to analyze!")
    
    st.subheader(":material/lightbulb: What Vision AI Can Do")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- Describe photos\n- Read text (OCR)\n- Identify objects")
    with col2:
        st.markdown("- Analyze charts\n- Understand layouts\n- Describe art style")
```

* **Conditional display**: Only shows when no file is uploaded
* **Material icons**: `:material/arrow_upward:` and `:material/lightbulb:`
* **Use case examples**: Helps users understand capabilities
* **Two-column layout**: Organized presentation of features

---

### :material/adjust: Key Features

| Feature | Implementation |
|---------|----------------|
| **Bordered Containers** | Upload and results in separate bordered sections |
| **Material Icons** | Modern UI throughout (no emojis) |
| **Smart File Size** | Auto-formats as bytes, KB, or MB |
| **Session State** | Results persist in separate container |
| **Image Upload** | `st.file_uploader` with type restrictions |
| **Stage Upload** | `session.file.put_stream()` with unique naming |
| **Vision Analysis** | `AI_COMPLETE` with `TO_FILE()` syntax |
| **Multiple Models** | Claude, OpenAI GPT-4, OpenAI O4, Pixtral |
| **Analysis Types** | Description, OCR, objects, charts, custom |
| **Server-Side Encryption** | Required for AI_COMPLETE with images |
| **File Management** | Staged files persist (manual cleanup via SQL) |

---

### :material/library_books: Key Technical Concepts

**Supported Vision Models:**
- `claude-3-5-sonnet` - Claude's latest vision model
- `openai-gpt-4.1` - OpenAI's GPT-4 with vision
- `openai-o4-mini` - OpenAI's efficient vision model
- `pixtral-large` - Mistral's vision model

According to the [Snowflake AI_COMPLETE documentation](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-file), additional supported models include:
- `claude-4-opus`, `claude-4-sonnet`, `claude-3-7-sonnet`
- `llama4-maverick`, `llama4-scout`

**Supported Image Formats:**
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- `.bmp` (Pixtral and Llama4 models only)

**Image Size Limits:**
- Most models: 10 MB maximum
- Claude models: 3.75 MB maximum, 8000x8000 max resolution

**Stage Requirements:**
- :material/check_circle: Server-side encryption (`SNOWFLAKE_SSE`)
- :material/check_circle: Directory table enabled
- :material/cancel: Client-side encryption not supported

**Analysis Types:**

| Type | Use Case | Example Prompt |
|------|----------|----------------|
| **General Description** | Quick overview | "Describe this image in detail" |
| **OCR** | Extract text | "Extract all text visible in this image" |
| **Object Identification** | List items | "List all objects you can identify" |
| **Chart Analysis** | Data insights | "Analyze this chart, describe trends" |
| **Custom** | Any question | User-defined prompt |

**UI Architecture:**

1. **Container 1 (Upload)**: File uploader, image preview, analysis type, analyze button
2. **Container 2 (Results)**: Analysis result and technical details (appears after processing)
3. **Helper Section**: Tips and capabilities (when no file uploaded)

**Processing Flow:**
1. User uploads image in bordered container
2. Image bytes → `BytesIO` stream
3. Upload to Snowflake stage with unique name
4. Call `AI_COMPLETE` with `TO_FILE()` reference
5. Store results in session state
6. Display results in separate bordered container
7. Staged files persist (can be cleaned manually via SQL if needed)

---

### :material/library_books: Resources

- [Snowflake AI_COMPLETE (Single File) Documentation](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-file)
- [Snowflake Cortex AI Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [st.file_uploader Documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
- [st.container Documentation](https://docs.streamlit.io/develop/api-reference/layout/st.container)
- [st.image Documentation](https://docs.streamlit.io/develop/api-reference/media/st.image)
- [Streamlit Material Icons](https://streamlit.io/components)
