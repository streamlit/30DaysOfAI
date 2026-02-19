# Day 28
# Building Apps with AI Assistants using AGENTS.md

import streamlit as st

st.set_page_config(page_title="Day 28: AI-Assisted Development", page_icon=":material/psychology:", layout="wide")

st.title(":material/psychology: Day 28: Building Apps with AI Assistants")
st.write("Learn how to use AGENTS.md to build Streamlit apps effortlessly with AI assistants like ChatGPT, Claude, or Cursor.")

# Sidebar
with st.sidebar:
    st.header(":material/description: AGENTS.md")
    st.info("AGENTS.md is like a README for AI—it contains all patterns, conventions, and instructions that help AI assistants build your apps correctly.", icon=":material/info:")
    
    st.divider()
    
    st.header(":material/link: Resources")
    st.page_link("https://github.com/dataprofessor/streamlit/blob/main/AGENTS.md", label="Download AGENTS.md", icon=":material/download:")
    st.page_link("https://blog.streamlit.io/vibe-code-streamlit-apps-with-ai-using-agents-md-04b7480f754e", label="Read the Blog Post", icon=":material/article:")
    
    st.divider()
    
    st.header(":material/lightbulb: Quick Tips")
    st.success("**Before You Start:**\n\n1. Copy AGENTS.md to your project\n2. Reference it with `@AGENTS.md`\n3. Choose your mode (Quick or Guided)\n4. Let AI build your app!", icon=":material/tips_and_updates:")
    
    st.divider()
    
    st.header(":material/robot: AI Assistants")
    st.write("**Popular Options:**")
    st.write("• ChatGPT (OpenAI)")
    st.write("• Claude (Anthropic)")
    st.write("• Cursor (Editor)")
    st.write("• GitHub Copilot")

# Main Content: Two Modes
st.subheader(":material/rocket: Two Ways to Use AGENTS.md")

tab1, tab2 = st.tabs([":material/flash_on: Mode 1: Quick Start", ":material/quiz: Mode 2: Guided Questions"])

# MODE 1: Quick Start
with tab1:
    st.markdown("### Quick Start with Instructions")
    st.write("If you know what you want, just tell the AI in one go!")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("#### How It Works")
        st.info("""
        **1. Reference AGENTS.md + provide instruction**
        
        The AI will:
        - Use your instruction as the starting point
        - Infer reasonable defaults
        - Ask 1-2 questions only if critical info is missing
        - Build the complete app with all files
        """, icon=":material/info:")
        
        st.markdown("#### Example Prompts")
        
        example_prompts = [
            ("Chatbot", "@AGENTS.md build me a chatbot using Snowflake Cortex"),
            ("Dashboard", "@AGENTS.md create a dashboard with file upload and Plotly charts"),
            ("RAG App", "@AGENTS.md build a RAG application with Cortex Search"),
            ("Data Tool", "@AGENTS.md create a data analysis tool with CSV upload")
        ]
        
        for name, prompt in example_prompts:
            with st.expander(f":material/content_paste: {name}", expanded=False):
                st.code(prompt, language="text")
                if st.button(f"Copy", key=f"copy_mode1_{name}"):
                    st.toast("Prompt copied!", icon=":material/check_circle:")
    
    with col2:
        st.markdown("#### What You Get")
        st.success("""
        **Complete Project:**
        ```
        my_app/
        ├── app.py
        ├── requirements.txt
        └── README.md
        ```
        
        **README includes:**
        - TLDR: One sentence summary
        - Features: Bullet list
        - Run Locally: Commands
        - Deploy to Community Cloud
        - Deploy to SiS
        """, icon=":material/folder:")
        
        st.markdown("#### When to Use")
        st.write(":material/check_circle: You know exactly what you want")
        st.write(":material/check_circle: You want fast results")
        st.write(":material/check_circle: You're comfortable with defaults")

