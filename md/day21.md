For today's challenge, our goal is to build a complete RAG (Retrieval-Augmented Generation) pipeline using Cortex Search. We'll retrieve relevant documents and use them as context for LLM-generated answers. The app displays a visual guide showing the three-step RAG process, then provides an interface to ask questions and see grounded answers.

> :material/warning: **Prerequisite:** You need a Cortex Search service before running this lesson. If you haven't created one yet, see **Day 19** for the setup. The service will automatically appear in the sidebar dropdown.

---

### :material/settings: How It Works: Step-by-Step

#### 1. Visual RAG Guide

```python
st.subheader(":material/menu_book: How RAG Works")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("**:material/looks_one: Retrieve**")
        st.markdown("Cortex Search finds relevant document chunks based on your question.")

with col2:
    with st.container(border=True):
        st.markdown("**:material/looks_two: Augment**")
        st.markdown("Retrieved chunks are added to the prompt as context for the LLM.")

with col3:
    with st.container(border=True):
        st.markdown("**:material/looks_3: Generate**")
        st.markdown("The LLM generates an answer grounded in the retrieved documents.")
```

* **Three-column layout**: Displays the RAG pipeline visually before users interact with the app
* **Bordered containers**: Each step is in its own container for clear separation
* **Educational context**: Helps users understand what will happen when they click "Search & Answer"

#### 2. Smart Service Selection

```python
# Default search service from Day 19
default_service = 'RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH'

# Try to get available services
try:
    services_result = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
    available_services = [f"{row['database_name']}.{row['schema_name']}.{row['name']}" 
                        for row in services_result] if services_result else []
except:
    available_services = []

# Ensure default service is always first
if default_service in available_services:
    available_services.remove(default_service)
available_services.insert(0, default_service)

# Selectbox with manual option
search_service = st.selectbox("Search Service:", options=available_services)
```

* **Explicit default**: Sets `RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH` as the default service name from Day 19
* **Auto-detection**: Queries Snowflake to find all available Cortex Search services in the account
* **Default always first**: Ensures the default service is always at position 0 (the default selection)
* **Dropdown selection**: Shows all available services in the selectbox
* **Manual entry option**: The app also allows users to enter a custom service path if needed

#### 3. Retrieval with Cortex Search

```python
from snowflake.core import Root

root = Root(session)
parts = search_service.split(".")

svc = (root
    .databases[parts[0]]
    .schemas[parts[1]]
    .cortex_search_services[parts[2]])

search_results = svc.search(
    query=question,
    columns=["CHUNK_TEXT", "FILE_NAME"],
    limit=num_chunks
)

# Extract context with metadata
context_chunks = []
sources = []
for item in search_results.results:
    context_chunks.append(item.get("CHUNK_TEXT", ""))
    sources.append(item.get("FILE_NAME", "Unknown"))

context = "\n\n---\n\n".join(context_chunks)
```

* **Dynamic service path**: Splits the service path and navigates through the Snowflake hierarchy
* **Metadata extraction**: Captures both chunk text and file names for source attribution
* **Configurable limit**: Uses the `num_chunks` slider value from the sidebar
* **Context assembly**: Joins chunks with separators to create a clear context block

#### 4. The RAG Prompt

```python
rag_prompt = f"""You are a helpful assistant. Answer based ONLY on the provided context.
If the context doesn't contain enough information, say so.

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {question}

Provide a clear, accurate answer based on the context."""
```

* **Instruction**: Tell the LLM to use only the context
* **Grounding**: Instruct to admit when info isn't available
* **Clear separation**: Context and question are clearly labeled

#### 5. Generate with Cortex LLM

```python
with st.status("Processing...", expanded=True) as status:
    st.write(":material/search: **Step 1:** Searching documents...")
    # ... search code ...
    st.write(f"   :material/check_circle: Found {len(context_chunks)} relevant chunks")
    
    st.write(":material/smart_toy: **Step 2:** Generating answer...")
    
    response_sql = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{model}',
        '{rag_prompt.replace("'", "''")}'
    ) as response
    """
    
    response = session.sql(response_sql).collect()[0][0]
    
    st.write("   :material/check_circle: Answer generated")
    status.update(label="Complete!", state="complete", expanded=True)
```

* **`st.status(...)`**: Creates an expandable status indicator that shows progress through both steps
* **`expanded=True`**: Keeps the status container open after completion so users can see what happened
* **Step-by-step feedback**: Shows "Searching documents..." then "Generating answer..." with checkmarks
* **SQL escaping**: Uses `.replace("'", "''")` to escape single quotes in the prompt (from retrieved text)
* **Model selection**: Uses the model chosen in the sidebar (claude-3-5-sonnet, mistral-large, or llama3.1-8b)

> :material/lightbulb: **Why SQL `COMPLETE` here?** For RAG applications, we use the SQL `SNOWFLAKE.CORTEX.COMPLETE()` function instead of the Python `Complete()` API. This approach works better when your prompt contains special characters from retrieved documents (easier escaping with SQL).

#### 6. Display Results with Source Attribution

```python
st.subheader(":material/lightbulb: Answer")
with st.container(border=True):
    st.markdown(response)

if show_context:
    st.subheader(":material/library_books: Retrieved Context")
    st.caption(f"Used {len(context_chunks)} chunks from customer reviews")
    for i, (chunk, source) in enumerate(zip(context_chunks, sources), 1):
        with st.expander(f":material/description: Chunk {i} - {source}"):
            st.write(chunk)
```

* **Answer display**: Shows the LLM response in a bordered container
* **Optional context viewer**: If "Show retrieved context" is checked in the sidebar, displays all chunks
* **Source attribution**: Each chunk shows its file name, so users know where the information came from
* **Expanders**: Chunks are collapsed by default to keep the interface clean

#### 7. Why RAG > Plain LLM

| Plain LLM | RAG with Cortex Search |
|-----------|----------------------|
| Uses training data | Uses YOUR documents |
| May hallucinate | Grounded in real content |
| Knowledge cutoff | Always current data |
| Generic answers | Specific to your context |

#### 8. Tuning RAG Quality

| Parameter | Effect |
|-----------|--------|
| More chunks | More context, may dilute relevance |
| Fewer chunks | More focused, might miss info |
| Better questions | Better retrieval results |
| Clear prompts | Better answer quality |

* **`num_chunks` slider**: In the sidebar, controls how many context chunks to retrieve (1-10, default 3)
* **Model selection**: Different models have different strengths (claude-3-5-sonnet for quality, llama3.1-8b for speed)
* **Show context toggle**: Helps debug by showing exactly what context was sent to the LLM

When this app runs, you'll have a working RAG system that retrieves relevant documents from Cortex Search, displays the process step-by-step, and generates grounded answers with source attribution. The visual guide at the top helps users understand the RAG pipeline before they interact with it.

---

### :material/library_books: Resources
- [Cortex Search for RAG](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Cortex Complete Function](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [RAG with Cortex Search Quickstart](https://www.snowflake.com/en/developers/guides/ask-questions-to-your-own-documents-with-snowflake-cortex-search/)
