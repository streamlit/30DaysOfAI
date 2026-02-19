For today's challenge, our goal is to load customer reviews from Day 16, process them, and create searchable chunks for RAG applications. We need to provide two processing strategies: keeping each review intact as a single chunk (recommended for short reviews), or splitting longer reviews into smaller overlapping chunks. Once that's done, we will have properly sized text chunks saved to Snowflake and ready for embedding generation in Day 18.

**Dataset**: We use the customer reviews uploaded in Day 16, which are stored in the `EXTRACTED_DOCUMENTS` table. Each review is ~50-150 words and contains product feedback.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Load Reviews from Day 16

```python
import streamlit as st
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

# Initialize session state with Day 16's table location
if 'day17_database' not in st.session_state:
    if 'rag_source_database' in st.session_state:
        st.session_state.day17_database = st.session_state.rag_source_database
        st.session_state.day17_schema = st.session_state.rag_source_schema
    else:
        st.session_state.day17_database = "RAG_DB"
        st.session_state.day17_schema = "RAG_SCHEMA"

if st.button(":material/folder_open: Load Reviews", type="primary"):
    query = f"""
    SELECT 
        DOC_ID, FILE_NAME, FILE_TYPE, EXTRACTED_TEXT,
        UPLOAD_TIMESTAMP, WORD_COUNT, CHAR_COUNT
    FROM {st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_table_name}
    ORDER BY FILE_NAME
    """
    df = session.sql(query).to_pandas()
    st.session_state.loaded_data = df
    st.rerun()
```

* **Session state integration**: Automatically detects the database and schema from Day 16's `rag_source_database` if available.
* **Load button**: When clicked, queries all documents from the Day 16 table using `SELECT`.
* **`.to_pandas()`**: Converts the Snowflake result into a Pandas DataFrame for easier processing in Python.
* **`st.rerun()`**: Forces an immediate refresh to display the loaded data without waiting for another interaction.

#### 2. Choose Processing Strategy

```python
processing_option = st.radio(
    "Select processing strategy:",
    ["Keep each review as a single chunk (Recommended)", 
     "Chunk reviews longer than threshold"],
    index=0
)

if "Chunk reviews" in processing_option:
    chunk_size = st.slider("Chunk Size (words):", 50, 500, 200, 50)
    overlap = st.slider("Overlap (words):", 0, 100, 50, 10)
```

* **Radio buttons**: Provides two clear options. The first option keeps reviews intact (best for short customer reviews).
* **`index=0`**: Sets the first option as default (Keep each review intact).
* **Conditional sliders**: The chunk size and overlap controls only appear when the second option is selected.
* **Chunk size**: Controls how many words each chunk can contain (default: 200 words).
* **Overlap**: Sets how many words overlap between consecutive chunks (default: 50 words). This maintains context continuity.

#### 3. Create Chunks from Reviews

```python
# Option 1: One review = one chunk
for idx, row in df.iterrows():
    chunks.append({
        'chunk_id': idx + 1,
        'doc_id': row['DOC_ID'],
        'file_name': row['FILE_NAME'],
        'chunk_text': row['EXTRACTED_TEXT'],
        'chunk_size': row['WORD_COUNT'],
        'chunk_type': 'full_review'
    })

# Option 2: Split longer reviews
words = row['EXTRACTED_TEXT'].split()
if len(words) > chunk_size:
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        chunks.append({
            'chunk_id': len(chunks) + 1,
            'chunk_text': chunk_text,
            'chunk_size': len(chunk_words),
            'chunk_type': 'split_chunk'
        })
```

* **Option 1 (full review)**: Simply copies each review's `EXTRACTED_TEXT` into a single chunk. For 100 reviews, this creates 100 chunks.
* **Option 2 (split)**: Splits the text into words using `.split()`, then creates overlapping chunks by stepping through with `range(0, len(words), chunk_size - overlap)`.
* **Overlap math**: If chunk_size=200 and overlap=50, we step by 150 words each time (200-50=150). This means the last 50 words of one chunk become the first 50 words of the next.
* **`chunk_type`**: Labels chunks as either `'full_review'` (intact) or `'split_chunk'` (was split) for tracking purposes.

#### 4. Check if Chunk Table Exists

```python
try:
    result = session.sql(f"SELECT COUNT(*) as count FROM {full_chunk_table}").collect()
    record_count = result[0]['COUNT']
    
    if record_count > 0:
        chunk_table_exists = True
    else:
        chunk_table_exists = False
except:
    chunk_table_exists = False
```

* **Existence check**: Queries the chunk table to see if it exists and has data.
* **`COUNT(*)`**: Returns the number of rows in the table.
* **Try/except**: If the table doesn't exist, the query will fail, and we catch that as "table doesn't exist yet".
* **Smart default**: This boolean is used to set the default state of the replace mode checkbox.

#### 5. Replace Mode for Chunks

```python
# Initialize checkbox state based on table status
if 'day17_replace_mode' not in st.session_state:
    st.session_state.day17_replace_mode = chunk_table_exists
else:
    # Reset if table name changed
    if st.session_state.get('day17_last_chunk_table') != full_chunk_table:
        st.session_state.day17_replace_mode = chunk_table_exists
        st.session_state.day17_last_chunk_table = full_chunk_table

replace_mode = st.checkbox(
    f":material/sync: Replace Table Mode for `{st.session_state.day17_chunk_table}`",
    key="day17_replace_mode"
)
```

