# Day 21
# RAG with Cortex Search

import streamlit as st

st.title(":material/link: RAG with Cortex Search")
st.write("Combine search results with LLM generation for grounded answers.")

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

st.divider()
st.subheader(":material/menu_book: How RAG Works")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("**:material/looks_one: Retrieve**")
        st.markdown("""
        Cortex Search finds 
        relevant document 
        chunks based on 
        your question.
        """)

with col2:
    with st.container(border=True):
        st.markdown("**:material/looks_two: Augment**")
        st.markdown("""
        Retrieved chunks 
        are added to the 
        prompt as context 
        for the LLM.
        """)

with col3:
    with st.container(border=True):
        st.markdown("**:material/looks_3: Generate**")
        st.markdown("""
        The LLM generates 
        an answer grounded 
        in the retrieved 
        documents.
        """)

st.divider()

# Sidebar configuration
with st.sidebar:
    st.header(":material/settings: Settings")
    
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
            "Search Service:",
            value=default_service,
            placeholder="database.schema.service_name",
            help="Full path to your Cortex Search service"
        )
    
    num_chunks = st.slider("Context chunks:", 1, 10, 3,
                           help="Number of relevant chunks to retrieve")
    
    model = st.selectbox(
        "LLM Model:",
        ["claude-3-5-sonnet", "mistral-large", "llama3.1-8b"],
        help="Model to generate the answer"
    )
    
    show_context = st.checkbox("Show retrieved context", value=True)

# Main interface
st.subheader(":material/help: Ask a Question")

question = st.text_input(
    "Your question:",
    value="Are the thermal gloves warm enough for winter?",
    placeholder="e.g., Which products have durability issues?"
)

if st.button(":material/search: Search & Answer", type="primary"):
    if question and search_service:
        with st.status("Processing...", expanded=True) as status:
            
            # Step 1: Retrieve context from Cortex Search
            st.write(":material/search: **Step 1:** Searching documents...")
            
            try:
                from snowflake.core import Root
                
                root = Root(session)
                parts = search_service.split(".")
                
                if len(parts) != 3:
                    st.error("Service path must be in format: database.schema.service_name")
                    st.stop()
                
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
                
                st.write(f"   :material/check_circle: Found {len(context_chunks)} relevant chunks")
                
                # Step 2: Generate answer with LLM
                st.write(":material/smart_toy: **Step 2:** Generating answer...")
                
                rag_prompt = f"""You are a helpful assistant. Answer the user's question based ONLY on the provided context.
If the context doesn't contain enough information to answer, say "I don't have enough information to answer that based on the available documents."

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {question}

Provide a clear, accurate answer based on the context. If you use information from the context, mention it naturally."""
                
                # Call LLM
                response_sql = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{model}',
                    '{rag_prompt.replace("'", "''")}'
                ) as response
                """
                
                response = session.sql(response_sql).collect()[0][0]
                
                st.write("   :material/check_circle: Answer generated")
                status.update(label="Complete!", state="complete", expanded=True)
                
                # Display results
                st.divider()
                
                st.subheader(":material/lightbulb: Answer")
                with st.container(border=True):
                    st.markdown(response)
                
                if show_context:
                    st.subheader(":material/library_books: Retrieved Context")
                    st.caption(f"Used {len(context_chunks)} chunks from customer reviews")
                    for i, (chunk, source) in enumerate(zip(context_chunks, sources), 1):
                        with st.expander(f":material/description: Chunk {i} - {source}"):
                            st.write(chunk)
                
            except Exception as e:
                status.update(label="Error", state="error")
                st.error(f"Error: {str(e)}")
                st.info(":material/lightbulb: **Troubleshooting:**\n- Make sure the search service exists (check Day 19)\n- Verify the service has finished indexing\n- Check your permissions")
    else:
        st.warning(":material/warning: Please enter a question and configure a search service.")
        st.info(":material/lightbulb: **Need a search service?**\n- Complete Day 19 to create `CUSTOMER_REVIEW_SEARCH`\n- The service will automatically appear in the dropdown above")

st.divider()
st.caption("Day 21: RAG with Cortex Search | 30 Days of AI")
