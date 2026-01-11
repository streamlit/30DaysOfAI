For today's challenge, our goal is to build a v2 of the **"LinkedIn Post Generator" web app**. Here, we'll integrate a **Streamlit frontend** with **Snowflake's Cortex AI** to generate text based on user-defined parameters. Particularly, the tool drafts social media content using the Claude 3.5 Sonnet model.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Connection and AI Function Wrapper

```python
import streamlit as st
import json
from snowflake.snowpark.functions import ai_complete

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

@st.cache_data
def call_cortex_llm(prompt_text):
    """Makes a call to Cortex AI with the given prompt."""
    model = "claude-3-5-sonnet"
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt_text).alias("response")
    )
    response_raw = df.collect()[0][0]
    return json.loads(response_raw)
```

* **`get_active_session()`**: Retrieves the current connection to the Snowflake database environment so the app can access data and AI services.
* **`try/except` block**: Automatically detects the environment and connects appropriately (works in SiS, locally, and on Community Cloud)
* **`@st.cache_data`**: A Streamlit decorator that caches the result of the function. If the same prompt is sent twice, it reloads the data from the cache instead of calling the AI again, saving time and compute credits.
* **`session.range(1).select(...)`**: This is a Snowpark pattern to execute a scalar function. It creates a single-row DataFrame to run the `ai_complete` function.
* **`ai_complete`**: The core function that sends the prompt to Snowflake Cortex (using the Claude 3.5 model) to generate the text.

#### 2. Building the User Interface

```python
st.title(":material/post: LinkedIn Post Generator v2")

content = st.text_input("Content URL:", "https://docs.snowflake.com/en/user-guide/views-semantic/overview")
tone = st.selectbox("Tone:", ["Professional", "Casual", "Funny"])
word_count = st.slider("Approximate word count:", 50, 300, 100)
```

* **`st.title`**: Sets the main header of the app.
* **`st.text_input`**: Creates a field for the user to paste the source URL they want the post to be about.
* **`st.selectbox`**: Provides a dropdown menu to restrict the user to specific options for the post's tone.
* **`st.slider`**: Allows the user to select a specific numerical range for the output length.

#### 3. Execution and Status Management



```python
if st.button("Generate Post"):
    with st.status("Starting engine...", expanded=True) as status:
        
        st.write(":material/psychology: Thinking: Analyzing constraints and tone...")
        prompt = f"""...""" # (Prompt construction omitted for brevity)
        
        st.write(":material/flash_on: Generating: contacting Snowflake Cortex...")
        response = call_cortex_llm(prompt)
        
        st.write(":material/check_circle: Post generation completed!")
        status.update(label="Post Generated Successfully!", state="complete", expanded=False)

    st.subheader("Generated Post:")
    st.markdown(response)
```

* **`if st.button("Generate Post"):`**: The logic inside this block only runs when the user physically clicks the button.
* **`with st.status(...)`**: Creates a container that provides visual feedback (like a spinner) to the user while the AI is processing, preventing the app from looking "frozen."
* **`prompt = f"""..."""`**: Constructs a dynamic string using Python f-strings to insert the user's specific variables (tone, length, URL) into the instructions for the AI.
* **`status.update(...)`**: Changes the visual state of the status container to "complete" and collapses it once the data is ready.
* **`st.markdown(response)`**: Renders the final text returned by the AI onto the screen, supporting formatting like bolding or lists.

When this code runs, you will see a sidebar-less web interface where inputting parameters and clicking "Generate" produces a formatted LinkedIn post in real-time.

---

### :material/library_books: Resources
- [st.status Documentation](https://docs.streamlit.io/develop/api-reference/status/st.status)
- [Build an LLM App using LangChain](https://docs.streamlit.io/develop/tutorials/llms/llm-quickstart)