* **Session state management**: Initializes the checkbox based on whether the table has data (ticked if yes, unticked if no).
* **Table name tracking**: If the user changes the chunk table name, the checkbox state resets based on the new table's status.
* **`key="day17_replace_mode"`**: Binds the checkbox to session state, allowing programmatic control while still respecting user clicks.
* **Dynamic label**: The checkbox label updates to show the current chunk table name.

#### 6. Save Chunks to Snowflake

```python
# Create chunk table
create_table_sql = f"""
CREATE TABLE IF NOT EXISTS {full_chunk_table} (
    CHUNK_ID NUMBER,
    DOC_ID NUMBER,
    FILE_NAME VARCHAR,
    CHUNK_TEXT VARCHAR,
    CHUNK_SIZE NUMBER,
    CHUNK_TYPE VARCHAR,
    CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
"""
session.sql(create_table_sql).collect()

# Convert DataFrame columns to uppercase
chunks_df_upper = chunks_df.copy()
chunks_df_upper.columns = ['CHUNK_ID', 'DOC_ID', 'FILE_NAME', 'CHUNK_TEXT', 'CHUNK_SIZE', 'CHUNK_TYPE']

# Write to Snowflake
session.write_pandas(chunks_df_upper, table_name=chunk_table, 
                     database=database, schema=schema, 
                     overwrite=replace_mode)
```

* **Table schema**: Defines the structure for storing chunks. The `CHUNK_TEXT` column holds the actual text that will be embedded in Day 18.
* **`CREATED_TIMESTAMP`**: Automatically records when each chunk was created.
* **Column name conversion**: Snowflake expects uppercase column names. We copy the DataFrame and rename all columns to uppercase before saving.
* **`session.write_pandas()`**: Writes the DataFrame to Snowflake in bulk. Much faster than individual INSERT statements for 100+ chunks.
* **`overwrite=replace_mode`**: When True, deletes existing table data before writing. When False, appends to existing data.

#### 7. Query Saved Chunks

```python
if st.button(":material/analytics: Query Chunk Table"):
    chunks_df = session.sql(f"""
        SELECT CHUNK_ID, FILE_NAME, CHUNK_SIZE, CHUNK_TYPE,
               LEFT(CHUNK_TEXT, 100) AS TEXT_PREVIEW
        FROM {full_chunk_table}
        ORDER BY CHUNK_ID
    """).to_pandas()
    
    st.session_state.queried_chunks = chunks_df
    st.rerun()
```

* **Query button**: Fetches all chunks from the table for verification.
* **`LEFT(CHUNK_TEXT, 100)`**: Shows only the first 100 characters of each chunk as a preview, keeping the table readable.
* **`AS TEXT_PREVIEW`**: Renames the truncated column for clarity.
* **Session state persistence**: Stores the results so they survive app reruns.

#### 8. View Full Chunk Text

```python
chunk_id = st.selectbox("Select Chunk ID:", options=chunks_df['CHUNK_ID'].tolist())

if st.button("Load Chunk Text"):
    st.session_state.selected_chunk_id = chunk_id
    st.session_state.load_chunk_text = True
    st.rerun()

if st.session_state.get('load_chunk_text'):
    text_result = session.sql(f"""
        SELECT CHUNK_TEXT FROM {full_chunk_table} 
        WHERE CHUNK_ID = {st.session_state.selected_chunk_id}
    """).collect()
    
    chunk_text = text_result[0]['CHUNK_TEXT']
    st.text_area("Full Chunk Text", value=chunk_text, height=300)
```

* **Select dropdown**: Lists all chunk IDs, letting users pick which one to inspect.
* **Load button**: Stores the selected chunk ID and sets a flag in session state.
* **`st.rerun()`**: Forces an immediate refresh to display the loaded chunk text.
* **Text area display**: Shows the complete chunk text in a scrollable box (300 pixels tall).
* **Verification**: Confirms that chunks were saved correctly and contain the expected text.

#### 9. Integration with Day 18

```python
st.session_state.chunks_table = f"{database}.{schema}.{chunk_table}"
st.session_state.chunks_database = database
st.session_state.chunks_schema = schema
```

* **Pass to Day 18**: Stores the chunk table location for tomorrow's embedding generation.
* **Seamless handoff**: Day 18 will automatically find this table and generate embeddings for each chunk.
* **Ready for vectorization**: Chunks are now properly sized (not too long, not too short) for optimal embedding quality.

When this code runs, you will have a chunk processing system that takes Day 16's documents, converts them into properly sized chunks (either keeping reviews intact or splitting them with overlap), and saves them to a Snowflake table ready for Day 18's embedding generation.

---

### :material/library_books: Resources
- [Snowpark DataFrames](https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes)
- [write_pandas Documentation](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/api/snowflake.snowpark.Session.write_pandas)
- [Text Chunking Best Practices](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search#chunking-strategies)
