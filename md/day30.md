For today's challenge, we're taking LangChain to the next level with **structured output using Pydantic**. Instead of getting plain text responses that need manual parsing, we'll use `PydanticOutputParser` to get type-safe, validated objects with guaranteed fields. This eliminates JSON parsing errors, provides IDE autocomplete, and makes displaying data in Streamlit clean and easy.

> :material/warning: **Prerequisite:** You need LangChain and Pydantic packages installed to run this app.

---

### :material/download: Installing Prerequisites

Before running this app, you need to install the required LangChain and Pydantic packages.

**For `requirements.txt`:**
```txt
langchain-core>=0.3.0
langchain-snowflake>=0.1.0
pydantic>=2.0.0
snowflake-snowpark-python>=1.18.0,<2.0
streamlit>=1.53.0
```

**Install with pip:**
```bash
pip install langchain-core langchain-snowflake pydantic snowflake-snowpark-python streamlit
```

**Package Breakdown:**
- `langchain-core` - Core LangChain functionality (ChatPromptTemplate, PydanticOutputParser, LCEL)
- `langchain-snowflake` - Snowflake Cortex integration for LangChain (ChatSnowflake)
- `pydantic` - Data validation and type-safe structured outputs (BaseModel, Field, Literal)
- `snowflake-snowpark-python` - Snowflake connection and session management
- `streamlit` - Web app framework

---

### :material/info: What is Structured Output?

**Structured output** means getting LLM responses as **typed Python objects** instead of plain text strings.

**Without structured output:**
```python
response = "The plant is called Pothos. It needs low water..."
# How do you extract the plant name? The water level? 😰
```

**With structured output:**
```python
response.name       # "Pothos"
response.water      # "Low"
response.care_tips  # "Water when soil is dry..."
# Type-safe, IDE autocomplete, guaranteed fields! 🎉
```

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Imports and Connection Setup

```python
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_snowflake import ChatSnowflake
from pydantic import BaseModel, Field
from typing import Literal

# Connect to Snowflake
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()
```

* **`from langchain_core.output_parsers import PydanticOutputParser`**: Imports the **output parser** that converts LLM text to Pydantic objects.
* **`from pydantic import BaseModel, Field`**: Imports Pydantic for defining **typed data models**.
* **`from typing import Literal`**: Imports `Literal` for **constraining values** to specific options.

#### 2. Defining the Output Schema with Pydantic

```python
# Define output schema
class PlantRecommendation(BaseModel):
    name: str = Field(description="Plant name")
    water: Literal["Low", "Medium", "High"] = Field(description="Water requirement")
    light: Literal["Low", "Medium", "High"] = Field(description="Light requirement")
    difficulty: Literal["Beginner", "Intermediate", "Expert"] = Field(description="Care difficulty level")
    care_tips: str = Field(description="Brief care instructions")
```

* **`class PlantRecommendation(BaseModel)`**: Defines a **Pydantic model** that describes the expected response structure.
* **`name: str`**: A required string field for the plant name.
* **`Literal["Low", "Medium", "High"]`**: **Constrains the value** to exactly these three options. Pydantic will reject any other values!
* **`Field(description="...")`**: Adds descriptions that help the LLM understand what each field should contain.

> :material/lightbulb: **Key Insight**: Using `Literal` types ensures the LLM can only return those exact values. If it tries to return "Very Low" or "low" (wrong case), Pydantic validation will fail!

#### 3. Creating the Parser

```python
# Create parser
parser = PydanticOutputParser(pydantic_object=PlantRecommendation)
```

* **`PydanticOutputParser(pydantic_object=PlantRecommendation)`**: Creates a parser that will:
  1. Generate JSON schema instructions for the LLM
  2. Parse the LLM's JSON response
  3. Validate it against your Pydantic schema
  4. Return a type-safe Python object

#### 4. Creating the Prompt Template

```python
# Create template with format instructions
template = ChatPromptTemplate.from_messages([
    ("system", "You are a plant expert. {format_instructions}"),
    ("human", "Recommend a plant for: {location}, {experience} experience, {space} space")
])
```

