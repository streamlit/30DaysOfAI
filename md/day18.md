For today's challenge, our goal is to generate embeddings for review chunks from Day 17 to enable semantic search in your RAG system. We need to convert text chunks into 768-dimensional vectors using Snowflake Cortex's `embed_text_768` function, then save them to a Snowflake table with the `VECTOR` data type. Once that's done, we will have vector embeddings ready for semantic search in Day 19.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Load Chunks from Day 17

```python
import streamlit as st
from snowflake.cortex import embed_text_768
import pandas as pd
import json

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Initialize with Day 17's table location
if 'day18_database' not in st.session_state:
    if 'chunks_database' in st.session_state:
        st.session_state.day18_database = st.session_state.chunks_database
        st.session_state.day18_schema = st.session_state.chunks_schema
    else:
        st.session_state.day18_database = "RAG_DB"
        st.session_state.day18_schema = "RAG_SCHEMA"

if st.button(":material/folder_open: Load Chunks", type="primary"):
    query = f"""
    SELECT 
        CHUNK_ID, DOC_ID, FILE_NAME, CHUNK_TEXT, CHUNK_SIZE, CHUNK_TYPE
    FROM {st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_chunk_table}
    ORDER BY CHUNK_ID
    """
    df = session.sql(query).to_pandas()
    st.session_state.chunks_data = df
    st.rerun()
```

* **`from snowflake.cortex import embed_text_768`**: Imports the Cortex function that generates 768-dimensional embeddings.
* **Session state integration**: Automatically detects the chunk table location from Day 17's `chunks_database` and `chunks_schema`.
* **Load button**: Queries all chunks from Day 17's table using `SELECT`.
* **`st.rerun()`**: Forces an immediate refresh to display the loaded chunks.

#### 2. Generate Embeddings with Batch Processing

```python
batch_size = st.selectbox("Batch Size", [10, 25, 50, 100], index=1)

if st.button(":material/calculate: Generate Embeddings", type="primary"):
    embeddings = []
    total_chunks = len(df)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(0, total_chunks, batch_size):
        batch_end = min(i + batch_size, total_chunks)
        status_text.text(f"Processing chunks {i+1} to {batch_end} of {total_chunks}")
        
        for idx, row in df.iloc[i:batch_end].iterrows():
            emb = embed_text_768(
                model='snowflake-arctic-embed-m', 
                text=row['CHUNK_TEXT']
            )
            embeddings.append({
                'chunk_id': row['CHUNK_ID'],
                'embedding': emb
            })
        
        progress_pct = batch_end / total_chunks
        progress_bar.progress(progress_pct)
    
    st.session_state.embeddings_data = embeddings
```

* **Batch size selection**: Lets users process chunks in batches of 10, 25, 50, or 100 for better performance control.
* **Progress tracking**: Creates a progress bar and status text to show processing status in real-time.
* **`embed_text_768(...)`**: This is the core Cortex function that converts text into a 768-dimensional vector. The `model='snowflake-arctic-embed-m'` parameter specifies which embedding model to use (Arctic Embed M is optimized for semantic search).
* **Embedding structure**: Returns a list of 768 floating-point numbers representing the semantic meaning of the text.
* **Storage**: Embeddings are stored in session state as a list of dictionaries, each containing a chunk ID and its embedding vector.

#### 3. View Generated Embeddings

```python
if 'embeddings_data' in st.session_state:
    with st.container(border=True):
        st.subheader(":material/looks_3: View Embeddings")
        
        embeddings = st.session_state.embeddings_data

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Embeddings Generated", len(embeddings))
        with col2:
            st.metric("Dimensions per Embedding", 768)
        
        # Show sample embedding
        with st.expander(":material/search: View Sample Embedding"):
            sample_emb = embeddings[0]['embedding']
            st.write("**First 10 values:**")
            st.write(sample_emb[:10])
```

* **Container structure**: The view is wrapped in a bordered container with a subheader.
* **Metrics display**: Shows total count of embeddings generated and confirms the 768-dimensional vector size.
* **Sample preview**: Displays the first 10 values of a sample embedding vector (e.g., `[0.234, -0.456, 0.123, ...]`).
* **Verification**: Lets you confirm embeddings were generated successfully before saving to Snowflake.

#### 4. Save Embeddings to Snowflake