# MODE 2: Guided Questions
with tab2:
    st.markdown("### Guided Sequential Questions")
    st.write("Not sure what you need? Let the AI guide you through questions, **one at a time**.")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("#### How It Works")
        st.info("""
        **1. Just reference AGENTS.md:**
        ```
        @AGENTS.md
        ```
        
        **2. AI asks ONE question at a time:**
        
        Question 1: "What would you like to build?"
        → chatbot, dashboard, data tool
        
        Question 2: "Where will it run?"
        → local, Community Cloud, Snowflake
        
        Question 3: "What's your data source?" (if relevant)
        → CSV, Snowflake, APIs
        
        Question 4: "Which LLM?" (if AI-related)
        → Cortex or OpenAI
        
        **3. AI builds complete app**
        """, icon=":material/quiz:")
        
        st.markdown("#### Example Flow")
        
        with st.container(border=True):
            st.markdown("**Example 1: Chatbot App**")
            
            qa_chatbot = [
                (":material/person: You", "@AGENTS.md"),
                (":material/smart_toy: AI", "What would you like to build?"),
                (":material/person: You", "a simple chatbot"),
                (":material/smart_toy: AI", "Where will it run?"),
                (":material/person: You", "Community Cloud"),
                (":material/smart_toy: AI", "Which LLM?"),
                (":material/person: You", "Cortex"),
                (":material/smart_toy: AI", ":material/check_circle: Building your chatbot app...")
            ]
            
            for speaker, message in qa_chatbot:
                if "You" in speaker:
                    st.markdown(f"**{speaker}**: `{message}`")
                else:
                    st.markdown(f"**{speaker}**: {message}")
        
        with st.container(border=True):
            st.markdown("**Example 2: Stock Dashboard**")
            
            qa_dashboard = [
                (":material/person: You", "@AGENTS.md"),
                (":material/smart_toy: AI", "What would you like to build?"),
                (":material/person: You", "dashboard"),
                (":material/smart_toy: AI", "Where will it run?"),
                (":material/person: You", "Snowflake"),
                (":material/smart_toy: AI", "What's your data source?"),
                (":material/person: You", "yfinance"),
                (":material/smart_toy: AI", ":material/check_circle: Building your dashboard...")
            ]
            
            for speaker, message in qa_dashboard:
                if "You" in speaker:
                    st.markdown(f"**{speaker}**: `{message}`")
                else:
                    st.markdown(f"**{speaker}**: {message}")
            
            st.caption(":material/lightbulb: Note: AI didn't ask about LLM because dashboards don't need them!")
    
    with col2:
        st.markdown("#### What You Get")
        st.success("""
        **Same Complete Project:**
        ```
        my_app/
        ├── app.py
        ├── requirements.txt
        └── README.md
        ```
        
        **AI automatically:**
        - Infers UI components
        - Adds caching where beneficial
        - Handles environment differences
        - Omits st.set_page_config() for SiS
        """, icon=":material/auto_awesome:")
        
        st.markdown("#### When to Use")
        st.write(":material/check_circle: You're exploring ideas")
        st.write(":material/check_circle: You want guidance")
        st.write(":material/check_circle: You're learning")

st.divider()

# Pattern Selection Guide
st.subheader(":material/rule: What the AI Builds Based on Your Request")

pattern_table = """
| You Say | AI Uses |
|---------|---------|
| chatbot, AI assistant | Chat Interface + Streaming + `ai_complete` |
| dashboard, visualization | Basic App + Plotly/Altair Charts |
| data analysis | File Upload + DataFrame Styling |
| RAG, search documents | Chat + Cortex Search + `ai_complete` |
| multipage | `st.navigation` + Session State |
| Snowflake, SiS | Omit `st.set_page_config` + Cortex patterns |
"""

st.markdown(pattern_table)
st.caption(":material/lightbulb: Caching is added automatically wherever beneficial")

st.divider()

# Key Patterns
st.subheader(":material/code: Key Patterns AGENTS.md Teaches")

col1, col2 = st.columns(2)

with col1:
    with st.expander(":material/cable: Universal Connection (Works Everywhere)", expanded=True):
        st.code("""@st.cache_resource
def get_session():
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except:
        from snowflake.snowpark import Session
        return Session.builder.configs(
            st.secrets["connections"]["snowflake"]
        ).create()""", language="python")
    
    with st.expander(":material/smart_toy: Cortex LLM with ai_complete"):
        st.code("""@st.cache_data(show_spinner=False)
def call_llm(prompt: str, model: str = "claude-3-5-sonnet") -> str:
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt).alias("response")
    )
    response_raw = df.collect()[0][0]
    response_json = json.loads(response_raw)
    
    if isinstance(response_json, dict) and "choices" in response_json:
        return response_json["choices"][0]["messages"]
    return str(response_json)""", language="python")

with col2:
    with st.expander(":material/chat: Chat Interface with Streaming"):
        st.code("""st.session_state.setdefault("messages", [])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Your message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        response = st.write_stream(stream_response(prompt))
    
    st.session_state.messages.append({"role": "assistant", "content": response})""", language="python")
    
    with st.expander(":material/target: SiS-Aware Code"):
        st.markdown("""
        **AI automatically knows:**
        - :material/check_circle: SiS deployment → No `st.set_page_config()`
        - :material/check_circle: Community Cloud → Include `st.set_page_config()`
        - :material/check_circle: Both → Use universal connection pattern
        """)

