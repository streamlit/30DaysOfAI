For today's challenge, we're rebuilding **Day 5's LinkedIn Post Generator** using **LangChain**, a framework that makes LLM applications cleaner, more reusable, and easier to extend. Instead of writing raw Cortex API calls with f-strings, we'll use LangChain's `PromptTemplate` and LangChain Expression Language (LCEL) to create composable chains.

> :material/warning: **Prerequisite:** You need LangChain packages installed to run this app.

---

### :material/download: Installing Prerequisites

Before running this app, you need to install the required LangChain packages.

**For `requirements.txt`:**
```txt
langchain-core>=0.3.0
langchain-snowflake>=0.1.0
snowflake-snowpark-python>=1.18.0,<2.0
streamlit>=1.53.0
```

**Install with pip:**
```bash
pip install langchain-core langchain-snowflake snowflake-snowpark-python streamlit
```

**Package Breakdown:**
- `langchain-core` - Core LangChain functionality (PromptTemplate, LCEL, output parsers)
- `langchain-snowflake` - Snowflake Cortex integration for LangChain (ChatSnowflake)
- `snowflake-snowpark-python` - Snowflake connection and session management
- `streamlit` - Web app framework

---

### :material/info: What is LangChain?

**LangChain** is a framework for building LLM applications with reusable, composable components:

- :material/description: **PromptTemplate**: Reusable prompts with variables
- :material/link: **LangChain Expression Language (LCEL)**: Chain components with `|` operator
- :material/verified: **Type-safe outputs**: Structured responses with Pydantic (coming in Day 30!)

**Why LangChain?**
- Cleaner, more readable code
- No manual JSON parsing
- Easy to extend and compose
- Works with multiple LLM providers

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Snowflake Connection Setup

```python
import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_snowflake import ChatSnowflake

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()
```

* **`from langchain_core.prompts import PromptTemplate`**: Imports the **PromptTemplate** class for creating reusable prompt templates.
* **`from langchain_snowflake import ChatSnowflake`**: Imports the **LangChain wrapper for Snowflake Cortex** models.
* **Universal connection pattern**: Works in both SiS and external environments.

#### 2. Creating a PromptTemplate

```python
# Create prompt template
template = PromptTemplate.from_template(
    """You are an expert social media manager. Generate a LinkedIn post based on:

    Tone: {tone}
    Desired Length: Approximately {word_count} words
    Use content from this URL: {content}

    Generate only the LinkedIn post text. Use dash for bullet points."""
)
```

* **`PromptTemplate.from_template(...)`**: Creates a **reusable template** with placeholders wrapped in `{curly_braces}`.
* **Placeholders**: `{tone}`, `{word_count}`, and `{content}` will be filled in at runtime.
* **Benefits**: No messy f-strings, templates can be stored, shared, and tested independently.

#### 3. Creating the LLM and Chain

```python
# Create LLM and chain
llm = ChatSnowflake(model="claude-3-5-sonnet", session=session)
chain = template | llm
```

* **`ChatSnowflake(model="claude-3-5-sonnet", session=session)`**: Creates a **LangChain-compatible LLM** using Snowflake Cortex.
* **`chain = template | llm`**: Uses **LCEL (LangChain Expression Language)** to create a chain. The `|` operator pipes the template output into the LLM.
* **What happens**: Template formats the prompt → LLM generates the response.

#### 4. Building the Streamlit UI

```python
# UI
st.title(":material/post: LinkedIn Post Generator")
content = st.text_input("Content URL:", "https://docs.snowflake.com/en/user-guide/views-semantic/overview")
tone = st.selectbox("Tone:", ["Professional", "Casual", "Funny"])
word_count = st.slider("Approximate word count:", 50, 300, 100)
```

* **`st.title(...)`**: Creates the app title with a Material icon.
* **`st.text_input(...)`**: Input field for the content URL with a default value.
* **`st.selectbox(...)`**: Dropdown for selecting the post tone.
* **`st.slider(...)`**: Slider for adjusting the desired word count.

#### 5. Invoking the Chain

```python
if st.button("Generate Post"):
    result = chain.invoke({"content": content, "tone": tone, "word_count": word_count})
    st.subheader("Generated Post:")
    st.markdown(result.content)
```