```python
# Table status check
try:
    check_query = f"""
    SELECT COUNT(*) as count 
    FROM {full_embedding_table}
    """
    result = session.sql(check_query).collect()
    current_count = result[0]['COUNT']
    
    if current_count > 0:
        st.warning(f":material/warning: **{current_count:,} embedding(s)** currently in table")
        embedding_table_exists = True
    else:
        st.info(":material/inbox: **Embedding table is empty**")
        embedding_table_exists = False
except:
    st.info(":material/inbox: **Embedding table doesn't exist yet**")
    embedding_table_exists = False

# Replace mode checkbox
replace_mode = st.checkbox(
    f":material/sync: Replace Table Mode for `{st.session_state.day18_embedding_table}`",
    key="day18_replace_mode"
)

if st.button(":material/save: Save Embeddings to Snowflake", type="primary"):
    with st.status("Saving embeddings...", expanded=True) as status:
        # Create or replace table based on mode
        if replace_mode:
            create_table_sql = f"""
            CREATE OR REPLACE TABLE {full_embedding_table} (
                CHUNK_ID NUMBER,
                EMBEDDING VECTOR(FLOAT, 768),
                CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
            """
            session.sql(create_table_sql).collect()
            st.write(":material/check_circle: Replaced existing table")
        else:
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {full_embedding_table} (
                CHUNK_ID NUMBER,
                EMBEDDING VECTOR(FLOAT, 768),
                CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
            """
            session.sql(create_table_sql).collect()
            st.write(":material/check_circle: Table ready")
        
        # Insert embeddings
        st.write(f":material/looks_two: Inserting {len(embeddings)} embeddings...")
        
        for i, emb_data in enumerate(embeddings):
            # Convert embedding to list
            if isinstance(emb_data['embedding'], list):
                emb_list = emb_data['embedding']
            else:
                emb_list = list(emb_data['embedding'])
            
            # Convert to proper array format for Snowflake
            emb_array = "[" + ",".join([str(float(x)) for x in emb_list]) + "]"
            
            insert_sql = f"""
            INSERT INTO {full_embedding_table} (CHUNK_ID, EMBEDDING)
            SELECT {emb_data['chunk_id']}, {emb_array}::VECTOR(FLOAT, 768)
            """
            session.sql(insert_sql).collect()
            
            if (i + 1) % 10 == 0:
                st.write(f"Saved {i + 1} of {len(embeddings)} embeddings...")
        
        status.update(label="Embeddings saved!", state="complete", expanded=False)
```

* **Table status check**: Checks if the embeddings table exists and shows current record count before saving.
* **Replace mode**: A checkbox lets users choose between replacing all existing embeddings (`CREATE OR REPLACE TABLE`) or appending to existing data (`CREATE TABLE IF NOT EXISTS`).
* **`VECTOR(FLOAT, 768)`**: Snowflake's special data type for storing embeddings, optimized for vector operations and similarity calculations.
* **Type handling**: Checks if the embedding is already a list or needs to be converted using `list()`.
* **Array string conversion**: Converts the Python list to a string format like `"[0.1, 0.2, 0.3, ...]"` that Snowflake can parse.
* **`::VECTOR(FLOAT, 768)`**: This SQL casting syntax converts the string array into Snowflake's VECTOR type. Using `SELECT ... ::VECTOR` instead of direct `VALUES` is required for proper type conversion.
* **Progress updates**: Uses `st.status()` container and shows progress every 10 embeddings inserted.
* **Session state storage**: Saves the embeddings table location for Day 19's Cortex Search creation.

#### 5. View Saved Embeddings

```python
# View Saved Embeddings Section
with st.container(border=True):
    st.subheader(":material/search: View Saved Embeddings")
    
    # Check if embeddings table exists and show record count
    try:
        count_result = session.sql(f"""
            SELECT COUNT(*) as CNT FROM {full_embedding_table}
        """).collect()
        
        if count_result:
            record_count = count_result[0]['CNT']
            if record_count > 0:
                st.warning(f":material/warning: **{record_count:,} embedding(s)** currently in table")
            else:
                st.info(":material/inbox: **Embedding table is empty**")
    except:
        st.info(":material/inbox: **Embedding table doesn't exist yet**")
    
    query_button = st.button(":material/analytics: Query Embedding Table", type="secondary")
    
    if query_button:
        query = f"""
        SELECT 
            CHUNK_ID,
            EMBEDDING,
            CREATED_TIMESTAMP,
            VECTOR_L2_DISTANCE(EMBEDDING, EMBEDDING) as SELF_DISTANCE
        FROM {full_embedding_table}
        ORDER BY CHUNK_ID
        """
        result_df = session.sql(query).to_pandas()
        st.session_state.queried_embeddings = result_df
        st.session_state.queried_embeddings_table = full_embedding_table
        st.rerun()
```