st.divider()

# Common Pitfalls Prevented
st.subheader(":material/shield: Common Pitfalls AGENTS.md Prevents")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 1. Duplicate Keys")
    st.code("""# AI adds unique keys
st.text_input("Name:", key="first")
st.text_input("Name:", key="last")""", language="python")

with col2:
    st.markdown("#### 2. Page Config in SiS")
    st.code("""# AI omits for SiS
# st.set_page_config()
# (not supported in SiS)""", language="python")

with col3:
    st.markdown("#### 3. Session State")
    st.code("""# AI initializes in main
st.session_state.setdefault("df", None)
pg = st.navigation(...)
pg.run()""", language="python")

st.divider()

# Getting Started
st.subheader(":material/play_circle: Getting Started")

col1, col2 = st.columns([2, 3])

with col1:
    st.markdown("#### Step 1: Get AGENTS.md")
    st.write("Copy AGENTS.md to your project or a central location")
    
    st.link_button(
        ":material/download: Download AGENTS.md",
        "https://github.com/dataprofessor/streamlit/blob/main/AGENTS.md",
        use_container_width=True
    )
    
    st.link_button(
        ":material/article: Read the Blog Post",
        "https://blog.streamlit.io/vibe-code-streamlit-apps-with-ai-using-agents-md-04b7480f754e",
        use_container_width=True
    )
    
    st.markdown("#### Step 2: Choose Your Mode")
    st.write("**Mode 1:** Quick instruction")
    st.code("@AGENTS.md build a chatbot")
    st.write("**Mode 2:** Guided questions")
    st.code("@AGENTS.md")
    
    st.markdown("#### Step 3: Answer Questions")
    st.write("(if prompted - Mode 2 only)")
    
    st.markdown("#### Step 4: Deploy")
    st.write("Follow the README deployment instructions")

with col2:
    st.markdown("#### Why This Works")
    
    st.success("""
    **1. Minimal friction**
    One file reference → a few questions → complete app
    
    **2. Smart defaults**
    Caching, error handling, UI components inferred
    
    **3. Environment-aware**
    Handles SiS vs Community Cloud differences
    
    **4. Complete output**
    app.py, requirements.txt, README.md
    
    **5. Consistent patterns**
    Same proven code every time
    """, icon=":material/check_circle:")

st.divider()

# Examples
st.subheader(":material/folder_open: Example Apps Built with AGENTS.md")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### :material/chat: Chatbot App")
        st.markdown("**The Q&A Flow:**")
        st.code("""Q: What would you like to build?
A: a simple chatbot

Q: Where will it run?
A: Community Cloud

Q: Which LLM?
A: Cortex""")
        
        st.markdown("**Features:**")
        st.write("• Chat interface with streaming")
        st.write("• Model selector (Claude/Llama/Mistral)")
        st.write("• Conversation history")
        st.write("• Response caching")
        
        st.caption(":material/folder: Location: `examples/chatbot_app/`")

with col2:
    with st.container(border=True):
        st.markdown("### :material/bar_chart: Stock Dashboard")
        st.markdown("**The Q&A Flow:**")
        st.code("""Q: What would you like to build?
A: dashboard

Q: Where will it run?
A: Snowflake

Q: What's your data source?
A: yfinance""")
        
        st.markdown("**Features:**")
        st.write("• Candlestick charts")
        st.write("• Volume analysis")
        st.write("• Key metrics")
        st.write("• Time period selector")
        
        st.caption(":material/folder: Location: `examples/stock_dashboard/`")

st.divider()

# Conclusion
st.subheader(":material/celebration: Start Vibe Coding!")

st.success("""
With AGENTS.md, you can truly **vibe code** your Streamlit apps. Just describe what you want (or let it guide you), 
answer a few questions, and watch your app come to life.

**No more:**
- :material/cancel: Explaining patterns repeatedly
- :material/cancel: Fixing inconsistent code
- :material/cancel: Wrestling with deployment differences

**Just:**
- :material/check_circle: Reference AGENTS.md
- :material/check_circle: Choose your mode
- :material/check_circle: Get a complete, deployment-ready app

Try it today and experience the future of AI-assisted development! :material/rocket:
""", icon=":material/auto_awesome:")

st.divider()
st.caption("Day 28: Building Apps with AI Assistants | 30 Days of AI with Streamlit")