* **`chain.invoke({...})`**: Calls the chain with a **dictionary of variables** that match the template placeholders.
* **`result.content`**: The LangChain response object has a `.content` attribute containing the generated text.
* **No JSON parsing**: LangChain handles the response structure automatically!

---

### :material/compare: Comparison: Day 5 vs Day 29

Let's compare the raw Cortex approach from Day 5 with today's LangChain approach:

#### Day 5: Raw Cortex API

```python
prompt = f"""You are an expert social media manager.
Tone: {tone}
Desired Length: {word_count} words
Use content from: {content}"""

df = session.range(1).select(ai_complete(model="claude-3-5-sonnet", prompt=prompt))
response_raw = df.collect()[0][0]
response = json.loads(response_raw)
text = response.get("choices", [{}])[0].get("messages", "")
```

**Issues:**
- Manual f-string formatting
- Multiple lines of JSON parsing
- Error-prone extraction of nested response

#### Day 29: LangChain

```python
template = PromptTemplate.from_template("""You are an expert social media manager.
Tone: {tone}
Desired Length: {word_count} words
Use content from: {content}""")

chain = template | llm
result = chain.invoke({"tone": tone, "word_count": word_count, "content": content})
text = result.content
```

**Benefits:**
- ✅ Cleaner, more readable code
- ✅ No manual JSON parsing
- ✅ Reusable template object
- ✅ Easy to extend (add more steps to the chain)

---

### :material/school: Key LangChain Concepts

#### PromptTemplate

Replace messy f-strings with reusable templates:

```python
# Create once, use many times
template = PromptTemplate.from_template(
    "Generate a {tone} post about {topic} in {word_count} words"
)

# Use with different inputs
result1 = chain.invoke({"tone": "professional", "topic": "AI", "word_count": 100})
result2 = chain.invoke({"tone": "casual", "topic": "Coffee", "word_count": 50})
```

#### LCEL (LangChain Expression Language)

Chain components with the pipe operator (`|`):

```python
# Simple chain: template → LLM
chain = template | llm

# Extended chain: template → LLM → output parser
chain = template | llm | output_parser

# What happens:
# 1. Template formats the input variables
# 2. LLM generates a response
# 3. Output parser structures the result
```

#### ChatSnowflake

LangChain wrapper for Snowflake Cortex models:

```python
# Create the LLM wrapper
llm = ChatSnowflake(model="claude-3-5-sonnet", session=session)

# Available models:
# - claude-3-5-sonnet
# - llama3-70b
# - mistral-large
# - And more Cortex models
```

---

### :material/lightbulb: Try It Out

1. **Enter a content URL** (or use the default Snowflake docs link)
2. **Select a tone**: Professional, Casual, or Funny
3. **Adjust the word count** using the slider
4. **Click "Generate Post"** to see the LinkedIn post

Try different combinations to see how the LLM adapts its output!

---

### :material/trending_up: Why Use LangChain?

**Advantages:**
- ✅ **Cleaner code**: No f-string formatting or JSON parsing
- ✅ **Composable**: Chain multiple components together
- ✅ **Reusable**: Templates can be shared and tested
- ✅ **Extensible**: Easy to add output parsers, memory, tools
- ✅ **Provider-agnostic**: Switch LLMs by changing one line

**When to use LangChain:**
- Building complex LLM applications
- Need structured outputs (Day 30!)
- Want cleaner, more maintainable code
- Building applications that may need to switch LLM providers

---

### :material/library_books: Resources

- [LangChain Documentation](https://python.langchain.com/docs/)
- [LangChain Snowflake Integration](https://python.langchain.com/docs/integrations/chat/snowflake/)
- [PromptTemplate Documentation](https://python.langchain.com/docs/modules/model_io/prompts/)
- [LCEL (LangChain Expression Language)](https://python.langchain.com/docs/expression_language/)
- [Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex)

---

### :material/rocket: Next Steps

- **Day 30**: Take LangChain further with **structured output using Pydantic**!
- Try adding more steps to the chain (output parsers, validators)
- Experiment with different Cortex models
- Build more complex chains with multiple LLM calls
