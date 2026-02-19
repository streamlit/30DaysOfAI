# Day 18
# Generating Embeddings for Customer Reviews

import streamlit as st
from snowflake.cortex import embed_text_768
import pandas as pd
import numpy as np

st.title(":material/calculate: Embeddings Generator for Customer Reviews")
st.write("Generate embeddings for review chunks from Day 17 to enable semantic search.")

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
if 'day18_database' not in st.session_state:
    # Check if we have chunks from Day 17
    if 'chunks_database' in st.session_state:
        st.session_state.day18_database = st.session_state.chunks_database
        st.session_state.day18_schema = st.session_state.chunks_schema
        st.session_state.day18_chunk_table = "REVIEW_CHUNKS"
    else:
        st.session_state.day18_database = "RAG_DB"
        st.session_state.day18_schema = "RAG_SCHEMA"
        st.session_state.day18_chunk_table = "REVIEW_CHUNKS"

if 'day18_embedding_table' not in st.session_state:
    st.session_state.day18_embedding_table = "REVIEW_EMBEDDINGS"

# Explanation
with st.expander(":material/library_books: What are embeddings?", expanded=True):
    st.markdown("""
    **Embeddings** convert text into numbers (vectors) that capture meaning:
    
    - Similar texts → Similar vectors
    - Different texts → Different vectors
    - Enables "search by meaning" (semantic search)
    
    The model outputs **768 numbers** for any text input.
    
    **In RAG for Customer Reviews**: Each review (or chunk) gets its own embedding, 
    allowing semantic search to find relevant customer feedback!
    
    **Example**: Search for "warm gloves" will find reviews mentioning "provides good warmth", 
    "kept hands toasty", even without exact keywords!
    """)

# Source Data Configuration and Load Section
with st.container(border=True):
    st.subheader(":material/analytics: Source Data Configuration")
    
    # Database configuration
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.day18_database = st.text_input(
            "Database", 
            value=st.session_state.day18_database, 
            key="day18_db_input"
        )
    with col2:
        st.session_state.day18_schema = st.text_input(
            "Schema", 
            value=st.session_state.day18_schema, 
            key="day18_schema_input"
        )
    with col3:
        st.session_state.day18_chunk_table = st.text_input(
            "Chunks Table", 
            value=st.session_state.day18_chunk_table, 
            key="day18_chunk_table_input"
        )
    
    st.info(f":material/location_on: Loading from: `{st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_chunk_table}`")
    st.caption(":material/lightbulb: This should point to the REVIEW_CHUNKS table from Day 17")
    
    # Check for existing loaded data
    if 'chunks_data' in st.session_state:
        st.success(f":material/check_circle: **{len(st.session_state.chunks_data)} chunk(s)** already loaded")
    
    # Load chunks button
    if st.button(":material/folder_open: Load Chunks", type="primary", use_container_width=True):
        try:
            with st.status("Loading chunks...", expanded=True) as status:
                st.write(":material/wifi: Querying database...")
                
                query = f"""
                SELECT 
                    CHUNK_ID,
                    DOC_ID,
                    FILE_NAME,
                    CHUNK_TEXT,
                    CHUNK_SIZE,
                    CHUNK_TYPE
                FROM {st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_chunk_table}
                ORDER BY CHUNK_ID
                """
                df = session.sql(query).to_pandas()
                
                st.write(f":material/check_circle: Loaded {len(df)} chunks")
                status.update(label="Chunks loaded successfully!", state="complete", expanded=False)
                
                # Store in session state
                st.session_state.chunks_data = df
                st.rerun()
                
        except Exception as e:
            st.error(f"Error loading chunks: {str(e)}")
            st.info(":material/lightbulb: Make sure you've processed reviews in Day 17 first!")

