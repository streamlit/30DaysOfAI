# Day 23
# LLM Evaluation & AI Observability

import streamlit as st
from snowflake.core import Root
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

# Initialize session state for run counter
if 'run_counter' not in st.session_state:
    st.session_state.run_counter = 1

# Check TruLens installation
try:
    from trulens.core.otel.instrument import instrument
    from trulens.otel.semconv.trace import SpanAttributes
    from trulens.apps.app import TruApp
    from trulens.connectors.snowflake import SnowflakeConnector
    from trulens.core.run import Run, RunConfig

    import pandas as pd
    import time
    trulens_available = True
except ImportError as e:
    trulens_available = False
    trulens_error = str(e)

st.title(":material/analytics: LLM Evaluation & AI Observability")
st.write("Evaluate your RAG application quality using TruLens and Snowflake AI Observability.")

# Info about evaluation
with st.expander("Why Evaluate LLMs?", expanded=False):
    st.markdown("""
    After building a RAG application (Days 21-22), you need to measure its quality:
    
    **The RAG Triad Metrics:**
    1. **Context Relevance** - Did we retrieve the right documents?
    2. **Groundedness** - Is the answer based on the context (no hallucinations)?
    3. **Answer Relevance** - Does the answer address the question?
    
    **TruLens:** An open-source library that integrates with Snowflake AI Observability to automatically evaluate LLM applications, track experiments, and store results for comparison.
    
    Learn more: [Snowflake AI Observability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability)
    """)

# Display TruLens status
if trulens_available:
    st.success(":material/check_circle: TruLens packages are installed and ready!")
else:
    st.error(f":material/cancel: TruLens packages not found: {trulens_error}")
    st.info("""
    **Required packages:**
    - `trulens-core`
    - `trulens-providers-cortex`
    - `trulens-connectors-snowflake`
    
    Add these to your Streamlit app's package configuration to enable TruLens evaluations.
    """)

# Configuration
with st.sidebar:
    st.header(":material/settings: Configuration")
    
    with st.expander("Search Service", expanded=True):
        search_service = st.text_input(
            "Cortex Search Service:",
            value="RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH",
            help="Format: database.schema.service_name (created in Day 19)"
        )
    
    with st.expander("Location", expanded=False):
        obs_database = st.text_input(
            "Database:",
            value="RAG_DB",
            help="Database for storing evaluation results"
        )
        
        obs_schema = st.text_input(
            "Schema:",
            value="RAG_SCHEMA",
            help="Schema for storing evaluation results"
        )
    
    num_results = st.slider("Results to retrieve:", 1, 5, 3)

    # Stage Status - create early like day25
    with st.expander("Stage Status", expanded=False):
        full_stage_name = f"{obs_database}.{obs_schema}.TRULENS_STAGE"
        
        try:
            # Check if stage exists
            stage_info = session.sql(f"SHOW STAGES LIKE 'TRULENS_STAGE' IN SCHEMA {obs_database}.{obs_schema}").collect()
            
            if stage_info:
                # Stage exists - drop and recreate to ensure correct configuration
                st.info(f":material/autorenew: Recreating stage with server-side encryption...")
                session.sql(f"DROP STAGE IF EXISTS {full_stage_name}").collect()
            
            # Create stage with server-side encryption
            session.sql(f"""
            CREATE STAGE {full_stage_name}
                DIRECTORY = ( ENABLE = true )
                ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
            """).collect()
            st.success(f":material/check_box: TruLens stage ready")
            
        except Exception as e:
            st.error(f":material/cancel: Could not create stage: {str(e)}")
            
            with st.expander(":material/build: Manual Fix"):
                st.code(f"""
DROP STAGE IF EXISTS {full_stage_name};
CREATE STAGE {full_stage_name}
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );
                """, language="sql")
        
        if st.button(":material/autorenew: Recreate Stage", help="Drop and recreate the stage"):
            try:
                session.sql(f"DROP STAGE IF EXISTS {full_stage_name}").collect()
                session.sql(f"""
                CREATE STAGE {full_stage_name}
                    DIRECTORY = ( ENABLE = true )
                    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
                """).collect()
                st.success(f":material/check_circle: Stage recreated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to recreate stage: {str(e)}")