* **Separate view section**: A dedicated container for viewing saved embeddings from the table.
* **Record count check**: Displays current count of embeddings in the table before querying.
* **Query button**: Fetches all embeddings from the table for verification.
* **`VECTOR_L2_DISTANCE(EMBEDDING, EMBEDDING)`**: Calculates the distance between each embedding and itself, which should always be 0. This validates that embeddings were stored correctly.
* **Session state storage**: Saves query results to persist across reruns.
* **Display columns**: Shows CHUNK_ID, CREATED_TIMESTAMP, and SELF_DISTANCE (but not the full EMBEDDING column, which would be too large to display).

#### 6. View Individual Embedding Vectors

```python
# Display results if available in session state
if 'queried_embeddings' in st.session_state:
    emb_df = st.session_state.queried_embeddings
    
    if len(emb_df) > 0:
        # Summary metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Embeddings", len(emb_df))
        with col2:
            st.metric("Dimensions", "768")
        
        # Display table without EMBEDDING column
        embedding_col = None
        for col in emb_df.columns:
            if col.upper() == 'EMBEDDING':
                embedding_col = col
                break
        
        if embedding_col:
            display_df = emb_df.drop(columns=[embedding_col])
        else:
            display_df = emb_df
        
        st.dataframe(display_df, use_container_width=True)
        st.info(":material/lightbulb: Self-distance should be 0, confirming embeddings are stored correctly")
        
        # View individual embedding vectors
        if embedding_col:
            with st.expander(":material/search: View Individual Embedding Vectors"):
                # Find CHUNK_ID column (case-insensitive)
                chunk_id_col = None
                for col in emb_df.columns:
                    if col.upper() == 'CHUNK_ID':
                        chunk_id_col = col
                        break
                
                chunk_ids = emb_df[chunk_id_col].tolist()
                selected_chunk = st.selectbox("Select CHUNK_ID", chunk_ids, key="view_embedding_chunk")
                
                if st.button(":material/analytics: Load Embedding Vector", key="load_embedding_btn"):
                    selected_emb = emb_df[emb_df[chunk_id_col] == selected_chunk][embedding_col].iloc[0]
                    st.session_state.loaded_embedding = selected_emb
                    st.session_state.loaded_embedding_chunk = selected_chunk
                    st.rerun()
                
                # Display loaded embedding
                if 'loaded_embedding' in st.session_state:
                    st.write(f"**Embedding Vector for CHUNK_ID {st.session_state.loaded_embedding_chunk}:**")
                    
                    # Convert to list if needed
                    emb_vector = st.session_state.loaded_embedding
                    if isinstance(emb_vector, str):
                        import json
                        emb_vector = json.loads(emb_vector)
                    elif hasattr(emb_vector, 'tolist'):
                        emb_vector = emb_vector.tolist()
                    elif not isinstance(emb_vector, list):
                        emb_vector = list(emb_vector)
                    
                    st.caption(f"Vector length: {len(emb_vector)} dimensions")
                    st.code(emb_vector, language="python")
```

* **Results display**: Shows the queried embeddings if available in session state.
* **Case-insensitive column handling**: Searches for 'EMBEDDING' and 'CHUNK_ID' columns case-insensitively to handle Snowflake's uppercase column names.
* **Selective display**: Drops the EMBEDDING column from the main dataframe display since it's too large (768 dimensions).
* **Select dropdown**: Lists all chunk IDs, letting users pick which embedding to inspect.
* **Load button**: Stores the selected embedding and chunk ID in session state.
* **Type conversion**: Handles multiple embedding formats (string, list, numpy array) and converts to list for display.
* **`st.code(...)`**: Displays the full 768-dimensional vector as a formatted Python list, making it easy to copy or inspect.
* **Verification**: Confirms embeddings are complete and correctly formatted before using them in semantic search.

#### 7. Integration with Day 19

```python
st.session_state.embeddings_table = f"{database}.{schema}.{embedding_table}"
st.session_state.embeddings_database = database
st.session_state.embeddings_schema = schema
```

* **Pass to Day 19**: Stores the embedding table location for tomorrow's Cortex Search service creation.
* **Semantic search ready**: Day 19 will use these embeddings to create a search service that can find similar reviews based on meaning, not just keywords.

When this code runs, you will have a complete embedding generation system that converts Day 17's text chunks into 768-dimensional vectors, saves them to Snowflake's VECTOR data type, and provides tools to verify the embeddings were created correctly. These vectors enable semantic search that understands meaning, not just exact word matches.

---

### :material/library_books: Resources
- [Cortex EMBED_TEXT_768 Function](https://docs.snowflake.com/en/sql-reference/functions/embed_text_768-snowflake-cortex)
- [Understanding Embeddings](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ml-embeddings)
- [Snowflake VECTOR Data Type](https://docs.snowflake.com/en/sql-reference/data-types-vector)
- [Vector Distance Functions](https://docs.snowflake.com/en/sql-reference/functions-vector)
