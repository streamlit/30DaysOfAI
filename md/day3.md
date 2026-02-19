For today's challenge, our goal is to call a Snowflake Cortex LLM using the OpenAI-compatible REST API. We'll build a Streamlit app that lets a user select a model, enter a prompt, and then stream the response back in real-time.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Imports and Client Setup

```python
import streamlit as st
from openai import OpenAI

conn = st.secrets["connections"]["snowflake"]
host = conn.get("host") or f"{conn['account']}.snowflakecomputing.com"
client = OpenAI(api_key=conn["password"], base_url=f"https://{host}/api/v2/cortex/v1")
```

* **`import streamlit as st`**: Imports the library needed to build the web app's user interface (UI).
* **`from openai import OpenAI`**: Imports the OpenAI client library, which works with Snowflake Cortex's OpenAI-compatible endpoint.
* **`conn = st.secrets[...]`**: Loads Snowflake connection details from the secrets file.
* **`host`**: Constructs the Snowflake host URL from either a direct host or account name.
* **`client`**: Creates an OpenAI client configured to use Snowflake Cortex as the backend, authenticating with a PAT token.

#### 2. Configure the User Interface

```python
llm_models = ["claude-3-5-sonnet", "mistral-large", "llama3.1-8b"]
model = st.selectbox("Select a model", llm_models)

example_prompt = "What is Python?"
prompt = st.text_area("Enter prompt", example_prompt)

streaming_method = st.radio(
    "Streaming Method:",
    ["Direct", "Real Streaming"],
    help="Choose how to stream the response"
)
```

* **`llm_models = [...]`**: Defines a Python list of the model names the user can choose from.
* **`model = st.selectbox(...)`**: Creates a drop-down menu in the UI with the label "Select a model". The user's choice is stored in the `model` variable.
* **`prompt = st.text_area(...)`**: Creates a multi-line text box for the user's prompt, and pre-populates it with the `example_prompt`.
* **`streaming_method = st.radio(...)`**: Adds a radio button to let users choose between direct (non-streaming) and real streaming responses.

#### 3. Generate and Stream the LLM Response

```python
if st.button("Generate Response"):
    messages = [{"role": "user", "content": prompt}]
    
    if streaming_method == "Direct":
        with st.spinner(f"Generating response with `{model}`"):
            response = client.chat.completions.create(model=model, messages=messages, stream=False)
            st.write(response.choices[0].message.content)
    else:
        with st.spinner(f"Generating response with `{model}`"):
            stream = client.chat.completions.create(model=model, messages=messages, stream=True)
        st.write_stream(stream)
```

* **`messages`**: Formats the user prompt as a chat message in the OpenAI format.
* **Direct method**: Calls the API with `stream=False`, waits for the complete response, then displays it all at once.
* **Real Streaming method**: Calls the API with `stream=True`, which returns a generator that yields chunks as they're generated. `st.write_stream()` displays these chunks in real-time.

> :material/lightbulb: **Why streaming matters:** Without streaming, users stare at a blank screen for several seconds while the LLM generates the full response. With streaming, they see words appearing immediately, making the app feel faster and more responsive even though the total time is the same.

---

### :material/key: Secrets Configuration

Your `secrets.toml` file needs to include a PAT (Programmatic Access Token) for authentication:

```toml
[connections.snowflake]
account = "your_account"
password = "your_pat_token"
```

---

### :material/library_books: Resources
- [Snowflake Cortex REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-llm-rest-api)
- [st.write_stream Documentation](https://docs.streamlit.io/develop/api-reference/write-magic/st.write_stream)
- [OpenAI Python Client](https://github.com/openai/openai-python)
