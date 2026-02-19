For today's challenge, we'll build our first **Cortex Agent** using both **Cortex Search** (for conversations) and **Cortex Analyst** (for metrics). Unlike manual RAG systems where you write code for every step, Cortex Agents autonomously plan, select tools, and execute tasks to answer questions.

---

### :material/info: What are Cortex Agents?

**Cortex Agents** are AI-powered assistants that can autonomously use tools to complete tasks. Think of them as having:
- :material/psychology: **Planning** - Agent analyzes the question
- :material/handyman: **Tool Selection** - Agent chooses the right tool(s)
- :material/bolt: **Execution** - Agent runs tools and synthesizes answers

**Key Difference from Manual RAG:**
- **Manual RAG (Day 19)**: You write code to search → format → prompt → generate
- **Cortex Agents (Day 26)**: Agent autonomously decides how to answer using available tools

**Today's Focus:** Multi-tool agent using **Cortex Search** on sales conversations and **Cortex Analyst** on sales metrics.

---

### :material/settings: How It Works: Step-by-Step

### 1. Create Sales Conversations Data

First, we need unstructured text data for the agent to search through:

```sql
CREATE TABLE SALES_CONVERSATIONS (
    conversation_id VARCHAR,
    transcript_text TEXT,
    customer_name VARCHAR,
    deal_stage VARCHAR,
    sales_rep VARCHAR,
    conversation_date TIMESTAMP,
    deal_value FLOAT,
    product_line VARCHAR
);
```

This table stores transcripts from 10 comprehensive sales calls with various customers.

### 2. Create Cortex Search Service

Enable semantic search on the conversation transcripts:

```sql
CREATE CORTEX SEARCH SERVICE SALES_CONVERSATION_SEARCH
  ON transcript_text
  ATTRIBUTES customer_name, deal_stage, sales_rep
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT transcript_text, customer_name, deal_stage, sales_rep, conversation_date
    FROM SALES_CONVERSATIONS
    WHERE conversation_date >= '2024-01-01'
  );
```

This creates a search index that the agent can use as a tool.

### 3. Create Sales Metrics Table

For structured data analysis:

```sql
CREATE TABLE SALES_METRICS (
    deal_id VARCHAR,
    customer_name VARCHAR,
    deal_value FLOAT,
    close_date DATE,
    sales_stage VARCHAR,
    win_status BOOLEAN,
    sales_rep VARCHAR,
    product_line VARCHAR
);
```

This table contains 10 deals with metrics like deal values, win/loss status, and sales reps.

### 4. Upload Semantic Model YAML

Create a semantic model that tells Cortex Analyst how to interpret the database schema:

```yaml
name: sales_metrics
description: Sales metrics and analytics model
tables:
  - name: SALES_METRICS
    base_table:
      database: CHANINN_SALES_INTELLIGENCE
      schema: DATA
      table: SALES_METRICS
    dimensions:
      - name: CUSTOMER_NAME
        expr: CUSTOMER_NAME
        data_type: VARCHAR(16777216)
        sample_values: [TechCorp Inc, SmallBiz Solutions, SecureBank Ltd]
        synonyms: [client, buyer, purchaser]
    measures:
      - name: DEAL_VALUE
        expr: DEAL_VALUE
        data_type: FLOAT
        sample_values: ['75000', '25000', '150000']
        synonyms: [revenue, sale_amount, transaction_value]
```

Upload this to `@CHANINN_SALES_INTELLIGENCE.DATA.MODELS/sales_metrics_model.yaml`

### 5. Create the Multi-Tool Cortex Agent

Now we define an agent that can use both tools:

