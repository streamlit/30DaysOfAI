For today's challenge, our goal is to create a semantic search service for customer reviews using Snowflake Cortex Search. Cortex Search is Snowflake's managed semantic search service that understands meaning (not just keywords), automatically indexes your data, stays in sync with your tables, and inherits Snowflake security and governance. We'll configure the database settings, create a searchable view, build the Cortex Search service, and verify it exists. Once complete, we'll have a working search service ready to query in Day 20.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Database Configuration and Session State

```python
import streamlit as st
from snowflake.core import Root
import pandas as pd

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Initialize session state for database configuration
if 'day19_database' not in st.session_state:
    if 'embeddings_database' in st.session_state:
        st.session_state.day19_database = st.session_state.embeddings_database
        st.session_state.day19_schema = st.session_state.embeddings_schema
    else:
        st.session_state.day19_database = "RAG_DB"
        st.session_state.day19_schema = "RAG_SCHEMA"

# Database Configuration UI
with st.container(border=True):
    st.subheader(":material/analytics: Database Configuration")
    
    database = st.text_input("Database", value=st.session_state.day19_database)
    schema = st.text_input("Schema", value=st.session_state.day19_schema)
    table_name = st.text_input("Source Table", value="REVIEW_CHUNKS")
```

* **Auto-detection**: Automatically detects the database and schema from Day 18's embeddings if available
* **Fallback defaults**: Uses `RAG_DB.RAG_SCHEMA` if Day 18 data isn't found
* **Session state persistence**: Stores configuration for use across the app
* **Bordered container**: Groups database configuration inputs in a clean, organized interface
* **Source table**: Expects `REVIEW_CHUNKS` table from Day 17 with chunk text and metadata

#### 2. What is Cortex Search?

**Cortex Search** is Snowflake's managed semantic search service that:

- :material/psychology: **Understands meaning**, not just keywords
- :material/flash_on: **Automatically indexes** your data
- :material/sync: **Stays in sync** with your tables
- 🔐 **Inherits Snowflake security** and governance

**For Customer Reviews:**
- Search "warm gloves" → finds reviews mentioning "toasty hands", "cold fingers"
- Search "durability issues" → finds "broke after 2 weeks", "lasted 3 seasons"
- Search "comfortable helmet" → finds "all-day wear", "no pressure points"

**Why use Cortex Search over manual approaches?**

| Manual Approach | Cortex Search |
|-----------------|---------------|
| You generate embeddings | :material/check_circle: Already done in Day 18 |
| Manual indexing | :material/check_circle: Automatic indexing |
| Manual sync | :material/check_circle: Auto-refresh |
| Build similarity search | :material/check_circle: Built-in semantic search |
| Manage infrastructure | :material/check_circle: Fully managed |

#### 3. Create the Search View

```python
if st.button(":material/build: Create Search View", type="primary"):
    create_view_sql = f"""
    CREATE OR REPLACE VIEW {database}.{schema}.REVIEW_SEARCH_VIEW AS
    SELECT 
        rc.CHUNK_ID,
        rc.CHUNK_TEXT,
        rc.FILE_NAME,
        rc.DOC_ID,
        rc.CHUNK_TYPE
    FROM {database}.{schema}.REVIEW_CHUNKS rc
    WHERE rc.CHUNK_TEXT IS NOT NULL
    """
    session.sql(create_view_sql).collect()
    st.success(f":material/check_circle: Created view: `{database}.{schema}.REVIEW_SEARCH_VIEW`")
```

* **`CREATE OR REPLACE VIEW`**: Creates a view that combines chunk text with metadata. Views update automatically when the underlying table changes.
* **`WHERE rc.CHUNK_TEXT IS NOT NULL`**: Filters out any chunks without text to avoid indexing errors.
* **Why a view?**: Cortex Search services query views, not tables directly. This provides flexibility to join multiple tables or add filtering logic.
* **Bordered container**: The button and SQL code are grouped in a bordered container (Step 1 in the app)