# Main content - Chunk Summary
if 'chunks_data' in st.session_state:
    with st.container(border=True):
        st.subheader(":material/looks_one: Chunk Summary")
        
        df = st.session_state.chunks_data
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Chunks", len(df))
        with col2:
            st.metric("Unique Reviews", df['FILE_NAME'].nunique())
        with col3:
            st.metric("Avg Chunk Size", f"{df['CHUNK_SIZE'].mean():.0f} words")
        
        # Show chunk type distribution
        if 'CHUNK_TYPE' in df.columns:
            st.write("**Chunk Type Distribution:**")
            chunk_type_counts = df['CHUNK_TYPE'].value_counts()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Full Reviews", chunk_type_counts.get('full_review', 0))
            with col2:
                st.metric("Split Reviews", chunk_type_counts.get('chunked_review', 0))
        
        with st.expander(":material/description: Preview Chunks"):
            st.dataframe(df.head(10), use_container_width=True)
    
    # Generate embeddings
    with st.container(border=True):
        st.subheader(":material/looks_two: Generate Embeddings")
        
        st.info("""
        **What happens here:**
        - Each review chunk is converted to a 768-dimensional vector
        - Embeddings are stored in Snowflake for semantic search
        - Enables finding relevant reviews based on meaning, not just keywords
        
        **For Customer Reviews**: This allows your RAG system to:
        - Find reviews about "durability" even if they mention "long-lasting" or "fell apart"
        - Search for "warm" products and find "toasty", "cold hands", "insulation"
        - Group similar feedback together semantically
        """)
        
        # Batch size selection
        batch_size = st.selectbox("Batch Size", [10, 25, 50, 100], index=1,
                                  help="Number of chunks to process at once")

        if st.button(":material/calculate: Generate Embeddings", type="primary", use_container_width=True):
            try:
                with st.status("Generating embeddings...", expanded=True) as status:
                    embeddings = []
                    total_chunks = len(df)
                    progress_bar = st.progress(0)
                    
                    for i in range(0, total_chunks, batch_size):
                        batch_end = min(i + batch_size, total_chunks)
                        st.write(f"Processing chunks {i+1} to {batch_end} of {total_chunks}...")
                        
                        for idx, row in df.iloc[i:batch_end].iterrows():
                            # Generate embedding using the correct function signature
                            emb = embed_text_768(model='snowflake-arctic-embed-m', text=row['CHUNK_TEXT'])
                            embeddings.append({
                                'chunk_id': row['CHUNK_ID'],
                                'embedding': emb
                            })
                        
                        # Update progress
                        progress = batch_end / total_chunks
                        progress_bar.progress(progress)
                    
                    status.update(label="Embeddings generated!", state="complete", expanded=False)
                    
                    # Store in session state
                    st.session_state.embeddings_data = embeddings
            
                    st.success(f":material/check_circle: Generated {len(embeddings)} embeddings for {len(df)} review chunks!")
                    
            except Exception as e:
                st.error(f"Error generating embeddings: {str(e)}")
    
    # View embeddings
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
        
        # Save embeddings to Snowflake
        with st.container(border=True):
            st.subheader(":material/looks_4: Save Embeddings to Snowflake")
            
            embeddings = st.session_state.embeddings_data
            
            # Embedding table name
            col1, col2 = st.columns([2, 1])
            with col1:
                st.session_state.day18_embedding_table = st.text_input(
                    "Embeddings Table Name",
                    value=st.session_state.day18_embedding_table,
                    help="Table name for storing embeddings",
                    key="day18_embedding_table_input"
                )
            
            full_embedding_table = f"{st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_embedding_table}"
            st.code(full_embedding_table, language="sql")
                
            # Check if embeddings table exists and show status
            try:
                check_query = f"""
                SELECT COUNT(*) as count 
                FROM {full_embedding_table}
                """
                result = session.sql(check_query).collect()
                current_count = result[0]['COUNT']
                
                if current_count > 0:
                    st.warning(f":material/warning: **{current_count:,} embedding(s)** currently in table `{full_embedding_table}`")
                    embedding_table_exists = True
                else:
                    st.info(":material/inbox: **Embedding table is empty** - No embeddings saved yet.")
                    embedding_table_exists = False
            except:
                st.info(":material/inbox: **Embedding table doesn't exist yet** - Will be created when you save embeddings.")
                embedding_table_exists = False
            
            # Initialize or update checkbox state based on table status
            if 'day18_replace_mode' not in st.session_state:
                st.session_state.day18_replace_mode = embedding_table_exists
            else:
                if 'day18_last_embedding_table' not in st.session_state or st.session_state.day18_last_embedding_table != full_embedding_table:
                    st.session_state.day18_replace_mode = embedding_table_exists
                    st.session_state.day18_last_embedding_table = full_embedding_table
            
            # Replace mode checkbox
            replace_mode = st.checkbox(
                f":material/sync: Replace Table Mode for `{st.session_state.day18_embedding_table}`",
                help=f"When enabled, replaces all existing embeddings in {full_embedding_table}",
                key="day18_replace_mode"
            )
            
            if replace_mode:
                st.warning("**Replace Mode Active**: Existing embeddings will be deleted before saving new ones.")
            else:
                st.success("**Append Mode Active**: New embeddings will be added to existing data.")
            
            if st.button(":material/save: Save Embeddings to Snowflake", type="primary", use_container_width=True):
                try:
                    with st.status("Saving embeddings...", expanded=True) as status:
                        # Step 1: Create or truncate embeddings table
                        st.write(":material/looks_one: Preparing table...")
                        
                        if replace_mode:
                            # Replace existing data
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
                            # Create if doesn't exist
                            create_table_sql = f"""
                            CREATE TABLE IF NOT EXISTS {full_embedding_table} (
                                CHUNK_ID NUMBER,
                                EMBEDDING VECTOR(FLOAT, 768),
                                CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                            )
                            """
                            session.sql(create_table_sql).collect()
                            st.write(":material/check_circle: Table ready")
                        
                        # Step 2: Insert embeddings
                        st.write(f":material/looks_two: Inserting {len(embeddings)} embeddings...")
                        
                        for i, emb_data in enumerate(embeddings):
                            # Get embedding list
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
                    
                    mode_msg = "replaced in" if replace_mode else "saved to"
                    st.success(f":material/check_circle: Successfully {mode_msg} `{full_embedding_table}`\n\n:material/calculate: {len(embeddings)} embedding(s) now in table")
                    
                    # Store for Day 19
                    st.session_state.embeddings_table = full_embedding_table
                    st.session_state.embeddings_database = st.session_state.day18_database
                    st.session_state.embeddings_schema = st.session_state.day18_schema
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Error saving embeddings: {str(e)}")
            
