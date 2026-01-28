For today's challenge, we'll build a chat interface for the multi-tool agent created in Day 26. This app demonstrates how to interact with a pre-created agent that can autonomously orchestrate between Cortex Search and Cortex Analyst, showing the agent's thinking process and tool selection in real-time.

---

### :material/settings: How It Works: Step-by-Step

### Prerequisites

Before starting Day 27, ensure you've completed Day 26:
- Multi-tool agent created: `SALES_CONVERSATION_AGENT`
- Database: `CHANINN_SALES_INTELLIGENCE`
- Schema: `DATA`
- Tables: `SALES_CONVERSATIONS` (10 transcripts) and `SALES_METRICS` (10 deals)
- Cortex Search service: `SALES_CONVERSATION_SEARCH`
- Semantic model YAML: `sales_metrics_model.yaml` uploaded to `@MODELS` stage

### 1. Connect to Pre-Created Agent

Day 27 uses the agent created in Day 26 via the pre-created agent API endpoint:

```python
DB_NAME = "CHANINN_SALES_INTELLIGENCE"
SCHEMA_NAME = "DATA"
AGENT_NAME = "SALES_CONVERSATION_AGENT"
AGENT_ENDPOINT = f"/api/v2/databases/{DB_NAME}/schemas/{SCHEMA_NAME}/agents/{AGENT_NAME}:run"
```

**Why Pre-Created Agents?**
- ✅ Consistent configuration across sessions
- ✅ Tools and instructions defined once in Day 26
- ✅ Simplified API calls (only pass messages)
- ✅ Better for production deployments

### 2. Chat Interface Architecture

```
┌──────────────────────────────────────────┐
│          Chat Interface (Day 27)          │
│                                           │
│  User Input → Agent API → Parse Response │
│                                           │
│  Display:                                 │
│  1. Tool Used (ConversationSearch/        │
│     SalesAnalyst)                         │
│  2. Agent Thinking (collapsed expander)   │
│  3. Output (hidden for SQL queries)       │
│  4. Generated SQL (with Run button)       │
│                                           │
└──────────────────────────────────────────┘
```

### 3. Calling the Pre-Created Agent

```python
def call_agent(query: str):
    """Call Cortex Agent API and return parsed response."""
    payload = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": query}]}]
    }
    
    result = {
        "text": "",
        "thinking": "",
        "tool_name": None,
        "tool_type": None,
        "sql": None,
        "events": []
    }
    
    # Call API and parse streaming events
    resp = _snowflake.send_snow_api_request("POST", AGENT_ENDPOINT, {}, {}, payload, None, 60000)
    events = json.loads(resp.get("content", ""))
    
    # Extract thinking, tool info, and results
    for event in events:
        if event.get("event") == "response":
            # Extract thinking from first response event
        elif event.get("event") == "response.tool_use":
            # Capture which tool was used
        elif event.get("event") == "response.tool_result":
            # Extract SQL if available
    
    return result
```

**Key Features:**
- Simplified payload (agent config already exists)
- Event parsing for thinking, tool usage, and results
- Captures first "response" event for concise thinking text

### 4. Display Order: Tool → Thinking → Output → SQL → Auto-Execution

```python
# 1. Show which tool was used (FIRST)
if result["tool_name"] and result["tool_type"]:
    st.caption(f":material/build: Tool: **{result['tool_name']}** (`{result['tool_type']}`)")

# 2. Show thinking if available (SECOND) - expanded by default
if result["thinking"]:
    with st.expander("🤔 Agent Thinking Process", expanded=True):
        st.warning(result["thinking"])

# 3. Show text response (THIRD) - Skip if SQL exists
if not result["sql"]:
    st.markdown(result["text"])

# 4. Show SQL if available (FOURTH, for analyst queries)
if result["sql"]:
    with st.expander(":material/query_stats: Generated SQL", expanded=True):
        st.code(result["sql"], language="sql")

# 5. Execute SQL directly (FIFTH, automatic execution)
if result["sql"]:
    try:
        df = session.sql(result["sql"]).to_pandas()
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"SQL Error: {e}")
```

**Display Logic:**
- **For Conversation Search**: Tool → Thinking (expanded) → Response text
- **For Sales Analyst**: Tool → Thinking (expanded) → SQL → Auto-executed results
- **No manual "Run SQL" button**: Results appear immediately

### 5. Sidebar Configuration Display

```python
with st.sidebar:
    st.header(":material/settings: Configuration")
    st.text_input("Database:", DB_NAME, disabled=True)
    st.text_input("Schema:", SCHEMA_NAME, disabled=True)
    st.text_input("Agent:", AGENT_NAME, disabled=True)
    
    st.divider()
    
    st.subheader(":material/search: Cortex Search")
    st.text_input("Service Name:", "SALES_CONVERSATION_SEARCH", disabled=True)
    st.text_input("Database.Schema:", f"{DB_NAME}.{SCHEMA_NAME}", disabled=True)
    
    st.divider()
    
    st.subheader(":material/query_stats: Cortex Analyst")
    st.text_input("Model File:", "sales_metrics_model.yaml", disabled=True)
    st.text_input("Stage:", "MODELS", disabled=True)
    st.text_input("Database.Schema:", f"{DB_NAME}.{SCHEMA_NAME}", disabled=True)
```

**Benefits:**
- Clear visibility into agent configuration
- Shows both tool configurations
- Helps users understand what data the agent can access

### 6. Example Questions

The app provides two columns of curated questions:

