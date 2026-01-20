# Day 19
# Creating Cortex Search for Customer Reviews

import streamlit as st
from snowflake.core import Root
import pandas as pd

st.title(":material/search: Cortex Search for Customer Reviews")
st.write("Create a semantic search service for the customer reviews processed in Days 16-18.")

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
    # Check if we have embeddings from Day 18
    if 'embeddings_database' in st.session_state:
        st.session_state.day19_database = st.session_state.embeddings_database
        st.session_state.day19_schema = st.session_state.embeddings_schema
    else:
        st.session_state.day19_database = "RAG_DB"
        st.session_state.day19_schema = "RAG_SCHEMA"

# Database Configuration
with st.container(border=True):
    st.subheader(":material/analytics: Database Configuration")
    
    # Database configuration
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.day19_database = st.text_input(
            "Database", 
            value=st.session_state.day19_database, 
            key="day19_db_input"
        )
    with col2:
        st.session_state.day19_schema = st.text_input(
            "Schema", 
            value=st.session_state.day19_schema, 
            key="day19_schema_input"
        )
    
    st.info(f":material/location_on: Using: `{st.session_state.day19_database}.{st.session_state.day19_schema}`")
    st.caption(":material/lightbulb: Make sure your REVIEW_CHUNKS table exists in this location")

# Step 1: Prepare the Data View
with st.container(border=True):
    st.subheader("Step 1: Prepare the Data View")
    
    st.markdown("""
    We'll create a view that combines review chunks with their metadata for searching:
    """)
    
    st.code(f"""
-- Create a searchable view of customer reviews
CREATE OR REPLACE VIEW {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW AS
SELECT 
    rc.CHUNK_ID,
    rc.CHUNK_TEXT,              -- The review text (searchable)
    rc.FILE_NAME,
    rc.DOC_ID,
    rc.CHUNK_TYPE
FROM {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_CHUNKS rc
WHERE rc.CHUNK_TEXT IS NOT NULL;
""", language="sql")
    
    # Button to create view
    if st.button(":material/build: Create Search View", type="primary", use_container_width=True):
        try:
            create_view_sql = f"""
            CREATE OR REPLACE VIEW {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW AS
            SELECT 
                rc.CHUNK_ID,
                rc.CHUNK_TEXT,
                rc.FILE_NAME,
                rc.DOC_ID,
                rc.CHUNK_TYPE
            FROM {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_CHUNKS rc
            WHERE rc.CHUNK_TEXT IS NOT NULL
            """
            session.sql(create_view_sql).collect()
            st.success(f":material/check_circle: Created view: `{st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW`")
        except Exception as e:
            st.error(f"Error creating view: {str(e)}")

# Step 2: Create the Cortex Search Service
with st.container(border=True):
    st.subheader("Step 2: Create the Cortex Search Service")
    
    st.code(f"""
CREATE OR REPLACE CORTEX SEARCH SERVICE {st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH
    ON CHUNK_TEXT                        -- Search on review text
    ATTRIBUTES FILE_NAME, CHUNK_TYPE     -- Return these as metadata
    WAREHOUSE = COMPUTE_WH               -- Replace with your warehouse
    TARGET_LAG = '1 hour'                -- Refresh frequency
AS (
    SELECT 
        CHUNK_TEXT,
        FILE_NAME,
        CHUNK_TYPE,
        CHUNK_ID
    FROM {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW
);
""", language="sql")
    
    st.info("""
:material/lightbulb: **Key Parameters:**
    - **ON**: The text column to make searchable (review text)
    - **ATTRIBUTES**: Additional columns to include in results (file name, chunk type)
    - **TARGET_LAG**: How often to refresh the index
    - **WAREHOUSE**: The compute warehouse for indexing
    """)
    
    # Warehouse selection
    warehouse = st.text_input("Warehouse Name", value="COMPUTE_WH", 
                              help="Enter your Snowflake warehouse name")
    
    # Button to create search service
    if st.button(":material/rocket_launch: Create Search Service", type="primary", use_container_width=True):
        try:
            with st.status("Creating Cortex Search Service...", expanded=True) as status:
                st.write(":material/looks_one: Creating service...")
                create_service_sql = f"""
                CREATE OR REPLACE CORTEX SEARCH SERVICE {st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH
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
                    FROM {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW
                )
                """
                session.sql(create_service_sql).collect()

                st.write(":material/looks_two: Waiting for indexing to complete...")
                st.caption("This may take a few minutes for 100 reviews...")
                
                status.update(label=":material/check_circle: Search service created!", state="complete", expanded=False)
            
            st.success(f":material/check_circle: Created: `{st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH`")
            st.session_state.search_service = f"{st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH"
            
            st.balloons()
            
        except Exception as e:
            st.error(f"Error creating search service: {str(e)}")
            st.info(":material/lightbulb: Make sure:\n- Warehouse name is correct\n- You have CREATE CORTEX SEARCH SERVICE privileges\n- Review chunks exist in the table")

# Step 3: Verify Search Service
with st.container(border=True):
    st.subheader("Step 3: Verify Your Search Service")
    
    st.markdown("""
    List all Cortex Search services to confirm your service was created successfully:
    """)
    
    if st.button(":material/assignment: List My Cortex Search Services", use_container_width=True):
        try:
            # Try to show services in the current database/schema
            result = session.sql(f"SHOW CORTEX SEARCH SERVICES IN SCHEMA {st.session_state.day19_database}.{st.session_state.day19_schema}").collect()
            if result:
                st.success(f":material/check_circle: Found {len(result)} Cortex Search service(s) in `{st.session_state.day19_database}.{st.session_state.day19_schema}`:")
                st.dataframe(result, use_container_width=True)
            else:
                st.info("No Cortex Search services found in this schema. Create one using the button in Step 2!")
                
                # Also try showing all services
                st.caption("Checking all schemas...")
                all_results = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
                if all_results:
                    st.warning(f"Found {len(all_results)} service(s) in other schemas:")
                    st.dataframe(all_results, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info(":material/lightbulb: If the service was just created, it may take a moment to appear. Try refreshing in a few seconds.")

st.divider()
st.caption("Day 19: Creating Cortex Search for Customer Reviews | 30 Days of AI")
