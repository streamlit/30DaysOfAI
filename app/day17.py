# Day 17
# Loading and Transforming Customer Reviews for RAG

import streamlit as st
import pandas as pd
import re

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

st.title(":material/sync: Prepare and Chunk Data for RAG")
st.write("Load customer reviews from Day 16, process them, and prepare searchable chunks for RAG.")

# Initialize session state for database configuration
if 'day17_database' not in st.session_state:
    # Check if we have table reference from Day 16
    if 'rag_source_database' in st.session_state:
        st.session_state.day17_database = st.session_state.rag_source_database
        st.session_state.day17_schema = st.session_state.rag_source_schema
        st.session_state.day17_table_name = "EXTRACTED_DOCUMENTS"
    else:
        st.session_state.day17_database = "RAG_DB"
        st.session_state.day17_schema = "RAG_SCHEMA"
        st.session_state.day17_table_name = "EXTRACTED_DOCUMENTS"

if 'day17_chunk_table' not in st.session_state:
    st.session_state.day17_chunk_table = "REVIEW_CHUNKS"

# Database Configuration and Load Section
with st.container(border=True):
    st.subheader(":material/analytics: Source Data Configuration")
    
    # Database configuration
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.day17_database = st.text_input(
            "Database", 
            value=st.session_state.day17_database, 
            key="day17_db_input"
        )
    with col2:
        st.session_state.day17_schema = st.text_input(
            "Schema", 
            value=st.session_state.day17_schema, 
            key="day17_schema_input"
        )
    with col3:
        st.session_state.day17_table_name = st.text_input(
            "Source Table", 
            value=st.session_state.day17_table_name, 
            key="day17_table_input"
    )
    
    st.info(f":material/location_on: Loading from: `{st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_table_name}`")
    st.caption(":material/lightbulb: This should point to the EXTRACTED_DOCUMENTS table from Day 16")
    
    # Check for existing loaded data
    if 'loaded_data' in st.session_state:
        st.success(f":material/check_circle: **{len(st.session_state.loaded_data)} document(s)** already loaded")

    # Load documents button
    if st.button(":material/folder_open: Load Reviews", type="primary", use_container_width=True):
        try:
            with st.status("Loading reviews from Snowflake...", expanded=True) as status:
                st.write(":material/wifi: Querying database...")
                
                query = f"""
                SELECT 
                    DOC_ID,
                    FILE_NAME,
                    FILE_TYPE,
                    EXTRACTED_TEXT,
                    UPLOAD_TIMESTAMP,
                    WORD_COUNT,
                    CHAR_COUNT
                FROM {st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_table_name}
                ORDER BY FILE_NAME
                """
                df = session.sql(query).to_pandas()
                
                st.write(f":material/check_circle: Loaded {len(df)} review(s)")
                status.update(label="Reviews loaded successfully!", state="complete", expanded=False)
                
                # Store in session state
                st.session_state.loaded_data = df
                st.session_state.source_table = f"{st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_table_name}"
                st.rerun()
                
        except Exception as e:
            st.error(f"Error loading reviews: {str(e)}")
            st.info(":material/lightbulb: Make sure you've uploaded review files in Day 16 first!")

