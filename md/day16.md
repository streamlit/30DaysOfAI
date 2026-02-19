For today's challenge, our goal is to build the first step of a RAG pipeline: extracting text from documents and **saving them to Snowflake**. We need to create a **batch file uploader** that accepts multiple TXT, MD (Markdown), and PDF files at once, then extract the raw text content and store it in a database table. Once that's done, we will have clean text ready for chunking, embedding, and RAG processing.

---

### :material/download: Download Sample Review Data

To get started quickly, download our sample dataset of 100 customer reviews from Avalanche winter sports equipment:

**📥 Download Link**: [review.zip](https://github.com/streamlit/30DaysOfAI/raw/refs/heads/main/assets/review.zip)

**How to Use:**
1. Click the download link above to get `review.zip`
2. Unzip the downloaded file on your computer
3. You'll find 100 review files: `review-001.txt` to `review-100.txt`
4. Use the app's file uploader to select all 100 files at once
5. Click **Extract Text** to process and save them to Snowflake

**What's Included:**
- 100 customer review files in TXT format
- Each review contains: product name, date, review summary, sentiment score, and order ID
- Perfect for testing batch processing and building RAG applications

**💡 Tip:** Upload all 100 files at once to see the batch processing in action!

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. Database Configuration and Session State

```python
import streamlit as st
from pypdf import PdfReader
import io

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Initialize session state for persistence
if 'database' not in st.session_state:
    st.session_state.database = "RAG_DB"
    st.session_state.schema = "RAG_SCHEMA"
    st.session_state.table_name = "EXTRACTED_DOCUMENTS"
```

* **`import streamlit as st`**: Imports the Streamlit library for building the web interface.
* **`from pypdf import PdfReader`**: Imports the PDF reading library to extract text from PDF files.
* **`try/except` block**: Automatically detects the environment and connects appropriately (SiS vs local/Community Cloud)
* **`session`**: The established Snowflake connection that we'll use to create tables and insert data
* **Session state initialization**: Stores database, schema, and table names in `st.session_state` so they persist across app reruns and user interactions.

#### 2. Batch File Upload

```python
uploaded_files = st.file_uploader(
    "Choose file(s)",
    type=["txt", "md", "pdf"],
    accept_multiple_files=True,
    help="Supported formats: TXT, MD, PDF. Upload multiple files at once!"
)

if uploaded_files:
    st.success(f":material/check_circle: {len(uploaded_files)} file(s) uploaded")
```

* **`accept_multiple_files=True`**: This is the key parameter that enables batch uploads. Users can select 20, 50, or even 100 files at once instead of uploading one at a time.
* **`type=["txt", "md", "pdf"]`**: Restricts uploads to only these file types, preventing invalid file formats.
* **`uploaded_files`**: Returns a list of file objects (or an empty list if nothing is uploaded).
* **Status message**: Shows "X file(s) uploaded" to confirm how many files were selected.

#### 3. Process Button and Progress Tracking

```python
# Process files button
process_button = st.button(
    f":material/sync: Extract Text from {len(uploaded_files)} File(s)",
    type="primary",
    use_container_width=True
)

if process_button:
    # Initialize progress tracking
    success_count = 0
    error_count = 0
    extracted_data = []
    
    progress_bar = st.progress(0, text="Starting extraction...")
    status_container = st.empty()
```

* **`st.button(...)`**: Creates a primary button that triggers the extraction process.
* **Dynamic label**: The button text shows the exact number of files that will be processed.
* **`type="primary"`**: Makes the button visually prominent with a distinct color.
* **Scoped variables**: `success_count`, `error_count`, and `extracted_data` are initialized inside the button block, so they're only available after the button is clicked.
* **Progress indicators**: `progress_bar` and `status_container` provide real-time feedback during processing.

#### 4. Replace Table Mode

```python
# Check if table exists
try:
    result = session.sql(f"SELECT COUNT(*) as count FROM {full_table_name}").collect()
    table_exists = True
except:
    table_exists = False

replace_mode = st.checkbox(
    f":material/sync: Replace Table Mode for `{st.session_state.table_name}`",
    value=table_exists,
    help=f"When enabled, replaces all existing data in {full_table_name}"
)
```

* **Table existence check**: Queries the database to see if the target table already has data.
* **Smart default**: If the table exists with data, the checkbox is ticked by default (suggesting replacement). If it's a new table, the checkbox is unticked (suggesting append).
* **Dynamic label**: The checkbox label updates to show the current table name, making it clear what will be replaced.
* **Replace vs Append**: When checked, existing data is deleted before new uploads. When unchecked, new files are added to existing data.

#### 5. Extract Text from Files

```python
for idx, uploaded_file in enumerate(uploaded_files):
    progress_pct = (idx + 1) / len(uploaded_files)
    progress_bar.progress(progress_pct, text=f"Processing {idx+1}/{len(uploaded_files)}: {uploaded_file.name}")
    
    # Extract text based on file extension
    if uploaded_file.name.lower().endswith(('.txt', '.md')):
        extracted_text = uploaded_file.read().decode("utf-8")
    elif uploaded_file.name.lower().endswith('.pdf'):
        pdf_reader = PdfReader(io.BytesIO(uploaded_file.read()))
        extracted_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n\n"
```

* **Progress tracking**: `enumerate()` gives us both the index and the file object, letting us show "Processing 15/30: review-015.txt" as we work through the batch.
* **`.progress(progress_pct, ...)`**: Updates a visual progress bar showing completion percentage and current file name.
* **File extension detection**: Uses `.endswith()` to determine file type, which is more reliable than checking MIME types.
* **Text extraction**: For TXT/MD files, reads and decodes as UTF-8. For PDFs, loops through all pages extracting text.
* **`io.BytesIO(...)`**: Wraps the uploaded file bytes in a file-like object that PdfReader can process.

#### 6. Handle Replace Mode

```python
# If replace mode enabled, truncate table first
if replace_mode:
    try:
        session.sql(f"TRUNCATE TABLE {full_table_name}").collect()
        st.success(f":material/check_circle: Cleared existing data from `{full_table_name}`")
    except:
        pass  # Table doesn't exist yet, that's fine
```

* **`TRUNCATE TABLE`**: Deletes all rows from the table while keeping the table structure intact. This is faster than `DELETE` for bulk operations.
* **Conditional execution**: Only runs if the checkbox is checked.
* **Try/except**: If the table doesn't exist yet, the truncate will fail, but we catch and ignore that error since we're about to create the table anyway.

#### 7. Save to Snowflake

```python
# Create database, schema, and table if needed
session.sql(f"CREATE DATABASE IF NOT EXISTS {st.session_state.database}").collect()
session.sql(f"CREATE SCHEMA IF NOT EXISTS {st.session_state.database}.{st.session_state.schema}").collect()

# Create table schema
create_table_sql = f"""
CREATE TABLE IF NOT EXISTS {full_table_name} (
    DOC_ID NUMBER AUTOINCREMENT,
    FILE_NAME VARCHAR,
    FILE_TYPE VARCHAR,
    FILE_SIZE NUMBER,
    EXTRACTED_TEXT VARCHAR,
    UPLOAD_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    WORD_COUNT NUMBER,
    CHAR_COUNT NUMBER
)
"""
session.sql(create_table_sql).collect()

# Insert extracted documents
for data in extracted_data:
    insert_sql = f"""
    INSERT INTO {full_table_name}
    (FILE_NAME, FILE_TYPE, FILE_SIZE, EXTRACTED_TEXT, WORD_COUNT, CHAR_COUNT)
    VALUES ('{data['file_name']}', '{data['file_type']}', {data['file_size']}, 
            '{data['text'].replace("'", "''")}', {data['word_count']}, {data['char_count']})
    """
    session.sql(insert_sql).collect()
```

* **Auto-creation**: Creates the database and schema if they don't exist using `IF NOT EXISTS` clauses.
* **`AUTOINCREMENT`**: The `DOC_ID` column automatically generates unique IDs for each document (1, 2, 3, ...).
* **`EXTRACTED_TEXT VARCHAR`**: This column stores the **complete document text**, not just metadata. This is what Day 17 will load and chunk.
* **`DEFAULT CURRENT_TIMESTAMP()`**: Automatically records when each document was uploaded.
* **`.replace("'", "''")`**: Escapes single quotes in the text to prevent SQL syntax errors when inserting.
* **Loop insertion**: Inserts each document one at a time. For 100 files, this means 100 INSERT statements.

#### 7. Query and View Saved Documents

```python
if st.button(":material/analytics: Query Table"):
    df = session.sql(f"SELECT * FROM {full_table_name}").to_pandas()
    st.session_state.queried_docs = df
    st.session_state.full_table_name = full_table_name
    st.rerun()

if 'queried_docs' in st.session_state:
    df = st.session_state.queried_docs
    st.dataframe(df)
    
    doc_id = st.selectbox("Select Document ID:", options=df['DOC_ID'].tolist())
    
    if st.button(":material/menu_book: Load Text"):
        doc = df[df['DOC_ID'] == doc_id].iloc[0]
        st.session_state.loaded_doc_text = doc['EXTRACTED_TEXT']
        st.session_state.loaded_doc_name = doc['FILE_NAME']
        st.rerun()
```

* **Query button**: Fetches all documents from the table using `SELECT *` and converts to a Pandas DataFrame for display.
* **Session state persistence**: Stores the DataFrame in `st.session_state.queried_docs` so it survives app reruns. Without this, clicking "Load Text" would reset the app and lose the query results.
* **`st.rerun()`**: Forces the app to refresh immediately, showing the newly loaded data without waiting for another user interaction.
* **`st.selectbox(...)`**: Creates a dropdown menu with all document IDs, letting users pick which document's full text to view.
* **Document viewer**: When "Load Text" is clicked, extracts the full `EXTRACTED_TEXT` column value and displays it in a text area, confirming that complete content (not just metadata) was stored.

#### 8. Integration with Day 17

```python
st.session_state.rag_source_table = f"{database}.{schema}.{table_name}"
st.session_state.rag_source_database = database
st.session_state.rag_source_schema = schema
```

* **Pass to Day 17**: Stores the table location in session state variables that Day 17 can access.
* **Seamless workflow**: Tomorrow's app will automatically detect this table and load all documents for chunking.
* **Batch merging**: All uploaded batches (whether 2 batches of 50 or 3 batches of 33) are in the same table, ready to be processed together.

When this code runs, you will have a document extraction tool that can upload 100 files in batches, extract all text content, and save it to a Snowflake table with full metadata. The `EXTRACTED_TEXT` column contains the complete document text that Day 17 will chunk for the RAG pipeline.

---

### :material/library_books: Resources
- [st.file_uploader Documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
- [pypdf Documentation](https://pypdf.readthedocs.io/en/stable/)
- [Snowflake AUTOINCREMENT](https://docs.snowflake.com/en/sql-reference/constraints-properties#autoincrement)
- [Session State Management](https://docs.streamlit.io/develop/concepts/architecture/session-state)
