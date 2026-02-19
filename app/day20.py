# Day 20
# Querying Cortex Search

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

# Input Container
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

    st.divider()

    # Search query input
    query = st.text_input(
        "Enter your search query:",
        value="warm thermal gloves",
        placeholder="e.g., durability issues, comfortable helmet"
    )

    num_results = st.slider("Number of results:", 1, 20, 5)
    
    search_clicked = st.button(":material/search: Search", type="primary", use_container_width=True)

# Output Container
with st.container(border=True):
    st.subheader(":material/analytics: Search Results")
    
    if search_clicked:
        if query and search_service:
            try:
                root = Root(session)
                parts = search_service.split(".")
                
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
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info(":material/lightbulb: **Troubleshooting:**\n- Make sure the search service exists (check Day 19)\n- Verify the service has finished indexing\n- Check that you have access permissions")
        else:
            st.warning(":material/warning: Please enter a query and configure a search service.")
            st.info(":material/lightbulb: **Need a search service?**\n- Complete Day 19 to create `CUSTOMER_REVIEW_SEARCH`\n- The service will automatically appear in the dropdown above")
    else:
        st.info(":material/arrow_upward: Configure your search service and enter a query above, then click Search to see results.")

st.divider()
st.caption("Day 20: Querying Cortex Search | 30 Days of AI")