**:material/query_stats: Sales Metrics** (uses SalesAnalyst):
- "What was the total sales volume?"
- "What is the average deal value?"
- "How many deals were closed?"
- "Which sales rep has the most closed deals?"
- "Show me deals by product line"
- "What is the win rate?"

**:material/forum: Conversations** (uses ConversationSearch):
- "Summarize the call with TechCorp Inc"
- "What concerns did TechCorp Inc raise?"
- "Tell me about the SmallBiz Solutions conversation"
- "What was discussed with DataDriven Co?"
- "Summarize the LegalEase Corp discussion"

Users can also type custom questions using the chat input.

---

## :material/psychology: How the Agent Orchestrates

### Example 1: Quantitative Question → SalesAnalyst

**User asks:** *"What was the total sales volume?"*

**Agent's Thinking (visible in expanded expander):**
> "The user is asking about total sales volume, which is a metrics question requiring aggregation. This falls under the SalesAnalyst tool's capabilities."

**Agent Response:**
1. **Tool**: SalesAnalyst (`cortex_analyst_text_to_sql`)
2. **Thinking**: Shows concise reasoning (expanded by default)
3. **SQL**: Displays generated query in expanded code block
4. **Results**: Automatically executes SQL and displays dataframe
5. **Output**: "I attempted to..." text is hidden for cleaner UX

### Example 2: Qualitative Question → ConversationSearch

**User asks:** *"Summarize the TechCorp Inc conversation"*

**Agent's Thinking (visible in expanded expander):**
> "The user wants a summary of a specific conversation. This requires searching sales conversation transcripts. I should use the ConversationSearch tool."

**Agent Response:**
1. **Tool**: ConversationSearch (`cortex_search`)
2. **Thinking**: Shows reasoning (expanded by default)
3. **Output**: Full answer text with conversation details
4. **SQL**: None (search tool doesn't generate SQL)

---

## :material/compare: Day 26 vs. Day 27

| Aspect | Day 26 | Day 27 |
|--------|--------|--------|
| **Purpose** | Agent setup & configuration | Chat interface & interaction |
| **UI Focus** | Data setup + Agent creation | Real-time chat with agent |
| **Agent Type** | Pre-created agent object | Uses Day 26's agent |
| **API Endpoint** | N/A (uses SQL DDL) | `/api/v2/databases/.../agents/...:run` |
| **Thinking Display** | No | Yes (expanded by default) |
| **Tool Visibility** | No | Yes (shows which tool was used) |
| **SQL Execution** | No | Yes (automatic execution) |
| **Chat History** | No | Yes (full conversation tracking) |
| **Debug Mode** | No | Yes (optional API event viewing) |

---

## :material/handyman: Key Features of Day 27

### 1. Thinking Visibility 🤔

See exactly how the agent decides which tool to use:
- **Expanded by default** (immediate visibility)
- Shows first "response" event (concise thinking)
- Displayed in yellow warning box
- Can be collapsed if desired

### 2. Tool Tracking 🔧

Know which tool answered each question:
- **SalesAnalyst** for metrics queries
- **ConversationSearch** for conversation queries
- Displayed with tool type (e.g., `cortex_analyst_text_to_sql`)

### 3. Smart Output Display 📝

- **For Search queries**: Shows full response text
- **For Analyst queries**: Hides "I attempted to..." text, shows only SQL and results
- Cleaner UX focused on actionable information
- Immediate data visibility

### 4. Automatic SQL Execution 📊

When Analyst is used:
- SQL displayed in expanded code block
- **Automatically executed** (no manual button needed)
- Results rendered as dataframe immediately
- Error handling if SQL fails
- Seamless user experience

### 5. Comprehensive Sidebar 📋

Shows full agent configuration:
- Database and schema
- Agent name
- Cortex Search service details
- Cortex Analyst model details
- Debug mode toggle
- Reset chat button

---

## :material/trending_up: Best Practices

### 1. Message Display Order

Always show in this order for clarity:
1. **Tool** - Which tool was used
2. **Thinking** - Why that tool was selected (expanded by default)
3. **Output** - The answer text (only for search queries)
4. **SQL** - Generated query (for analyst queries)
5. **Results** - Dataframe (automatically executed for analyst queries)

### 2. Thinking Text Source

Extract thinking from the **first** "response" event:
- Contains concise tool selection reasoning
- Avoid the lengthy detailed reasoning from later events
- Provides clean, actionable insights

### 3. SQL Display Logic

For analyst queries:
- Hide the generic "I attempted to..." response
- Show only the SQL query
- **Automatically execute** and display results
- No manual interaction needed
- Focus on data, not status messages

### 4. Debug Mode

Provide optional debug mode:
- Off by default (clean UX)
- Shows all API events when enabled
- Helps troubleshoot issues
- Useful for development and learning

---

## :material/trending_up: Why This Architecture?

**Advantages:**
- ✅ **Full Transparency**: See thinking + tool selection (expanded by default)
- ✅ **Immediate Results**: SQL automatically executed
- ✅ **Production Ready**: Chat history, error handling, clean UI
- ✅ **Developer Friendly**: Debug mode for troubleshooting
- ✅ **Seamless UX**: No manual button clicks needed

**Use Cases:**
- Sales intelligence dashboards
- Customer support interfaces
- Business analytics chatbots
- Knowledge management systems

---

## :material/library_books: Resources

- [Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent)
- [Cortex Agents REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-rest-api)
- [Pre-Created Agent Endpoints](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run)
- [Cortex Search Service](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-service)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
