For today's challenge, our goal is to build a complete conversational RAG chatbot that lets users chat with their documents. Unlike Day 21 (single question/answer), Day 22 maintains full conversation history, allowing follow-up questions and contextual dialogue. The app features a chat interface with message history, semantic search for each question, grounded answers using retrieved context, source attribution with expandable sources, and the ability to clear history.

> :material/warning: **Prerequisite:** You need a Cortex Search service before running this lesson. If you haven't created one yet, see **Day 19** for the setup. The service will automatically appear in the sidebar dropdown.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Initialize Conversation State

```python
import streamlit as st

st.title(":material/chat: Chat with Your Documents")
st.write("A conversational RAG chatbot powered by Cortex Search.")

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Initialize state
if "doc_messages" not in st.session_state:
    st.session_state.doc_messages = []
```

* **`st.session_state.doc_messages`**: Stores the entire conversation history (user questions and assistant responses)
* **Initialization check**: Only creates the list if it doesn't exist, preserving history across reruns
* **Persistent history**: This is the key difference from Day 21—conversation survives across interactions

#### 2. Smart Service Selection in Sidebar

```python
with st.sidebar:
    st.header(":material/settings: Settings")
    
    # Check for search service from Day 19
    default_service = st.session_state.get('search_service', 'RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH')
    
    # Try to get available services
    try:
        services_result = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
        available_services = [f"{row['database_name']}.{row['schema_name']}.{row['name']}" 
                            for row in services_result] if services_result else []
    except:
        available_services = []
    
    # Ensure default service is always first in the list
    if default_service:
        # Remove it if it exists elsewhere in the list
        if default_service in available_services:
            available_services.remove(default_service)
        # Add it at the beginning
        available_services.insert(0, default_service)
    
    # Add manual entry option
    if available_services:
        available_services.append("-- Enter manually --")
        
        search_service_option = st.selectbox(
            "Search Service:",
            options=available_services,
            index=0,
            help="Select your Cortex Search service from Day 19"
        )
        
        # If manual entry selected, show text input
        if search_service_option == "-- Enter manually --":
            search_service = st.text_input(
                "Enter service path:",
                placeholder="database.schema.service_name"
            )
        else:
            search_service = search_service_option
            
            # Show status if this is the Day 19 service
            if search_service == st.session_state.get('search_service'):
                st.caption(":material/check_circle: Using service from Day 19")
    else:
        # Fallback to text input if no services found
        search_service = st.text_input(
            "Cortex Search Service:",
            value=default_service,
            placeholder="database.schema.service_name"
        )
    
    num_chunks = st.slider("Context chunks:", 1, 5, 3,
                           help="Number of relevant chunks to retrieve per question")
    
    st.divider()
    
    if st.button(":material/delete: Clear Chat", use_container_width=True):
        st.session_state.doc_messages = []
        st.rerun()
```

* **Guaranteed default**: Ensures `RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH` is always first in the dropdown, even if other services exist
* **Duplicate prevention**: Removes the default from other positions in the list before adding it at the top
* **Auto-detection**: Automatically finds all available Cortex Search services in your account
* **Flexible input**: Offers a dropdown for available services OR manual text entry option
* **Error handling**: Gracefully falls back to text input if services can't be detected
* **Visual feedback**: Shows a checkmark when using the Day 19 service
* **Configurable chunks**: Slider controls how many document chunks to retrieve per question (1-5, default 3)
* **Clear Chat button**: Resets the conversation history and reruns the app to show a fresh state
* **`st.rerun()`**: Forces the app to refresh immediately after clearing history

#### 3. Search Function

```python
def search_documents(query, service_path, limit):
    from snowflake.core import Root
    root = Root(session)
    parts = service_path.split(".")
    
    if len(parts) != 3:
        raise ValueError("Service path must be in format: database.schema.service_name")
    
    svc = root.databases[parts[0]].schemas[parts[1]].cortex_search_services[parts[2]]
    results = svc.search(query=query, columns=["CHUNK_TEXT", "FILE_NAME"], limit=limit)
    
    chunks_data = []
    for item in results.results:
        chunks_data.append({
            "text": item.get("CHUNK_TEXT", ""),
            "source": item.get("FILE_NAME", "Unknown")
        })
    return chunks_data
```

* **Reusable function**: Encapsulates search logic for cleaner code
* **Path validation**: Ensures the service path has exactly 3 parts (database.schema.service)
* **Metadata extraction**: Returns both chunk text and file names for source attribution
* **Dictionary structure**: Each chunk is stored as `{"text": ..., "source": ...}` for easy display later

#### 4. Chat Input and Processing

