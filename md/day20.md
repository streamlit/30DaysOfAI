For today's challenge, our goal is to query the Cortex Search service you created in Day 19 to find relevant customer reviews. We need to use the Python SDK to perform semantic searches, retrieve relevant documents based on meaning (not just keywords), and display the results in a clean interface. Once that's done, we will have a working document search that understands natural language queries.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Import Libraries and Establish Connection

```python
import streamlit as st
from snowflake.core import Root

st.title(":material/search: Querying Cortex Search")
st.write("Search and retrieve relevant text chunks using Cortex Search Service.")

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

* **`from snowflake.core import Root`**: Imports the Python API for accessing Cortex Search services. This is cleaner than using SQL strings.
* **`st.title(...)`**: Sets the page title with an emoji icon for visual appeal.
* **`try/except` block**: Automatically detects the environment and connects appropriately (SiS vs local/Community Cloud)
* **`session`**: The established Snowflake connection that we'll use to query the search service.

#### 2. Input Container: Service Configuration

```python
with st.container(border=True):
    st.subheader(":material/search: Search Configuration and Query")
    
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
```

* **Bordered container**: Groups all input elements together for better organization.
* **`default_service`**: Explicitly sets `RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH` as the default service name from Day 19.
* **`SHOW CORTEX SEARCH SERVICES`**: Queries Snowflake to list all available search services in your account.
* **List comprehension**: Builds a list of service paths in the format `database.schema.service_name` for each service found.
* **Ensure default first**: Removes the default service if it's in the list, then inserts it at position 0 so it's always the first option.
* **Try/except**: If the query fails (no services exist), sets an empty list.

#### 3. Smart Service Selection

```python
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
            st.success(":material/check_circle: Using service from Day 19")
else:
    # Fallback to text input if no services found
    search_service = st.text_input(
        "Search Service:",
        value=default_service,
        placeholder="database.schema.service_name",
        help="Full path to your Cortex Search service"
    )

st.code(search_service, language="sql")
st.caption(":material/lightbulb: This should point to your CUSTOMER_REVIEW_SEARCH service from Day 19")
```

* **Selectbox with manual option**: If services are found, creates a dropdown menu. Adds "-- Enter manually --" as the last option for custom paths.
* **`index=0`**: Sets the first service (the default `RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH`) as the default selection.
* **`help` parameter**: Adds a tooltip explaining this should be the service from Day 19.
* **Conditional input**: If "Enter manually" is selected, shows a text input box. Otherwise, uses the selected service.
* **Status indicator**: If the selected service matches Day 19's service stored in session state, shows a green success message.
* **Fallback**: If no services are found, shows only a text input with the default path pre-filled.
* **`st.code(...)`**: Displays the full service path in a code block for clarity.
* **Caption**: Reminds users this should point to their `CUSTOMER_REVIEW_SEARCH` service.

#### 4. Search Query Input

```python
st.divider()

# Search query input
query = st.text_input(
    "Enter your search query:",
    value="warm thermal gloves",
    placeholder="e.g., durability issues, comfortable helmet"
)

num_results = st.slider("Number of results:", 1, 20, 5)

search_clicked = st.button(":material/search: Search", type="primary", use_container_width=True)
```

* **`st.divider()`**: Creates a visual separator between service configuration and query input sections.
* **Text input**: Creates a search box with a default query ("warm thermal gloves") to show users what kind of input to provide.
* **`placeholder`**: Shows example queries when the input is empty, giving users ideas for what to search.
* **Slider**: Lets users control how many results to return (1-20, default is 5).
* **Search button**: Full-width primary button that triggers the search. We store the click state in `search_clicked` for use in the output container.

#### 5. Output Container: Initialize and Check Button Click

```python
with st.container(border=True):
    st.subheader(":material/analytics: Search Results")
    
    if search_clicked:
        if query and search_service:
            try:
                root = Root(session)
                parts = search_service.split(".")
                
                if len(parts) != 3:
                    st.error("Service path must be in format: database.schema.service_name")
```

* **Separate bordered container**: The output is in its own container, visually distinct from the input.
* **`if search_clicked:`**: Only executes search logic when the button is clicked.
* **`if query and search_service:`**: Validates that both required fields are filled.
* **`Root(session)`**: Creates the entry point for the Python API.
* **`.split(".")`**: Breaks the full path into database, schema, and service name.
* **Validation**: Checks that the path has exactly 3 parts.

#### 6. Execute Semantic Search

```python
if len(parts) != 3:
    st.error("Service path must be in format: database.schema.service_name")
