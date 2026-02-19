# Day 27
# Multi-Tool Agent Orchestration

import json
import streamlit as st

# Environment detection and connection setup
IS_SIS = False
try:
    from snowflake.snowpark.context import get_active_session
    import _snowflake
    session = get_active_session()
    IS_SIS = True
except:
    import requests
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()
    conn = session._conn._conn
    HOST, TOKEN = conn.host, conn.rest.token

# Config
DB_NAME = "CHANINN_SALES_INTELLIGENCE"
SCHEMA_NAME = "DATA"
AGENT_NAME = "SALES_CONVERSATION_AGENT"
AGENT_ENDPOINT = f"/api/v2/databases/{DB_NAME}/schemas/{SCHEMA_NAME}/agents/{AGENT_NAME}:run"

def run_sql(sql):
    """Execute SQL and return dataframe."""
    try:
        return session.sql(sql.replace(';', '')).to_pandas()
    except Exception as e:
        st.error(f"SQL Error: {e}")
        return None

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
        "table_data": None,
        "events": []
    }
    
    try:
        if IS_SIS:
            resp = _snowflake.send_snow_api_request("POST", AGENT_ENDPOINT, {}, {}, payload, None, 60000)
            content = resp.get("content", "") if isinstance(resp, dict) else str(resp)
            
            if resp.get("status", 200) >= 400:
                result["text"] = f":material/error: API Error: {content}"
                return result
            
            events = json.loads(content)
            result["events"] = events
            
            for event in events:
                event_type = event.get("event", "")
                data = event.get("data", {})
                
                # Parse response event with thinking - capture first occurrence only
                if event_type == "response" and not result["thinking"]:
                    content_list = data.get("content", [])
                    for content_item in content_list:
                        # Extract thinking text from first response event
                        if "thinking" in content_item and not result["thinking"]:
                            thinking_obj = content_item.get("thinking", {})
                            if isinstance(thinking_obj, dict):
                                result["thinking"] = thinking_obj.get("text", "")
                            elif isinstance(thinking_obj, str):
                                result["thinking"] = thinking_obj
                            break  # Stop after finding first thinking
                
                # Parse text response
                if event_type == "response.text.delta":
                    result["text"] += data.get("text", "")
                elif event_type == "response.text":
                    text_obj = data.get("text", {})
                    if isinstance(text_obj, dict):
                        result["text"] = text_obj.get("text", "")
                    else:
                        result["text"] = str(text_obj)
                
                # Parse tool usage - capture which tool is being used
                elif event_type == "response.tool_use":
                    result["tool_name"] = data.get("name")
                    result["tool_type"] = data.get("type")
                    # For cortex_analyst, get SQL from input
                    if data.get("type") == "cortex_analyst_text_to_sql":
                        tool_input = data.get("input", {})
                        result["sql"] = tool_input.get("sql")
                
                # Parse tool result - for table data
                elif event_type == "response.tool_result":
                    content_list = data.get("content", [])
                    for content_item in content_list:
                        if content_item.get("type") == "json":
                            json_data = content_item.get("json", {})
                            # Extract SQL if available
                            if "sql" in json_data:
                                result["sql"] = json_data["sql"]
                            # Extract result_set if available
                            if "result_set" in json_data:
                                result["table_data"] = json_data["result_set"]
                
                # Parse table data
                elif event_type == "response.table":
                    result_set = data.get("result_set", {})
                    if result_set and result_set.get("data"):
                        result["table_data"] = result_set
                
                # Handle errors
                elif event_type == "error":
                    error_details = data.get("error", {})
                    result["text"] += f"\n\n:material/error: Error: {error_details.get('message', 'Unknown error')}"
        
        else:
            # External environment
            resp = requests.post(
                f"https://{HOST}{AGENT_ENDPOINT}",
                json=payload,
                stream=True,
                headers={
                    "Authorization": f'Snowflake Token="{TOKEN}"',
                    "Content-Type": "application/json"
                }
            )
            
            if resp.status_code >= 400:
                result["text"] = f":material/error: API Error: {resp.text}"
                return result
            
            for line in resp.iter_lines():
                if line and line.decode('utf-8').startswith('data: '):
                    data_str = line.decode('utf-8')[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        event = json.loads(data_str)
                        result["events"].append(event)
                        
                        event_type = event.get('event', '')
                        data = event.get('data', {})
                        
                        # Parse response event with thinking - capture first occurrence only
                        if event_type == "response" and not result["thinking"]:
                            content_list = data.get("content", [])
                            for content_item in content_list:
                                if "thinking" in content_item and not result["thinking"]:
                                    thinking_obj = content_item.get("thinking", {})
                                    if isinstance(thinking_obj, dict):
                                        result["thinking"] = thinking_obj.get("text", "")
                                    elif isinstance(thinking_obj, str):
                                        result["thinking"] = thinking_obj
                                    break  # Stop after finding first thinking
                        
                        if event_type == "response.text.delta":
                            result["text"] += data.get("text", "")
                        elif event_type == "response.tool_use":
                            result["tool_name"] = data.get("name")
                            result["tool_type"] = data.get("type")
                            if data.get("type") == "cortex_analyst_text_to_sql":
                                result["sql"] = data.get("input", {}).get("sql")
                        elif event_type == "response.tool_result":
                            content_list = data.get("content", [])
                            for content_item in content_list:
                                if content_item.get("type") == "json":
                                    json_data = content_item.get("json", {})
                                    if "sql" in json_data:
                                        result["sql"] = json_data["sql"]
                                    if "result_set" in json_data:
                                        result["table_data"] = json_data["result_set"]
                        elif event_type == "response.table":
                            result_set = data.get("result_set", {})
                            if result_set and result_set.get("data"):
                                result["table_data"] = result_set
                    except:
                        pass
        
        return result
        
    except Exception as e:
        import traceback
        result["text"] = f":material/error: Exception: {str(e)}"
        result["events"].append({"error": str(e), "traceback": traceback.format_exc()})
        return result

# Example questions
METRICS_QS = ["What was the total sales volume?", "What is the average deal value?",
              "How many deals were closed?", "Which sales rep has the most closed deals?",
              "Show me deals by product line", "What is the win rate?"]
CONVO_QS = ["Summarize the call with TechCorp Inc", "What concerns did TechCorp Inc raise?",
            "Tell me about the SmallBiz Solutions conversation", "What was discussed with DataDriven Co?",
            "Summarize the LegalEase Corp discussion"]

# Sidebar
with st.sidebar:
    st.header(":material/settings: Configuration")
    st.text_input("Database:", DB_NAME, disabled=True)
    st.text_input("Schema:", SCHEMA_NAME, disabled=True)
    st.text_input("Agent:", AGENT_NAME, disabled=True)
    
    st.divider()
    
    st.subheader(":material/search: Cortex Search")
    st.text_input("Service Name:", "SALES_CONVERSATION_SEARCH", disabled=True, key="search_service")
    st.text_input("Database.Schema:", f"{DB_NAME}.{SCHEMA_NAME}", disabled=True, key="search_db")
    
    st.divider()
    
    st.subheader(":material/query_stats: Cortex Analyst")
    st.text_input("Model File:", "sales_metrics_model.yaml", disabled=True, key="analyst_model")
    st.text_input("Stage:", "MODELS", disabled=True, key="analyst_stage")
    st.text_input("Database.Schema:", f"{DB_NAME}.{SCHEMA_NAME}", disabled=True, key="analyst_db")
    
    st.divider()
    debug_mode = st.checkbox("🐛 Debug Mode (show API events)", value=False)
    
    if st.button(":material/refresh: Reset Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("Day 27: Multi-Tool Agent Orchestration")

# Main
st.title(":material/construction: Multi-Tool Agent Orchestration")
st.write("The agent uses **orchestration** to automatically choose between Cortex Search (conversations) and Cortex Analyst (metrics).")

# Check if agent exists
try:
    agents = session.sql(f'SHOW AGENTS IN SCHEMA "{DB_NAME}"."{SCHEMA_NAME}"').collect()
    agent_names = [row['name'] for row in agents]
    
    if AGENT_NAME in agent_names:
        st.success(f"✅ Connected to agent: **{AGENT_NAME}**", icon=":material/check_circle:")
    else:
        st.error(f"❌ Agent '{AGENT_NAME}' not found!", icon=":material/error:")
        st.warning("Go to Day 26 and create the agent first.")
        st.stop()
except Exception as e:
    st.error(f"Cannot verify agent: {e}")
    st.stop()

# Check data
try:
    convo_count = session.sql(f'SELECT COUNT(*) as cnt FROM "{DB_NAME}"."{SCHEMA_NAME}".SALES_CONVERSATIONS').collect()[0]['CNT']
    metrics_count = session.sql(f'SELECT COUNT(*) as cnt FROM "{DB_NAME}"."{SCHEMA_NAME}".SALES_METRICS').collect()[0]['CNT']
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"💬 Conversations: **{convo_count}** records" if convo_count > 0 else "⚠️ No conversation data")
    with col2:
        if metrics_count > 0:
            st.info(f"📊 Metrics: **{metrics_count}** records")
        else:
            st.error("❌ SALES_METRICS is empty! Run Step 4 in Day 26")
except:
    pass

st.session_state.setdefault("messages", [])

# Example questions
with st.container(border=True):
    st.markdown("### :material/help: Example Questions")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**:material/query_stats: Sales Metrics** (uses SalesAnalyst)")
        if (q := st.selectbox("", ["Select a question..."] + METRICS_QS, key="m", label_visibility="collapsed")) != "Select a question...":
            if st.button(":material/send: Ask", key="am", use_container_width=True):
                st.session_state.pending = q
                st.rerun()
    with col2:
        st.markdown("**:material/forum: Conversations** (uses ConversationSearch)")
        if (q := st.selectbox("", ["Select a question..."] + CONVO_QS, key="c", label_visibility="collapsed")) != "Select a question...":
            if st.button(":material/send: Ask", key="ac", use_container_width=True):
                st.session_state.pending = q
                st.rerun()

# Display history
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg['role']):
        if msg['role'] == 'assistant':
            # 1. Show which tool was used (FIRST)
            if msg.get('tool_name') and msg.get('tool_type'):
                st.caption(f":material/build: Tool: **{msg['tool_name']}** (`{msg['tool_type']}`)")
            
        # 2. Show thinking if available (SECOND)
        if msg.get('thinking'):
            with st.expander("🤔 Agent Thinking Process", expanded=False):
                st.warning(msg['thinking'])
        
        # 3. Show text response (skip if SQL exists - we'll just show results)
        if not msg.get('sql'):
            st.markdown(msg['content'])
        
        # 4. Show SQL and table data if available (for analyst queries)
        if msg.get('sql'):
            with st.expander(":material/query_stats: Generated SQL", expanded=True):
                st.code(msg['sql'], language="sql")
        
        # 5. Execute SQL directly if we have it
        if msg.get('sql'):
            try:
                df = session.sql(msg['sql']).to_pandas()
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {e}")
        
        # Debug: show events if enabled
        if debug_mode and msg.get('events'):
            with st.expander(f"🐛 Debug: {len(msg['events'])} API Events"):
                for idx, evt in enumerate(msg['events'], 1):
                    st.write(f"**Event #{idx}:** `{evt.get('event', 'unknown')}`")
                    st.json(evt)