# Main content - Review Summary
if 'loaded_data' in st.session_state:
    with st.container(border=True):
        st.subheader(":material/looks_one: Review Summary")
        
        df = st.session_state.loaded_data
                
        # Show statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Reviews", len(df))
        with col2:
            st.metric("Total Words", f"{df['WORD_COUNT'].sum():,}")
        with col3:
            st.metric("Avg Words/Review", f"{df['WORD_COUNT'].mean():.0f}")
            
        # Display review summary
        st.dataframe(df[['DOC_ID', 'FILE_NAME', 'FILE_TYPE', 'UPLOAD_TIMESTAMP', 'WORD_COUNT']], 
                    use_container_width=True)
                
    # Processing options
    with st.container(border=True):
        st.subheader(":material/looks_two: Choose Processing Strategy")
        
        st.info("""
        **Customer Review Processing Options:**
        
        Since customer reviews are typically short (~150 words each), you have two options:
        - **Option 1**: Use each review as-is (Recommended for reviews)
        - **Option 2**: Chunk longer reviews (For reviews >200 words)
        """)
        
        processing_option = st.radio(
            "Select processing strategy:",
            ["Keep each review as a single chunk (Recommended)", 
             "Chunk reviews longer than threshold"],
            index=0
        )
        
        # Add chunk size controls (only show if chunking option is selected)
        if "Chunk reviews" in processing_option:
            col1, col2 = st.columns(2)
            with col1:
                chunk_size = st.slider(
                    "Chunk Size (words):",
                    min_value=50,
                    max_value=500,
                    value=200,
                    step=50,
                    help="Maximum number of words per chunk"
                )
            with col2:
                overlap = st.slider(
                    "Overlap (words):",
                    min_value=0,
                    max_value=100,
                    value=50,
                    step=10,
                    help="Number of overlapping words between chunks"
                )
            st.caption(f"Reviews with >{chunk_size} words will be split into chunks of {chunk_size} words with {overlap} word overlap")
        else:
            # Default values if not chunking
            chunk_size = 200
            overlap = 50
        
        if st.button(":material/flash_on: Process Reviews", type="primary", use_container_width=True):
            chunks = []
            
            with st.status("Processing reviews...", expanded=True) as status:
                if "Keep each review" in processing_option:
                    # Option 1: One review = one chunk
                    st.write(":material/edit_note: Creating one chunk per review...")
                    
                    for idx, row in df.iterrows():
                        chunks.append({
                            'doc_id': row['DOC_ID'],
                            'file_name': row['FILE_NAME'],
                            'chunk_id': idx + 1,
                            'chunk_text': row['EXTRACTED_TEXT'],
                            'chunk_size': row['WORD_COUNT'],
                            'chunk_type': 'full_review'
                        })
                    
                    st.write(f":material/check_circle: Created {len(chunks)} chunks (1 per review)")
                    
                else:
                    # Option 2: Chunk longer reviews
                    st.write(f":material/edit_note: Chunking reviews longer than {chunk_size} words...")
                    chunk_id = 1
                    
                    for idx, row in df.iterrows():
                        text = row['EXTRACTED_TEXT']
                        words = text.split()
                        
                        if len(words) <= chunk_size:
                            # Keep short reviews as-is
                            chunks.append({
                                'doc_id': row['DOC_ID'],
                                'file_name': row['FILE_NAME'],
                                'chunk_id': chunk_id,
                                'chunk_text': text,
                                'chunk_size': len(words),
                                'chunk_type': 'full_review'
                            })
                            chunk_id += 1
                        else:
                            # Split longer reviews
                            for i in range(0, len(words), chunk_size - overlap):
                                chunk_words = words[i:i + chunk_size]
                                chunk_text = ' '.join(chunk_words)
                                
                                chunks.append({
                                    'doc_id': row['DOC_ID'],
                                    'file_name': row['FILE_NAME'],
                                    'chunk_id': chunk_id,
                                    'chunk_text': chunk_text,
                                    'chunk_size': len(chunk_words),
                                    'chunk_type': 'chunked_review'
                                })
                                chunk_id += 1
                    
                    st.write(f":material/check_circle: Created {len(chunks)} chunks from {len(df)} reviews")
                
                status.update(label="Processing complete!", state="complete", expanded=False)
                    
            # Store chunks in session state
            st.session_state.review_chunks = chunks
            st.session_state.processing_option = processing_option
            
            st.success(f":material/check_circle: Processed {len(df)} reviews into {len(chunks)} searchable chunks!")
    
    # Display chunks if they exist
    if 'review_chunks' in st.session_state:
        with st.container(border=True):
            st.subheader(":material/looks_3: Processed Review Chunks")
            
            chunks = st.session_state.review_chunks
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Chunks", len(chunks))
            with col2:
                full_reviews = len([c for c in chunks if c['chunk_type'] == 'full_review'])
                st.metric("Full Reviews", full_reviews)
            with col3:
                split_reviews = len([c for c in chunks if c['chunk_type'] == 'chunked_review'])
                st.metric("Split Reviews", split_reviews)
            
            # Display chunks
            with st.expander(":material/description: View Chunks"):
                chunks_df = pd.DataFrame(chunks)
                st.dataframe(chunks_df[['chunk_id', 'file_name', 'chunk_size', 'chunk_type', 'chunk_text']], 
                            use_container_width=True)
        
        # Step 4: Save chunks to Snowflake
        with st.container(border=True):
            st.subheader(":material/looks_4: Save Chunks to Snowflake")
            
            chunks = st.session_state.review_chunks
            
            # Chunk table name
            col1, col2 = st.columns([2, 1])
            with col1:
                st.session_state.day17_chunk_table = st.text_input(
                    "Chunk Table Name",
                    value=st.session_state.day17_chunk_table,
                    help="Table name for storing review chunks",
                    key="day17_chunk_table_input"
                )
            
            full_chunk_table = f"{st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_chunk_table}"
            st.code(full_chunk_table, language="sql")
            
            # Check if chunk table exists and show status
            chunk_table_exists = False  # Default to False (unticked)
            try:
                count_result = session.sql(f"""
                    SELECT COUNT(*) as CNT FROM {full_chunk_table}
                """).collect()
                
                if count_result:
                    record_count = count_result[0]['CNT']
                    if record_count > 0:
                        st.warning(f":material/warning: **{record_count} chunk(s)** currently in table `{full_chunk_table}`")
                        chunk_table_exists = True  # Only tick if table has data
                    else:
                        st.info(":material/inbox: **Chunk table is empty** - No chunks saved yet.")
                        chunk_table_exists = False
            except:
                st.info(":material/inbox: **Chunk table doesn't exist yet** - Will be created when you save chunks.")
                chunk_table_exists = False
            
            # Initialize or update checkbox state based on table status
            # This ensures checkbox reflects current table state
            if 'day17_replace_mode' not in st.session_state:
                # First time - initialize based on table existence
                st.session_state.day17_replace_mode = chunk_table_exists
            else:
                # Check if table name changed - if so, reset based on new table status
                if 'day17_last_chunk_table' not in st.session_state or st.session_state.day17_last_chunk_table != full_chunk_table:
                    st.session_state.day17_replace_mode = chunk_table_exists
                    st.session_state.day17_last_chunk_table = full_chunk_table
            
            # Replace mode checkbox
            replace_mode = st.checkbox(
                f":material/sync: Replace Table Mode for `{st.session_state.day17_chunk_table}`",
                help=f"When enabled, clears all existing data in {full_chunk_table} before saving new chunks",
                key="day17_replace_mode"
            )
            
            if replace_mode:
                st.warning("**Replace Mode Active**: Existing chunks will be deleted before saving new ones.")
            else:
                st.success("**Append Mode Active**: New chunks will be added to existing data.")
            
            # Save chunks to table
            if st.button(":material/save: Save Chunks to Snowflake", type="primary", use_container_width=True):
                try:
                    with st.status("Saving chunks to Snowflake...", expanded=True) as status:
                        # Step 1: Create table if it doesn't exist
                        st.write(":material/looks_one: Checking table...")
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
                        
                        # Step 2: Replace mode - clear existing chunks
                        if replace_mode:
                            st.write(":material/sync: Replace mode: Clearing existing chunks...")
                            try:
                                session.sql(f"TRUNCATE TABLE {full_chunk_table}").collect()
                                st.write("   :material/check_circle: Existing chunks cleared")
                            except Exception as e:
                                st.write(f"   :material/warning: No existing chunks to clear")
                        
                        # Step 3: Insert chunks
                        st.write(f":material/looks_3: Inserting {len(chunks)} chunk(s)...")
                        chunks_df = pd.DataFrame(chunks)
                        
                        # Rename columns to uppercase to match Snowflake table
                        chunks_df_upper = chunks_df[['chunk_id', 'doc_id', 'file_name', 'chunk_text', 
                                                       'chunk_size', 'chunk_type']].copy()
                        chunks_df_upper.columns = ['CHUNK_ID', 'DOC_ID', 'FILE_NAME', 'CHUNK_TEXT', 
                                                   'CHUNK_SIZE', 'CHUNK_TYPE']
                        
                        if replace_mode:
                            # Use overwrite for replace mode (though we already truncated)
                            session.write_pandas(chunks_df_upper,
                                               table_name=st.session_state.day17_chunk_table,
                                               database=st.session_state.day17_database,
                                               schema=st.session_state.day17_schema,
                                               overwrite=True)
                        else:
                            # Append mode
                            session.write_pandas(chunks_df_upper,
                                               table_name=st.session_state.day17_chunk_table,
                                               database=st.session_state.day17_database,
                                               schema=st.session_state.day17_schema,
                                               overwrite=False)
                        
                        status.update(label=":material/check_circle: Chunks saved!", state="complete", expanded=False)
                    
                    mode_msg = "replaced in" if replace_mode else "saved to"
                    st.success(f":material/check_circle: Successfully {mode_msg} `{full_chunk_table}`\n\n:material/description: {len(chunks)} chunk(s) now in table")
                    
                    # Store for Day 18
                    st.session_state.chunks_table = full_chunk_table
                    st.session_state.chunks_database = st.session_state.day17_database
                    st.session_state.chunks_schema = st.session_state.day17_schema
                    st.session_state.chunk_table_saved = True
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Error saving chunks: {str(e)}")