* **`ChatPromptTemplate.from_messages([...])`**: Creates a **chat-style template** with system and human messages.
* **`{format_instructions}`**: A placeholder where the parser will inject JSON schema instructions telling the LLM how to format its response.
* **`("system", "...")`**: Sets the assistant's persona and includes format instructions.
* **`("human", "...")`**: The user's request with placeholders for input variables.

#### 5. Building the Chain

```python
# Create LLM and chain
llm = ChatSnowflake(model="claude-3-5-sonnet", session=session)
chain = template | llm | parser
```

* **`chain = template | llm | parser`**: Creates a **three-step chain**:
  1. `template`: Formats the prompt with variables and format instructions
  2. `llm`: Generates a JSON response
  3. `parser`: Parses JSON into a typed Pydantic object

#### 6. Building the Streamlit UI

```python
# UI
st.title(":material/potted_plant: Plant Recommender")
location = st.text_input("Location:", "Apartment in Seattle")
experience = st.selectbox("Experience:", ["Beginner", "Intermediate", "Expert"])
space = st.text_input("Space:", "Small desk")
```

* **`st.title(...)`**: Creates the app title with a plant emoji icon.
* **`st.text_input("Location:", ...)`**: Text input for the user's location.
* **`st.selectbox("Experience:", ...)`**: Dropdown for gardening experience level.
* **`st.text_input("Space:", ...)`**: Text input for available space description.

#### 7. Invoking the Chain and Displaying Results

```python
if st.button("Get Recommendation"):
    result = chain.invoke({
        "location": location,
        "experience": experience,
        "space": space,
        "format_instructions": parser.get_format_instructions()
    })

    st.subheader(f":material/eco: {result.name}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Water", result.water)
    col2.metric("Light", result.light)
    col3.metric("Difficulty", result.difficulty)
    st.info(f"**Care:** {result.care_tips}")

    with st.expander(":material/description: See raw JSON response"):
        st.json(result.model_dump())
```

* **`parser.get_format_instructions()`**: Generates **JSON schema instructions** that tell the LLM exactly how to format its response.
* **`result.name`, `result.water`, etc.**: **Type-safe access** with IDE autocomplete! No string key lookups, no `KeyError` exceptions.
* **`st.metric(...)`**: Displays key metrics in a clean, visual format.
* **`result.model_dump()`**: Converts the Pydantic object back to a dictionary for JSON display.

---

### :material/compare: Comparison: Manual Parsing vs Structured Output

#### Before: Manual JSON Parsing

```python
response_raw = df.collect()[0][0]
response = json.loads(response_raw)  # Manual parsing
plant_name = response["name"]  # No type safety, could crash with KeyError
water_level = response["water"]  # Hope it's spelled right!
```

**Problems:**
- ❌ Manual JSON parsing
- ❌ No type safety
- ❌ No IDE autocomplete
- ❌ Runtime errors if keys are wrong

#### After: Structured Output with Pydantic

```python
parser = PydanticOutputParser(pydantic_object=PlantRecommendation)
chain = template | llm | parser
result = chain.invoke({..., "format_instructions": parser.get_format_instructions()})

plant_name = result.name  # Type-safe, IDE autocomplete!
water_level = result.water  # Guaranteed to be "Low", "Medium", or "High"
```

**Benefits:**
- ✅ Automatic JSON parsing
- ✅ Full type safety
- ✅ IDE autocomplete works
- ✅ Validation ensures correct values
- ✅ Compile-time error checking

---

### :material/school: Key Pydantic Concepts

#### Type Safety with Literal

Using `Literal["Low", "Medium", "High"]` ensures the LLM can only return those exact values:

```python
water: Literal["Low", "Medium", "High"]

# Valid: result.water = "Low"
# Valid: result.water = "Medium"
# Invalid: result.water = "Very Low"  # Pydantic will reject!
# Invalid: result.water = "low"       # Wrong case, rejected!
```