```sql
CREATE OR REPLACE AGENT SALES_CONVERSATION_AGENT
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: 'Provide clear, concise answers based on the available data. Do not hallucinate or answer off-topic questions.'
    orchestration: 'For questions about sales metrics (totals, averages, counts, deals, reps, products, win/loss), use the SalesAnalyst tool. For questions about sales conversation transcripts (summaries, concerns, discussions), use the ConversationSearch tool. Decline questions outside this scope.'
    system: 'You are a Sales Intelligence Assistant. Your purpose is to analyze sales metrics and conversation transcripts. Only answer questions about sales data. Decline questions about weather, coding, general knowledge, or anything outside the sales domain.'
  tools:
    - tool_spec:
        type: "cortex_search"
        name: "ConversationSearch"
        description: "Searches sales conversation transcripts"
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "SalesAnalyst"
        description: "Generates and executes SQL queries on sales metrics data"
  tool_resources:
    ConversationSearch:
      name: "CHANINN_SALES_INTELLIGENCE.DATA.SALES_CONVERSATION_SEARCH"
      max_results: "5"
    SalesAnalyst:
      semantic_model_file: "@chaninn_sales_intelligence.data.models/sales_metrics_model.yaml"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
        query_timeout: 60
  $$;
```

**Key Components:**
- **`models.orchestration`**: Claude Sonnet 4.5 for intelligent tool routing
- **`instructions.response`**: How the agent should format responses
- **`instructions.orchestration`**: Rules for tool selection
- **`instructions.system`**: The agent's persona and boundaries
- **`tools`**: Two tools - ConversationSearch (Cortex Search) and SalesAnalyst (Cortex Analyst)
- **`tool_resources`**: Configuration for each tool
- **`execution_environment`**: Enables server-side SQL execution for the analyst

### 6. Display in Streamlit

The app provides two main tabs:

**Data Setup Tab**:
- Step 1: Create database and schema (`CHANINN_SALES_INTELLIGENCE.DATA`)
- Step 2: Create sales conversations table with 10 comprehensive transcripts
- Step 3: Create Cortex Search service (optimized to skip if exists)
- Step 4: Create sales metrics table with 10 deals
- Step 5: Upload semantic model YAML with auto-upload feature
- Step 6: Verify complete setup

**Create Agent Tab**:
- View agent specification SQL with both tools
- Create the multi-tool agent with one click
- Agent uses orchestration to decide between Cortex Search and Cortex Analyst

**What Happens:**
1. Agent receives your question
2. Agent decides which tool to use (ConversationSearch or SalesAnalyst)
3. Agent calls the appropriate tool
4. Agent synthesizes an answer with citations

---

## :material/psychology: How Agents Plan

### Example 1: Metrics Question → SalesAnalyst

When you ask *"What was the total sales volume?"*, the agent:

1. **Analyzes** the question (needs numerical aggregation)
2. **Selects** SalesAnalyst tool
3. **Generates** SQL query
4. **Returns** answer (without the "I attempted to..." text)
5. **Shows** SQL for manual execution

### Example 2: Conversation Question → ConversationSearch

When you ask *"What concerns did TechCorp Inc raise?"*, the agent:

1. **Analyzes** the question (needs conversation search)
2. **Selects** ConversationSearch tool
3. **Retrieves** top 5 relevant conversation snippets
4. **Synthesizes** an answer citing the found information
5. **Returns** response with details

All of this happens automatically without manual code!

---

## :material/handyman: Agent Tools Overview

Cortex Agents in Day 26 support two tool types:

- **`cortex_search`**: Semantic search on unstructured conversation text
- **`cortex_analyst_text_to_sql`**: Generate and execute SQL queries on structured metrics

In Day 27, we'll see this agent in action with a full chat interface!

---

## :material/trending_up: Why Use Multi-Tool Agents?

**Advantages:**
- ✅ **Less Code**: No manual RAG pipeline or tool selection logic
- ✅ **Autonomous**: Agent decides which tool to use
- ✅ **Comprehensive**: Access to both structured and unstructured data
- ✅ **Extensible**: Easy to add more tools
- ✅ **Explainable**: Agent shows its reasoning process

**Use Cases:**
- Sales intelligence (metrics + conversations)
- Customer support chatbots
- Knowledge base Q&A with analytics
- Document search and data analysis

---

## :material/library_books: Resources

- [Cortex Agents Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Agents REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-rest-api)
- [Agent Run API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)

---

## :material/rocket: Next Steps

- **Day 27**: Build a chat interface for the multi-tool agent with full orchestration visibility
- Try asking both metrics and conversation questions
- Experiment with different instruction styles
- Add debug mode to see the agent's thinking process