```python
# Main interface
if not search_service:
    st.info(":material/arrow_back: Configure a Cortex Search service to start chatting!")
    st.caption(":material/lightbulb: **Need a search service?**\n- Complete Day 19 to create `CUSTOMER_REVIEW_SEARCH`\n- The service will automatically appear in the dropdown above")
else:
    # Display chat history
    for msg in st.session_state.doc_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your documents..."):
        st.session_state.doc_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                with st.spinner("Searching and thinking..."):
                    # Retrieve context
                    chunks_data = search_documents(prompt, search_service, num_chunks)
                    context = "\n\n---\n\n".join([c["text"] for c in chunks_data])
                    
                    # Generate response with guardrails
                    rag_prompt = f"""You are a customer review analysis assistant. Your role is to ONLY answer questions about customer reviews and feedback.

STRICT GUIDELINES:
1. ONLY use information from the provided customer review context below
2. If asked about topics unrelated to customer reviews (e.g., general knowledge, coding, math, news), respond: "I can only answer questions about customer reviews. Please ask about product feedback, customer experiences, or review insights."
3. If the context doesn't contain relevant information, say: "I don't have enough information in the customer reviews to answer that."
4. Stay focused on: product features, customer satisfaction, complaints, praise, quality, pricing, shipping, or customer service mentioned in reviews
5. Do NOT make up information or use knowledge outside the provided reviews

CONTEXT FROM CUSTOMER REVIEWS:
{context}

USER QUESTION: {prompt}

Provide a clear, helpful answer based ONLY on the customer reviews above. If you cite information, mention it naturally."""
                    
                    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', '{rag_prompt.replace(chr(39), chr(39)+chr(39))}')"
                    response = session.sql(sql).collect()[0][0]
                
                st.markdown(response)
                
                # Show sources with file names
                with st.expander(f":material/library_books: Sources ({len(chunks_data)} reviews used)"):
                    for i, chunk_info in enumerate(chunks_data, 1):
                        st.caption(f"**[{i}] {chunk_info['source']}**")
                        st.write(chunk_info['text'][:200] + "..." if len(chunk_info['text']) > 200 else chunk_info['text'])
                
                st.session_state.doc_messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info(":material/lightbulb: **Troubleshooting:**\n- Make sure the search service exists (check Day 19)\n- Verify the service has finished indexing\n- Check your permissions")
```

* **Service validation**: Checks if a search service is configured before showing chat interface
* **Helpful guidance**: Shows instructional message if no service is selected
* **`:=` walrus operator**: Assigns `prompt` and checks if it's truthy (user pressed Enter) in one line
* **`st.chat_input(...)`**: Fixed input bar at the bottom of the app (better UX than `st.text_input`)
* **Immediate display**: Shows user message right away, then assistant message appears below
* **`st.spinner(...)`**: Shows loading indicator while searching and generating
* **Guardrails in system prompt**: Prevents the LLM from answering off-topic questions (general knowledge, coding, math, etc.)
* **Strict scope enforcement**: Defines the assistant as a "customer review analysis assistant" with explicit boundaries
* **Grounding enforcement**: Multiple instructions to use ONLY the provided context and not hallucinate
* **Graceful rejection**: Politely redirects users when they ask questions outside the review domain
* **String escaping**: Uses `chr(39)` to handle single quotes in retrieved text (avoids SQL injection)
* **Error handling**: Catches exceptions and provides helpful troubleshooting tips
* **Source display**: Shows expandable sources immediately after the response
* **Append to history**: Stores both user question and assistant response for the next rerun

#### 5. Guardrails: Keeping Conversations on Topic

One critical enhancement in this chatbot is the implementation of **guardrails** in the system prompt. These prevent the LLM from answering questions outside the scope of customer reviews:

**What Guardrails Prevent:**
- ❌ General knowledge questions ("What's the capital of France?")
- ❌ Coding requests ("Write me Python code")
- ❌ Math problems ("What's 47 × 83?")
- ❌ Current events ("What's the latest news?")
- ❌ Any topic unrelated to customer reviews

**Example Interactions:**

```
User: "What do customers say about the helmets?"
✅ Valid question → Returns review insights

User: "Write me Python code to sort a list"
❌ Off-topic → "I can only answer questions about customer reviews. Please ask about product feedback, customer experiences, or review insights."

User: "What's 2+2?"
❌ Off-topic → Politely redirects to review-related questions
```

**Why This Matters:**
- **Prevents scope creep**: Keeps the chatbot focused on its intended purpose
- **Avoids hallucinations**: LLM can't make up answers outside the provided context
- **Better user experience**: Users understand the chatbot's capabilities and limitations
- **Trust and reliability**: Answers are always grounded in actual customer review data

The guardrails work through explicit instructions in the system prompt that define acceptable topics (product features, satisfaction, complaints, quality, etc.) and provide a standard rejection message for off-topic queries.

#### 6. Day 21 vs Day 22: Key Differences

| Feature | Day 21 (Single-turn RAG) | Day 22 (Conversational RAG) |
|---------|--------------------------|------------------------------|
| **History** | No history | Full conversation stored |
| **Interface** | Button + text input | Chat interface with `st.chat_input` |
| **Follow-ups** | Each question is independent | Can reference previous exchanges |
| **Use case** | One-off questions | Multi-turn conversations |
| **Complexity** | Simpler | More stateful |

#### 7. Example Conversation Flow

```
User: "What do customers say about thermal gloves?"
Assistant: [Searches reviews → Retrieves 3 chunks → Generates answer]
"Customers generally praise the thermal gloves for warmth..."

User: "Are there any complaints?"
Assistant: [Searches again → Can reference previous context]
"Yes, some customers mentioned durability issues after extended use..."

User: "Which products get the best reviews?"
Assistant: [New search → Provides answer]
"Based on the reviews, the helmets receive the highest ratings..."
```

* **Each question triggers a new search**: Unlike some conversational systems, this app searches for every question (not just the first)
* **Independent retrieval**: Ensures answers are always grounded in the most relevant documents for each specific question
* **History persists**: Users can scroll up to review the entire conversation

When this app runs, you'll have a fully functional conversational document Q&A chatbot that retrieves relevant information from Cortex Search, maintains conversation history, and generates grounded answers with source attribution. This completes Week 3's RAG pipeline journey—from document extraction (Day 16) to chunking (Day 17) to embeddings (Day 18) to search service creation (Day 19) to querying (Day 20) to single-turn RAG (Day 21) to this complete conversational chatbot (Day 22).

---

### :material/library_books: Resources
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Build Conversational Apps](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
- [Snowflake Cortex LLMs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
