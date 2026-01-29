For today's challenge, we'll learn how to **vibe code** Streamlit apps using AGENTS.md—an open standard for guiding AI coding assistants. Instead of explaining patterns repeatedly, you reference one file and let the AI build complete, production-ready applications.

---

## :material/info: What is AGENTS.md?

[AGENTS.md](https://agents.md) is an open format adopted by over 60,000 open-source projects. It's like a **README for AI agents**—a dedicated file that provides context, conventions, and instructions that help AI assistants work effectively on your project.

**Key Insight:**
- **README.md** = For humans
- **AGENTS.md** = For AI agents

The Streamlit AGENTS.md aggregates all 27 days of patterns from this challenge into one reference document. When you share it with an LLM, the AI instantly knows:
- Code conventions and patterns
- Cortex AI integration methods
- Deployment considerations (SiS vs Community Cloud)
- Best practices and common pitfalls

---

## :material/robot: Sidebar: Your Quick Reference

The app includes a helpful sidebar with:

### AGENTS.md Overview
A quick reminder that AGENTS.md is like a README for AI—it contains all patterns, conventions, and instructions that help AI assistants build your apps correctly.

### Resources
Direct links to:
- **Download AGENTS.md** - Get the file from GitHub
- **Read the Blog Post** - In-depth guide on using AGENTS.md

### Quick Tips
**Before You Start:**
1. Copy AGENTS.md to your project
2. Reference it with `@AGENTS.md`
3. Choose your mode (Quick or Guided)
4. Let AI build your app!

### AI Assistants
Popular AI coding assistants you can use with AGENTS.md:
- ChatGPT (OpenAI)
- Claude (Anthropic)
- Cursor (Editor)
- GitHub Copilot

---

## :material/rocket: Two Ways to Use AGENTS.md

Our AGENTS.md supports **two modes of operation**, making it effortless to get started:

### Mode 1: Quick Start with Instructions

If you know what you want, just tell the AI in one go:

```
@AGENTS.md build me a chatbot using Snowflake Cortex
```

**The AI will:**
- Use your instruction as the starting point
- Infer reasonable defaults
- Ask only 1-2 clarifying questions if critical info is missing
- Build the complete app with all files (app.py, requirements.txt, README.md)

**Example Prompts:**
```
@AGENTS.md build a chatbot with Cortex Complete

@AGENTS.md create a dashboard with file upload and Plotly charts

@AGENTS.md build a RAG application with Cortex Search
```

### Mode 2: Guided Sequential Questions

If you're not sure what you need, just reference the file:

```
@AGENTS.md
```

**The AI will guide you through questions ONE AT A TIME:**

1. **"What would you like to build?"** → chatbot, dashboard, data tool
2. **"Where will it run?"** → local, Community Cloud, Snowflake
3. **"What's your data source?"** (if relevant) → CSV, Snowflake, APIs
4. **"Which LLM?"** (only if AI-related) → Cortex or OpenAI

Then it builds, inferring UI components from app type and adding caching automatically.

---

## :material/folder_open: Example Apps

Two complete example apps were built using the AGENTS.md guided flow:

### Example 1: Chatbot (`examples/chatbot_app/`)

**The Q&A Flow:**

| Question | Answer |
|----------|--------|
| What would you like to build? | a simple chatbot |
| Where will it run? | Community Cloud |
| Which LLM? | Cortex |

**What Got Created:**
```
examples/chatbot_app/
├── app.py              # Chat interface with streaming
├── requirements.txt    # streamlit, snowflake-snowpark-python
└── README.md           # Deployment instructions
```

**Features:** Chat interface, model selector (Claude/Llama/Mistral), conversation history, response caching.

Four questions. Complete app. Ready to deploy.

### Example 2: Stock Dashboard (`examples/stock_dashboard/`)

**The Q&A Flow:**

| Question | Answer |
|----------|--------|
| What would you like to build? | dashboard |
| Where will it run? | Snowflake |
| What's your data source? | yfinance |

**What Got Created:**
```
examples/stock_dashboard/
├── app.py              # Dashboard with Plotly charts
├── requirements.txt    # streamlit, yfinance, plotly
└── README.md           # Deployment instructions
```

**Features:** Candlestick charts, volume analysis, key metrics, time period selector.

Three questions. The AI knew not to ask about LLMs (dashboards don't need them) and automatically omitted `st.set_page_config()` for SiS compatibility.

---

## :material/code: Key Patterns AGENTS.md Teaches

### 1. Universal Database Connection

Works across all three deployment environments:

```python
@st.cache_resource
def get_session():
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except:
        from snowflake.snowpark import Session
        return Session.builder.configs(
            st.secrets["connections"]["snowflake"]
        ).create()
```

### 2. Snowflake Cortex LLM with `ai_complete`

The recommended pattern for universal compatibility:

```python
import json
from snowflake.snowpark.functions import ai_complete

@st.cache_data(show_spinner=False)
def call_llm(prompt: str, model: str = "claude-3-5-sonnet") -> str:
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt).alias("response")
    )
    response_raw = df.collect()[0][0]
    response_json = json.loads(response_raw)
    
    if isinstance(response_json, dict) and "choices" in response_json:
        return response_json["choices"][0]["messages"]
    return str(response_json)
```

### 3. Chat Interface with Streaming

```python
st.session_state.setdefault("messages", [])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Your message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        response = st.write_stream(stream_response(prompt))
    
    st.session_state.messages.append({"role": "assistant", "content": response})
```

### 4. SiS-Aware Code

The AI automatically knows:
- **SiS deployment** → No `st.set_page_config()`
- **Community Cloud** → Include `st.set_page_config()`
- **Both** → Use the universal connection pattern

---

## :material/rule: Pattern Selection Guide

Based on what you ask for, the AI selects the right patterns:

| You Say | AI Uses |
|---------|---------|
| chatbot, AI assistant | Chat Interface + Streaming + `ai_complete` |
| dashboard, visualization | Basic App + Plotly/Altair Charts |
| data analysis | File Upload + DataFrame Styling |
| RAG, search documents | Chat + Cortex Search + `ai_complete` |
| multipage | `st.navigation` + Session State |
| Snowflake, SiS | Omit `st.set_page_config` + Cortex patterns |

Caching is added automatically wherever beneficial.

---

## :material/shield: Common Pitfalls Prevented

The AGENTS.md teaches the AI to avoid common mistakes:

### 1. Duplicate Widget Keys
```python
# AI learns to always add unique keys
st.text_input("Name:", key="first_name")
st.text_input("Name:", key="last_name")
```

### 2. Page Config in SiS
```python
# AI omits st.set_page_config() when targeting SiS
# (it's not supported)
```

### 3. Session State in Multipage Apps
```python
# AI initializes in main app.py, not individual pages
st.session_state.setdefault("df", None)
pg = st.navigation(...)
pg.run()
```

---

## :material/play_circle: Getting Started

### Step 1: Get the AGENTS.md

**Download:** [AGENTS.md from GitHub](https://github.com/dataprofessor/streamlit/blob/main/AGENTS.md)

Copy the Streamlit AGENTS.md to your project or a central location where your AI assistant can access it.

**Learn More:** [Read the Blog Post](https://blog.streamlit.io/vibe-code-streamlit-apps-with-ai-using-agents-md-04b7480f754e) for in-depth coverage of how to use AGENTS.md effectively.

### Step 2: Reference It

In Cursor or your AI coding tool:

**Quick build:**
```
@AGENTS.md build a data dashboard with file upload
```

**Guided flow:**
```
@AGENTS.md
```

### Step 3: Answer Questions (if prompted)

The AI asks only what it needs to know, one question at a time.

### Step 4: Deploy

Your app comes with a README containing deployment instructions for all three targets (local, Community Cloud, SiS).

---

## :material/celebration: Why This Works

The AGENTS.md approach works because:

1. **Minimal friction**: One file reference, a few questions, complete app
2. **Smart defaults**: Caching, error handling, and UI components are inferred
3. **Environment-aware**: Automatically handles SiS vs Community Cloud differences
4. **Complete output**: Every app includes app.py, requirements.txt, README.md
5. **Consistent patterns**: Same proven code patterns every time

---

## :material/auto_awesome: Vibe Coding in Action

With AGENTS.md, you can truly **vibe code** your Streamlit apps. Just describe what you want (or let it guide you), answer a few questions, and watch your app come to life.

**No more:**
- :material/cancel: Explaining patterns repeatedly
- :material/cancel: Fixing inconsistent code
- :material/cancel: Wrestling with deployment differences

**Just:**
- :material/check_circle: Reference AGENTS.md
- :material/check_circle: Choose your mode (Quick or Guided)
- :material/check_circle: Get a complete, deployment-ready app

This is the future of AI-assisted development: effortless, consistent, and production-ready! :material/rocket:

---

### :material/library_books: Resources
- [Download AGENTS.md from GitHub](https://github.com/dataprofessor/streamlit/blob/main/AGENTS.md) - Get the complete AGENTS.md file
- [Vibe Code Streamlit Apps with AI Blog Post](https://blog.streamlit.io/vibe-code-streamlit-apps-with-ai-using-agents-md-04b7480f754e) - In-depth guide on using AGENTS.md
- [AGENTS.md Official Website](https://agents.md) - Learn about the open standard
- [Streamlit Documentation](https://docs.streamlit.io) - Official Streamlit docs
- [Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql) - Cortex AI functions
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit) - Deploy to Snowflake