#### Field Descriptions

Descriptions help the LLM understand what each field should contain:

```python
name: str = Field(description="Common name of the plant")
water: Literal["Low", "Medium", "High"] = Field(description="Water requirement level")
```

#### Format Instructions

The parser automatically generates instructions for the LLM:

```python
instructions = parser.get_format_instructions()
# Produces something like:
# "Return a JSON object with the following schema:
#  {'name': str, 'water': 'Low'|'Medium'|'High', ...}"
```

---

### :material/lightbulb: Try It Out

1. **Enter your location** (e.g., "Apartment in Seattle", "Office in Austin")
2. **Select your experience level**: Beginner, Intermediate, or Expert
3. **Describe your space** (e.g., "Small desk", "Sunny windowsill", "Dark corner")
4. **Click "Get Recommendation"** to see a personalized plant suggestion

Try different combinations and expand the JSON response to see the structured data!

---

## :material/celebration: Congratulations: Your Journey Begins!

You've completed all 30 days! But this isn't the end; it's the **beginning** of your extended learning journey.

### What You've Mastered (Days 1-28)

- ✅ **Streamlit** for rapid UI development
- ✅ **Snowflake Cortex AI** (Complete, Search, Analyst, Agents)
- ✅ **Production patterns** and best practices
- ✅ **AI-assisted development** workflows (Day 28)

### What You've Discovered (Days 29-30)

- :material/public: **Open source integration**: LangChain and Pydantic are **examples**
- :material/build: **Mix-and-match mindset**: Combine Snowflake with any tool
- :material/door_open: **Gateway opened**: You now know **how** to integrate

### Your Complete AI Application Stack

Here's what you've learned to build with:

```
┌─────────────────────────────────────────────────────────────┐
│              Your AI Application Stack                       │
├─────────────────────────────────────────────────────────────┤
│  UI Layer:         Streamlit                                 │
│  Compute:          Snowflake                                 │
│  LLM Provider:     Cortex AI                                 │
│  Validation:       Pydantic ← NEW!                           │
│  Observability:    TruLens (Day 23)                          │
│  Vector Store:     Snowflake VECTOR(FLOAT, 768) +            │
│                    snowflake-arctic-embed-m (Day 18)         │
│  Semantic Search:  Cortex Search (Day 19)                    │
│  Agent Framework:  Cortex Agents (Days 26-27)                │
│                    + LangChain ← NEW! (Days 29-30)           │
└─────────────────────────────────────────────────────────────┘
```

### Where to Go Next (Your Choice!)

Days 29-30 showed you **how to integrate open source tools**. Now explore:

**Other Frameworks:**
- LlamaIndex for advanced RAG
- Haystack for NLP pipelines
- DSPy for prompt optimization

**Observability:**
- LangSmith for tracing
- Weights & Biases for experiments
- Helicone for LLM analytics

**APIs & Data:**
- FastAPI for REST endpoints
- SQLModel for database models
- Instructor for structured outputs

**Advanced Agents:**
- LangGraph for complex workflows
- AutoGen for multi-agent systems
- CrewAI for collaboration

### The Core Message

**Snowflake + Streamlit give you the foundation.**  
**Open source tools give you flexibility.**  
**You decide what to add to your stack.**

Your journey doesn't end here; it expands! Keep exploring, keep building, and share what you create. The community is excited to see where you go next! 🚀

---

### :material/library_books: Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [LangChain Output Parsers](https://python.langchain.com/docs/modules/model_io/output_parsers/)
- [PydanticOutputParser Reference](https://python.langchain.com/docs/modules/model_io/output_parsers/types/pydantic/)
- [LangChain Snowflake Integration](https://python.langchain.com/docs/integrations/chat/snowflake/)
- [Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex)

---

**Share your learnings**: Tag #30DaysOfAI and show us what you've built!  
**Keep learning**: Explore the tools that excite you most  
**Stay connected**: Join the community and help others on their journey