# Handle input
user_input = st.session_state.pop('pending', None) or st.chat_input("Ask a question about sales data...")

if user_input:
    # Add user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            result = call_agent(user_input)
        
        # Build message dict
        msg = {
            "role": "assistant",
            "content": result["text"],
            "thinking": result["thinking"],
            "tool_name": result["tool_name"],
            "tool_type": result["tool_type"],
            "sql": result["sql"],
            "table_data": result["table_data"],
            "events": result["events"] if debug_mode else []
        }
        
        # 1. Show which tool was used (FIRST)
        if result["tool_name"] and result["tool_type"]:
            st.caption(f":material/build: Tool: **{result['tool_name']}** (`{result['tool_type']}`)")
        
        # 2. Show thinking if available (SECOND)
        if result["thinking"]:
            with st.expander("🤔 Agent Thinking Process", expanded=True):
                st.warning(result["thinking"])
        
        # 3. Show text response (skip if SQL exists - we'll just show results)
        if not result["sql"]:
            st.markdown(result["text"])
        
        # 4. Show SQL if available
        if result["sql"]:
            with st.expander(":material/query_stats: Generated SQL", expanded=True):
                st.code(result["sql"], language="sql")
        
        # 5. Execute SQL directly if we have it
        if result["sql"]:
            try:
                df = session.sql(result["sql"]).to_pandas()
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {e}")
        

        
        # Debug events
        if debug_mode and result["events"]:
            with st.expander(f"🐛 Debug: {len(result['events'])} API Events"):
                for idx, evt in enumerate(result["events"], 1):
                    st.write(f"**Event #{idx}:** `{evt.get('event', 'unknown')}`")
                    st.json(evt)
        
        st.session_state.messages.append(msg)

st.divider()
st.caption("Day 27: Multi-Tool Agent Orchestration | Chat with Sales Data | 30 Days of AI with Streamlit")