# View Saved Embeddings Section
with st.container(border=True):
    st.subheader(":material/search: View Saved Embeddings")
    
    # Check if embeddings table exists and show record count
    full_embedding_table = f"{st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_embedding_table}"
    
    try:
        count_result = session.sql(f"""
            SELECT COUNT(*) as CNT FROM {full_embedding_table}
        """).collect()
        
        if count_result:
            record_count = count_result[0]['CNT']
            if record_count > 0:
                st.warning(f":material/warning: **{record_count:,} embedding(s)** currently in table `{full_embedding_table}`")
            else:
                st.info(":material/inbox: **Embedding table is empty** - Generate and save embeddings above.")
    except:
        st.info(":material/inbox: **Embedding table doesn't exist yet** - Generate and save embeddings to create it.")
    
    query_button = st.button(":material/analytics: Query Embedding Table", type="secondary", use_container_width=True)
    
    if query_button:
        try:
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
            
            # Store in session state
            st.session_state.queried_embeddings = result_df
            st.session_state.queried_embeddings_table = full_embedding_table
            st.rerun()
            
        except Exception as e:
            st.error(f"Error querying embeddings: {str(e)}")
    
    # Display results if available in session state
    if 'queried_embeddings' in st.session_state and st.session_state.get('queried_embeddings_table') == full_embedding_table:
        emb_df = st.session_state.queried_embeddings
        
        if len(emb_df) > 0:
            st.code(full_embedding_table, language="sql")
            
            # Summary metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Embeddings", len(emb_df))
            with col2:
                st.metric("Dimensions", "768")
            
            # Display table without the EMBEDDING column for readability
            # Check which columns exist (case-insensitive)
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
            
            # View individual embedding vectors (only if EMBEDDING column exists)
            if embedding_col:
                with st.expander(":material/search: View Individual Embedding Vectors"):
                    st.write("Select a CHUNK_ID to view its full 768-dimensional embedding vector:")
                    
                    # Find CHUNK_ID column (case-insensitive)
                    chunk_id_col = None
                    for col in emb_df.columns:
                        if col.upper() == 'CHUNK_ID':
                            chunk_id_col = col
                            break
                    
                    chunk_ids = emb_df[chunk_id_col].tolist()
                    selected_chunk = st.selectbox("Select CHUNK_ID", chunk_ids, key="view_embedding_chunk")
                    
                    if st.button(":material/analytics: Load Embedding Vector", key="load_embedding_btn"):
                        # Get the embedding for selected chunk
                        selected_emb = emb_df[emb_df[chunk_id_col] == selected_chunk][embedding_col].iloc[0]
                        
                        # Store in session state
                        st.session_state.loaded_embedding = selected_emb
                        st.session_state.loaded_embedding_chunk = selected_chunk
                        st.rerun()
                    
                    # Display loaded embedding
                    if 'loaded_embedding' in st.session_state:
                        st.write(f"**Embedding Vector for CHUNK_ID {st.session_state.loaded_embedding_chunk}:**")
                        
                        # Convert to list if needed
                        emb_vector = st.session_state.loaded_embedding
                        if isinstance(emb_vector, str):
                            # If it's a string representation, parse it
                            import json
                            emb_vector = json.loads(emb_vector)
                        elif hasattr(emb_vector, 'tolist'):
                            emb_vector = emb_vector.tolist()
                        elif not isinstance(emb_vector, list):
                            emb_vector = list(emb_vector)
                        
                        st.caption(f"Vector length: {len(emb_vector)} dimensions")
                        
                        # Display the full embedding vector as code
                        st.code(emb_vector, language="python")
        else:
            st.info(":material/inbox: No embeddings found in table.")
    else:
        st.info(":material/inbox: No embeddings queried yet. Click 'Query Embedding Table' to view saved embeddings.")

st.divider()
st.caption("Day 18: Generating Embeddings for Customer Reviews | 30 Days of AI")