# View Saved Chunks Section
with st.container(border=True):
    st.subheader(":material/search: View Saved Chunks")
    
    # Show which table is being queried (from Step 4 configuration)
    full_chunk_table = f"{st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_chunk_table}"
    st.caption(f":material/analytics: Querying chunk table: `{full_chunk_table}`")
    
    query_button = st.button(":material/analytics: Query Chunk Table", type="secondary", use_container_width=True)
    
    if query_button:
        try:
            query_sql = f"""
            SELECT 
                CHUNK_ID,
                FILE_NAME,
                CHUNK_SIZE,
                CHUNK_TYPE,
                LEFT(CHUNK_TEXT, 100) AS TEXT_PREVIEW,
                CREATED_TIMESTAMP
            FROM {full_chunk_table}
            ORDER BY CHUNK_ID
            """
            chunks_df = session.sql(query_sql).to_pandas()
            
            # Store in session state for persistence
            st.session_state.queried_chunks = chunks_df
            st.session_state.queried_chunks_table = full_chunk_table
            st.rerun()
                
        except Exception as e:
            st.error(f"Error querying chunks: {str(e)}")
    
    # Display results if available in session state
    if 'queried_chunks' in st.session_state and st.session_state.get('queried_chunks_table') == full_chunk_table:
        chunks_df = st.session_state.queried_chunks
        
        if len(chunks_df) > 0:
            st.code(full_chunk_table, language="sql")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Chunks", len(chunks_df))
            with col2:
                full_count = len(chunks_df[chunks_df['CHUNK_TYPE'] == 'full_review'])
                st.metric("Full Reviews", full_count)
            with col3:
                split_count = len(chunks_df[chunks_df['CHUNK_TYPE'] == 'chunked_review'])
                st.metric("Split Reviews", split_count)
            
            # Display table
            st.dataframe(
                chunks_df[['CHUNK_ID', 'FILE_NAME', 'CHUNK_SIZE', 'CHUNK_TYPE', 'TEXT_PREVIEW']],
                use_container_width=True
            )
            
            # Option to view full text of a chunk
            with st.expander(":material/menu_book: View Full Chunk Text"):
                chunk_id = st.selectbox(
                    "Select Chunk ID:",
                    options=chunks_df['CHUNK_ID'].tolist(),
                    format_func=lambda x: f"Chunk #{x} - {chunks_df[chunks_df['CHUNK_ID']==x]['FILE_NAME'].values[0]}",
                    key="chunk_text_selector"
                )
                
                if st.button("Load Chunk Text", key="load_chunk_text_btn"):
                    # Store selection in session state
                    st.session_state.selected_chunk_id = chunk_id
                    st.session_state.load_chunk_text = True
                    st.rerun()
                
                # Display chunk text if loaded
                if st.session_state.get('load_chunk_text') and st.session_state.get('selected_chunk_id'):
                    text_sql = f"SELECT CHUNK_TEXT, FILE_NAME FROM {full_chunk_table} WHERE CHUNK_ID = {st.session_state.selected_chunk_id}"
                    text_result = session.sql(text_sql).to_pandas()
                    if len(text_result) > 0:
                        chunk = text_result.iloc[0]
                        st.text_area(
                            chunk['FILE_NAME'],
                            value=chunk['CHUNK_TEXT'],
                            height=300,
                            key=f"chunk_text_display_{st.session_state.selected_chunk_id}"
                        )
        else:
            st.info(":material/inbox: No chunks found in table.")
    else:
        st.info(":material/inbox: No chunks queried yet. Click 'Query Chunk Table' to view saved chunks.")

st.divider()
st.caption("Day 17: Loading and Transforming Customer Reviews for RAG | 30 Days of AI")
