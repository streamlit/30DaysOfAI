**Day 15** wraps up Week 2 (Chatbots) by introducing a practical tool for comparing different LLM models. After spending Week 2 building progressively sophisticated chatbots, you now need to answer a key question: **Which model should I use?**

For today's challenge, our goal is to **build a side-by-side model comparison tool**. We need to **run the same prompt through two different models sequentially** and compare their metrics. Once that's done, we will **display both responses side-by-side** with performance metrics such as total latency and output token count.

**Why this matters now:**
- You've just finished building complete chatbots (Days 8-14)
- Week 3 starts RAG applications tomorrow - you'll need to choose a model
- Different models have different trade-offs: speed vs quality, cost vs capability
- This tool helps you make informed decisions for your use case

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Model Execution and Metrics Collection

```python
import streamlit as st
import time
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

def run_model(model: str, prompt: str) -> dict:
    """Execute model and collect metrics."""
    start = time.time()

    # Call Cortex Complete function
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt).alias("response")
    )

    # Get response from dataframe
    rows = df.collect()
    response_raw = rows[0][0]
    response_json = json.loads(response_raw)

    # Extract text from response
    text = response_json.get("choices", [{}])[0].get("messages", "") if isinstance(response_json, dict) else str(response_json)

    latency = time.time() - start
    tokens = int(len(text.split()) * 4/3)  # Estimate tokens (1 token ≈ 0.75 words)

    return {
        "latency": latency,
        "tokens": tokens,
        "response_text": text
    }
```

* **`from snowflake.snowpark.functions import ai_complete`**: **Imports the `ai_complete` function** to interact with **Snowflake Cortex AI models**.
* **`session = get_active_session()`**: **Retrieves the active Snowpark session** necessary to execute Cortex AI calls.
* **`start = time.time()`**: **Records the exact moment** we start the API call. This is our baseline for timing measurements.
* **`df = session.range(1).select(...)`**: This is the **Snowpark pattern for calling Cortex functions**. We create a DataFrame with one row and call `ai_complete`.
* **`rows = df.collect()`**: **Executes the query and collects results** into a list. Breaking this into steps makes the code more readable than chaining `.collect()[0][0]`.
* **`response_raw = rows[0][0]`**: **Extracts the first cell** from the first row, which contains the JSON response string.
* **`json.loads(response_raw)`**: The **response comes back as a JSON string**, so we parse it to access the nested structure.
* **`text = response_json.get(...) if isinstance(response_json, dict) else str(response_json)`**: **Extracts the text from the response** using an inline conditional that handles both dict and non-dict responses.
* **`latency = time.time() - start`**: **Measures total response time** from when we started the API call until we received the complete response.
* **`tokens = int(len(text.split()) * 4/3)`**: **Estimates token count** using the rule of thumb that 1 token ≈ 0.75 words (or 1 word ≈ 1.33 tokens). We multiply word count by 4/3 for a better approximation.

#### 2. Building the Side-by-Side UI

```python
# Model selection
llm_models = [
    "llama3-8b",
    "llama3-70b",
    "mistral-7b",
    "mixtral-8x7b",
    "claude-3-5-sonnet",
    "claude-haiku-4-5",
    "openai-gpt-5",
    "openai-gpt-5-mini"
]
st.title(":material/compare: Select Models")
col_a, col_b = st.columns(2)

col_a.write("**Model A**")
model_a = col_a.selectbox("Model A", llm_models, key="model_a", label_visibility="collapsed")

col_b.write("**Model B**")
model_b = col_b.selectbox("Model B", llm_models, key="model_b", index=1, label_visibility="collapsed")

# Response containers
st.divider()
col_a, col_b = st.columns(2)
results = st.session_state.latest_results

# Loop through both models to avoid code duplication
for col, model_name, model_key in [(col_a, model_a, "model_a"), (col_b, model_b, "model_b")]:
    with col:
        st.subheader(model_name)
        container = st.container(height=400, border=True)

        if results:
            display_response(container, results, model_key)

        st.caption("Performance Metrics")
        if results:
            display_metrics(results, model_key)
        else:  # Show placeholders when no results yet
            latency_col, tokens_col = st.columns(2)
            latency_col.metric("Latency (s)", "—")
            tokens_col.metric("Tokens", "—")
```