# TruLens Evaluation  
with st.container(border=True):
    st.markdown("##### :material/settings_suggest: Evaluation Configuration")
    
    app_name = st.text_input(
        "App Name:",
        value="customer_review_rag",
        help="Name for your RAG application"
    )
    
    app_version = st.text_input(
        "App Version:",
        value=f"v{st.session_state.run_counter}",
        help="Version identifier for this experiment"
    )
    
    rag_model = st.selectbox(
        "RAG Model:",
        ["claude-3-5-sonnet", "mixtral-8x7b", "llama3-70b", "llama3.1-8b"],
        help="Model for generating answers",
        key="trulens_model"
    )
    
    st.markdown("##### :material/dataset: Test Questions")
    test_questions_text = st.text_area(
        "Questions (one per line):",
        value="What do customers say about thermal gloves?\nAre there any durability complaints?\nWhich products get the best reviews?",
        height=150,
        help="Enter questions to evaluate"
    )
    
    run_evaluation = st.button(":material/science: Run TruLens Evaluation", type="primary")

if run_evaluation:
    # Parse questions
    test_questions = [q.strip() for q in test_questions_text.split('\n') if q.strip()]
    
    if not test_questions:
        st.error("Please enter at least one question.")
        st.stop()
    
    try:
        with st.status("Running TruLens evaluation...", expanded=True) as status:
            st.write(":orange[:material/check:] Importing required libraries...")
            
            from trulens.apps.app import TruApp
            from trulens.connectors.snowflake import SnowflakeConnector
            from trulens.core.run import Run, RunConfig
            import pandas as pd
            import time
            
            st.write(":orange[:material/check:] Preparing test dataset...")
            
            # Set database and schema context (required for TruLens)
            session.use_database(obs_database)
            session.use_schema(obs_schema)
            
            # Create a DataFrame from test questions
            test_data = []
            for idx, question in enumerate(test_questions):
                test_data.append({
                    "QUERY": question,
                    "QUERY_ID": idx + 1
                })
            
            test_df = pd.DataFrame(test_data)
            
            # Save to Snowflake table for TruLens
            test_snowpark_df = session.create_dataframe(test_df)
            dataset_table = "CUSTOMER_REVIEW_TEST_QUESTIONS"
            
            # Drop table if exists and recreate
            try:
                session.sql(f"DROP TABLE IF EXISTS {dataset_table}").collect()
            except:
                pass
            
            test_snowpark_df.write.mode("overwrite").save_as_table(dataset_table)
            
            st.write(f":orange[:material/check:] Created dataset table: `{obs_database}.{obs_schema}.{dataset_table}`")
            
            st.write(":orange[:material/check:] Setting up RAG application...")
            
            # Define RAG class with instrumented methods (following the working pattern)
            class CustomerReviewRAG:
                def __init__(self, snowpark_session):
                    self.session = snowpark_session
                    self.search_service = search_service
                    self.num_results = num_results
                    self.model = rag_model
                
                @instrument(
                    span_type=SpanAttributes.SpanType.RETRIEVAL,
                    attributes={
                        SpanAttributes.RETRIEVAL.QUERY_TEXT: "query",
                        SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS: "return",
                    }
                )
                def retrieve_context(self, query: str) -> list:  # Return LIST, not str
                    """Retrieve context from Cortex Search."""
                    root = Root(self.session)
                    parts = self.search_service.split(".")
                    svc = root.databases[parts[0]].schemas[parts[1]].cortex_search_services[parts[2]]
                    results = svc.search(query=query, columns=["CHUNK_TEXT"], limit=self.num_results)
                    # Return as LIST of strings
                    return [r["CHUNK_TEXT"] for r in results.results]
                
                @instrument(span_type=SpanAttributes.SpanType.GENERATION)
                def generate_completion(self, query: str, context: list) -> str:
                    """Generate answer using LLM."""
                    context_str = "\n\n".join(context)  # Join here instead
                    prompt = f"""Based on this context from customer reviews:
            
            {context_str}
            
            Question: {query}
            
            Provide a helpful answer based on the context above:"""
                    
                    prompt_escaped = prompt.replace("'", "''")
                    response = self.session.sql(
                        f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{self.model}', '{prompt_escaped}')"
                    ).collect()[0][0]
                    return response.strip()
                
                @instrument(
                    span_type=SpanAttributes.SpanType.RECORD_ROOT,
                    attributes={
                        SpanAttributes.RECORD_ROOT.INPUT: "query",
                        SpanAttributes.RECORD_ROOT.OUTPUT: "return",
                    }
                )
                def query(self, query: str) -> str:
                    """Main RAG query method."""
                    context = self.retrieve_context(query)  # Now returns list
                    answer = self.generate_completion(query, context)
                    return answer
            
            st.write(":orange[:material/check:] Registering app with TruLens...")
            
            # Create fresh TruLens session for each run (don't persist across reruns)
            from trulens.core import TruSession
            
            # Always clear singleton to ensure fresh session
            if hasattr(TruSession, '_singleton_instances'):
                TruSession._singleton_instances.clear()
            
            # Create new connector and session
            tru_connector = SnowflakeConnector(snowpark_session=session)
            tru_session = TruSession(connector=tru_connector)
            
            # Create RAG app instance
            rag_app = CustomerReviewRAG(session)
            
            # Register the RAG app with unique version for each run
            unique_app_version = f"{app_version}_{st.session_state.run_counter}"
            
            tru_rag = TruApp(
                app=rag_app,
                app_name=app_name,
                app_version=unique_app_version,
                connector=tru_connector,
                main_method=rag_app.query
            )
            
            st.write(f":orange[:material/check:] Running evaluation on {len(test_questions)} questions...")
            
            # Configure run
            run_config = RunConfig(
                run_name=f"{unique_app_version}_{int(time.time())}",
                dataset_name=dataset_table,
                description=f"Customer review RAG evaluation using {rag_model}",
                label="customer_review_eval",
                source_type="TABLE",
                dataset_spec={
                    "input": "QUERY",
                },
            )
            
            # Add run to TruLens
            run: Run = tru_rag.add_run(run_config=run_config)
            
            # Start the run - this executes all queries in batch
            run.start()
            
            st.write(":orange[:material/check:] Waiting for all invocations to complete...")
            
            # Wait for invocations to complete
            max_wait = 180  # 3 minutes
            start_time = time.time()
            while run.get_status() != "INVOCATION_COMPLETED":
                if time.time() - start_time > max_wait:
                    st.warning("Run taking longer than expected, continuing...")
                    break
                time.sleep(3)
            
            st.write(":orange[:material/check:] Computing RAG Triad metrics...")
            
            # Compute metrics on the run
            try:
                run.compute_metrics([
                    "answer_relevance",
                    "context_relevance",
                    "groundedness",
                ])
                metrics_computed = True
                st.write(":orange[:material/check:] Metrics computed successfully!")
            except Exception as e:
                st.warning(f"Metrics computation: {str(e)}")
                metrics_computed = False
            
            st.write(":orange[:material/check: Evaluation complete!")
            status.update(label="Evaluation complete", state="complete")
            
            # Increment run counter
            st.session_state.run_counter += 1
        
        # Display results
        with st.container(border=True):
            st.markdown("#### :material/analytics: Evaluation Results")
            
            st.success(f"""
:material/check: **Evaluation Run Complete!**

**Run Details:**
- App Name: **{app_name}**
- App Version: **{unique_app_version}**
- Run Name: **{run_config.run_name}**
- Questions Evaluated: **{len(test_questions)}**
- Model: **{rag_model}**

**View Results in Snowsight:**
Navigate to: **AI & ML → Evaluations → {app_name}**
            """)
            
    except Exception as e:
        st.error(f"Error during evaluation: {str(e)}")
        
        with st.expander("See full error details"):
            st.exception(e)
        
        st.info("""
        **Troubleshooting:**
        - Ensure required packages are installed (see requirements below)
        - Check that your Cortex Search service is accessible
        - Verify database and schema permissions
        - Make sure you have privileges to create tables in the observability schema
        """)
        
        with st.expander(":material/code: Required packages"):
            st.code("""# Add to pyproject.toml or install in environment:
trulens-connectors-snowflake>=2.5.0
snowflake-snowpark-python>=1.18.0,<2.0
pandas>=1.5.0""", language="txt")

# Footer
st.divider()
st.caption("Day 23: LLM Evaluation & AI Observability | 30 Days of AI with Streamlit")