#### 4. Create the Cortex Search Service

```python
warehouse = st.text_input("Warehouse Name", value="COMPUTE_WH", 
                          help="Enter your Snowflake warehouse name")

if st.button(":material/rocket_launch: Create Search Service", type="primary"):
    with st.status("Creating Cortex Search Service...", expanded=True) as status:
        st.write(":material/looks_one: Creating service...")
        create_service_sql = f"""
        CREATE OR REPLACE CORTEX SEARCH SERVICE {database}.{schema}.CUSTOMER_REVIEW_SEARCH
            ON CHUNK_TEXT
            ATTRIBUTES FILE_NAME, CHUNK_TYPE
            WAREHOUSE = {warehouse}
            TARGET_LAG = '1 hour'
        AS (
            SELECT 
                CHUNK_TEXT,
                FILE_NAME,
                CHUNK_TYPE,
                CHUNK_ID
            FROM {database}.{schema}.REVIEW_SEARCH_VIEW
        )
        """
        session.sql(create_service_sql).collect()
        
        st.write(":material/looks_two: Waiting for indexing to complete...")
        st.caption("This may take a few minutes for 100 reviews...")
        
        status.update(label=":material/check_circle: Search service created!", state="complete", expanded=False)
    
    st.session_state.search_service = f"{database}.{schema}.CUSTOMER_REVIEW_SEARCH"
    st.balloons()
```

* **Warehouse input**: The search service needs a warehouse for indexing. Users enter their warehouse name here.
* **`ON CHUNK_TEXT`**: Specifies which column contains the searchable text. This is what users will search against.
* **`ATTRIBUTES FILE_NAME, CHUNK_TYPE`**: Additional columns to include in search results for context and filtering.
* **`TARGET_LAG = '1 hour'`**: How often the index refreshes to include new data. Set to 1 hour for this example.
* **`st.status(...)`**: Creates an expandable status indicator showing progress through the creation steps.
* **Indexing time**: After creation, Snowflake needs 1-2 minutes to index 100 review chunks. The service exists immediately but isn't searchable until indexing completes.
* **`st.balloons()`**: Celebratory animation when the service is created successfully.
* **Bordered container**: The entire service creation interface is grouped in a bordered container (Step 2 in the app)

#### 5. Verify the Search Service

```python
if st.button(":material/assignment: List My Cortex Search Services"):
    try:
        result = session.sql(f"SHOW CORTEX SEARCH SERVICES IN SCHEMA {database}.{schema}").collect()
        if result:
            st.success(f":material/check_circle: Found {len(result)} Cortex Search service(s) in `{database}.{schema}`:")
            st.dataframe(result, use_container_width=True)
        else:
            st.info("No Cortex Search services found. Create one in Step 2!")
    except Exception as e:
        st.error(f"Error: {str(e)}")
```

* **`SHOW CORTEX SEARCH SERVICES`**: Lists all search services in the specified schema.
* **Verification**: Confirms the service was created and shows its status (INDEXING or READY).
* **Status column**: Check that the service shows "READY" before searching. If it shows "INDEXING", wait a few minutes.
* **Integration with Day 20**: Once the service is verified and ready, you can proceed to Day 20 to query it using the Python API.
* **Bordered container**: The verification interface is grouped in a bordered container (Step 3 in the app)

When this code runs, you will have created and verified a Cortex Search service that's ready to use. The service indexes your customer review chunks and makes them searchable by meaning, not just keywords. Cortex Search understands meaning rather than just keywords—searching for "warm gloves" will find reviews mentioning "toasty hands" or "cold fingers" even without those exact words. In Day 20, you'll learn how to query this service to find relevant reviews.

---

### :material/library_books: Resources
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Python API: snowflake.core](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/api/snowflake.core)
- [CREATE CORTEX SEARCH SERVICE](https://docs.snowflake.com/en/sql-reference/sql/create-cortex-search-service)