* **`llm_models = [...]`**: **Defines the list of available models** including Llama, Mistral, Mixtral, Claude, and OpenAI GPT variants for comparison.
* **`st.title(":material/compare: Select Models")`**: **Creates the main page title** with a Material icon (compare icon) to visually represent the comparison feature.
* **`col_a, col_b = st.columns(2)`**: **Creates two equal-width columns** with meaningful names instead of using array indices like `cols[0]` and `cols[1]`. This makes the code more beginner-friendly.
* **`col_a.selectbox(...)`**: **Creates a dropdown menu** in the first column for Model A selection.
* **`label_visibility="collapsed"`**: **Hides the selectbox label** since we're showing our own bold heading above it.
* **`index=1`**: **Sets Model B's default selection** to the second model in the list, ensuring different models are selected by default.
* **`st.divider()`**: **Creates a visual separator** between the model selection area and the response containers.
* **`st.container(height=400, border=True)`**: **Creates a fixed-height container** (400 pixels) with a border, ensuring both response areas are the same size and scrollable if content overflows.
* **`for col, model_name, model_key in [...]`**: **Loop pattern with tuple unpacking** that eliminates code duplication for Model A and Model B. Each iteration unpacks the column, model name, and key for that model.
* **`st.caption("Performance Metrics")`**: **Adds a small caption** above the metrics to label what the numbers represent.
* **Placeholder metrics**: When no results exist yet, we show "—" for both latency and tokens to indicate empty state.

#### 3. Sequential Execution and Display

```python
# Chat input and execution
st.divider()
if prompt := st.chat_input("Enter your message to compare models"):
    # Run models sequentially (Model A, then Model B)
    with st.status(f"Running {model_a}..."):
        result_a = run_model(model_a, prompt)
    with st.status(f"Running {model_b}..."):
        result_b = run_model(model_b, prompt)

    # Store results in session state (replaces previous results)
    st.session_state.latest_results = {"prompt": prompt, "model_a": result_a, "model_b": result_b}
    st.rerun()  # Trigger rerun to display results

# Display helper functions
def display_response(container, results: dict, model_key: str):
    """Display chat messages in container."""
    with container:
        with st.chat_message("user"):
            st.write(results["prompt"])
        with st.chat_message("assistant"):
            st.write(results[model_key]["response_text"])

def display_metrics(results: dict, model_key: str):
    """Display metrics for a model."""
    latency_col, tokens_col = st.columns(2)

    latency_col.metric("Latency (s)", f"{results[model_key]['latency']:.1f}")
    tokens_col.metric("Tokens", results[model_key]['tokens'])
```

* **`if prompt := st.chat_input(...)`**: **Creates the chat input box** at the bottom of the screen. The walrus operator (`:=`) assigns and checks the value in one line.
* **`st.divider()`**: **Creates a visual separator** before the chat input to clearly distinguish the input area from the results above.
* **Sequential execution comment**: The inline comment **"Run models sequentially (Model A, then Model B)"** clarifies the execution order for learners.
* **`with st.status(f"Running {model_a}...")`**: **Creates a status indicator** that shows "Running model_name..." while the code inside executes, giving users visual feedback during the wait.
* **Sequential execution**: We **run Model A completely, wait for its result, then run Model B**. The total time is the sum of both models' latencies. While this is slower than parallel execution, it's much simpler to implement and understand.
* **`st.session_state.latest_results = {...}`**: **Stores the results in session state** with inline comment explaining it replaces previous results, so learners understand only the latest prompt and responses are kept (not a full chat history).
* **`st.rerun()`**: **Triggers a rerun** to display the newly stored results in the containers. The inline comment "Trigger rerun to display results" clarifies why this is necessary.
* **`display_response()` and `display_metrics()`**: **Helper functions** that avoid repeating the same code for Model A and Model B.
* **`st.chat_message("user")` and `st.chat_message("assistant")`**: **Create styled message bubbles** that look like a chat interface.
* **`latency_col, tokens_col = st.columns(2)`**: **Creates two columns with meaningful names** for displaying the two metrics side-by-side.
* **`latency_col.metric("Latency (s)", ...)`**: **Displays the latency metric** with 1 decimal place for readability (e.g., "3.2s" instead of "3.234567s").
* **`tokens_col.metric("Tokens", ...)`**: **Displays the estimated token count** as an integer, giving a sense of response length and cost.

When this code runs, you will see a clean comparison interface where you can select two models from 8 options, enter a prompt, and immediately see how they compare in terms of response speed and output length.