else:
    svc = (root
        .databases[parts[0]]
        .schemas[parts[1]]
        .cortex_search_services[parts[2]])
    
    with st.spinner("Searching..."):
        results = svc.search(
            query=query,
            columns=["CHUNK_TEXT", "FILE_NAME", "CHUNK_TYPE", "CHUNK_ID"],
            limit=num_results
        )
    
    st.success(f":material/check_circle: Found {len(results.results)} result(s)!")
```

* **Dictionary-style navigation**: Uses `[parts[0]]`, `[parts[1]]`, `[parts[2]]` to navigate through the Snowflake hierarchy.
* **`else` block**: Only executes the search if the path validation passes.
* **`svc.search(...)`**: This is the core search call using the Python API.
* **`query`**: The natural language search query from the user.
* **`columns`**: Specifies which fields to return (chunk text, file name, chunk type, chunk ID).
* **`limit`**: Maximum number of results, controlled by the slider.
* **`st.spinner(...)`**: Shows an animated loading indicator while the search executes.
* **Success message**: Shows how many results were found.

#### 7. Display Search Results

```python
# Display results
for i, item in enumerate(results.results, 1):
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**Result {i}** - {item.get('FILE_NAME', 'N/A')}")
        with col2:
            st.caption(f"Type: {item.get('CHUNK_TYPE', 'N/A')}")
        with col3:
            st.caption(f"Chunk: {item.get('CHUNK_ID', 'N/A')}")
        
        st.write(item.get("CHUNK_TEXT", "No text found"))
        
        # Show relevance score if available
        if hasattr(item, 'score') or 'score' in item:
            score = item.get('score', item.score if hasattr(item, 'score') else None)
            if score is not None:
                st.caption(f"Relevance Score: {score:.4f}")
```

* **`enumerate(results.results, 1)`**: Loops through results starting the counter at 1, giving us "Result 1", "Result 2", etc.
* **Bordered container**: Each result is displayed in its own container with a visible border.
* **Three-column layout**: First column (width 2) shows result number and file name. Second and third columns (width 1 each) show chunk type and ID.
* **`.get('FILE_NAME', 'N/A')`**: Safely retrieves values. If the field doesn't exist, shows "N/A".
* **Full text display**: Shows the complete chunk text below the metadata.
* **Relevance score**: If available, displays the semantic similarity score (lower distance = higher relevance).
* **Automatic ranking**: Results are ordered by relevance (most similar to the query appears first).

#### 8. Error Handling and Empty States

```python
except Exception as e:
    st.error(f"Error: {str(e)}")
    st.info(":material/lightbulb: **Troubleshooting:**\n- Make sure the search service exists (check Day 19)\n- Verify the service has finished indexing\n- Check that you have access permissions")
else:
    st.warning(":material/warning: Please enter a query and configure a search service.")
    st.info(":material/lightbulb: **Need a search service?**\n- Complete Day 19 to create `CUSTOMER_REVIEW_SEARCH`\n- The service will automatically appear in the dropdown above")
else:
    st.info(":material/arrow_upward: Configure your search service and enter a query above, then click Search to see results.")
```

* **Exception handling**: Catches any errors during the search process and displays them.
* **Troubleshooting tips**: Provides helpful guidance for common issues (service doesn't exist, indexing incomplete, permission issues).
* **Warning message**: Shown if query or service is missing, reminding users to configure both.
* **Helpful info**: Points users to Day 19 to create the required search service.
* **Empty state**: When no search has been performed yet, shows a helpful message pointing users to the input container.

When this code runs, you will have a semantic search interface that can find relevant customer reviews based on natural language queries. Try searching for "durability problems" to see it find reviews mentioning "broke after 2 weeks" and "lasted 3 seasons" even though they don't use the exact words you searched for.

---

### :material/library_books: Resources
- [Cortex Search Python SDK](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search#querying-a-cortex-search-service)
- [Python API: snowflake.core](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/api/snowflake.core)
- [Semantic Search Guide](https://www.snowflake.com/en/developers/guides/ask-questions-to-your-own-documents-with-snowflake-cortex-search/)
