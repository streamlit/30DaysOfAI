For today's challenge, our goal is to **evaluate the quality of your RAG application** using **TruLens** and Snowflake's AI Observability framework. After building a complete RAG system in Days 21-22, it's critical to measure whether it's producing accurate, grounded, and relevant answers. We'll use TruLens to automatically evaluate your RAG application using the **RAG Triad** metrics (Context Relevance, Groundedness, Answer Relevance). The app provides an interactive interface to configure evaluation settings, run evaluations, and view results directly in Snowsight.

> :material/warning: **Prerequisite:** You need TruLens packages installed and a Cortex Search service from Day 19.

---

### :material/settings: How It Works: Step-by-Step

Let's break down what each part of the code does.

#### 1. The RAG Triad: Three Essential Metrics

According to [Snowflake's RAG evaluation guide](https://www.snowflake.com/en/engineering-blog/eval-guided-optimization-llm-judges-rag-triad/), evaluating RAG requires measuring three dimensions:

| Metric | Question | Why It Matters |
|--------|----------|----------------|
| **Context Relevance** | Did we retrieve relevant documents? | Bad retrieval → bad answers |
| **Groundedness** | Is the answer based on context? | Prevents hallucinations |
| **Answer Relevance** | Does it answer the question? | Ensures usefulness |

* **Context Relevance**: Measures whether the search system (Cortex Search) retrieved documents that are actually related to the user's question. A low score means your search needs tuning.
* **Groundedness**: Checks if the LLM's answer comes from the provided context or if it's making things up (hallucinating). High groundedness = no hallucinations.
* **Answer Relevance**: Evaluates whether the final answer actually addresses what the user asked. You can have great context and grounding but still give an irrelevant answer.

#### 2. Package Availability Check and UI Setup

```python
import streamlit as st

# Check TruLens installation
try:
    from trulens.connectors.snowflake import SnowflakeConnector
    from trulens.core.run import Run, RunConfig
    from trulens.core import TruSession
    from trulens.core.otel.instrument import instrument
    import pandas as pd
    import time
    trulens_available = True
except ImportError as e:
    trulens_available = False
    trulens_error = str(e)

st.title(":material/analytics: LLM Evaluation & AI Observability")
st.write("Evaluate your RAG application quality using TruLens and Snowflake AI Observability.")

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
```

* **Import check**: Verifies all required TruLens packages are installed before proceeding
* **User feedback**: Shows clear status message with required packages if missing
* **Graceful degradation**: Allows app to load even if packages are missing (shows instructions instead)

#### 3. Sidebar Configuration and Stage Setup

```python
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
        obs_database = st.text_input("Database:", value="RAG_DB")
        obs_schema = st.text_input("Schema:", value="RAG_SCHEMA")
    
    num_results = st.slider("Results to retrieve:", 1, 5, 3)
    
    # Stage Status - create early
    with st.expander("Stage Status", expanded=False):
        full_stage_name = f"{obs_database}.{obs_schema}.TRULENS_STAGE"
        
        try:
            # Check if stage exists
            stage_info = session.sql(f"SHOW STAGES LIKE 'TRULENS_STAGE' IN SCHEMA {obs_database}.{obs_schema}").collect()
            
            if stage_info:
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
```

* **Organized configuration**: Uses expanders to group related settings
* **Default values**: Pre-fills with values from Day 19 setup
* **Automatic stage creation**: Creates the required TruLens stage with proper encryption on page load
* **Stage validation**: Checks and recreates stage to ensure correct configuration
* **Manual fix option**: Provides SQL code if automatic creation fails

#### 4. Evaluation Configuration UI

```python
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
        help="Model for generating answers"
    )
    
    st.markdown("##### :material/dataset: Test Questions")
    test_questions_text = st.text_area(
        "Questions (one per line):",
        value="What do customers say about thermal gloves?\nAre there any durability complaints?\nWhich products get the best reviews?",
        height=150
    )
    
    run_evaluation = st.button(":material/science: Run TruLens Evaluation", type="primary")
```

* **Run counter**: Automatically increments version numbers for each evaluation run
* **Model selection**: Choose which Cortex LLM to evaluate
* **Flexible questions**: Edit test questions directly in the UI
* **One-line format**: Questions separated by newlines for easy editing

#### 5. What is TruLens?

TruLens is an open-source library that integrates with Snowflake AI Observability to:
- Automatically trace and evaluate LLM applications
- Compute RAG Triad metrics automatically
- Store results in Snowflake for analysis and comparison
- Track experiments over time

#### 6. Instrumenting Your RAG Application

The first step is to create an instrumented RAG class that TruLens can trace:

```python
from trulens.core.otel.instrument import instrument

class CustomerReviewRAG:
    def __init__(self, snowpark_session):
        self.session = snowpark_session
        self.search_service = search_service
        self.num_results = num_results
        self.model = rag_model
    
    @instrument()
    def retrieve_context(self, query: str) -> str:
        """Retrieve context from Cortex Search."""
        root = Root(self.session)
        parts = self.search_service.split(".")
        svc = root.databases[parts[0]].schemas[parts[1]].cortex_search_services[parts[2]]
        results = svc.search(query=query, columns=["CHUNK_TEXT"], limit=self.num_results)
        context = "\n\n".join([r["CHUNK_TEXT"] for r in results.results])
        return context
    
    @instrument()
    def generate_completion(self, query: str, context: str) -> str:
        """Generate answer using LLM."""
        prompt = f"""Based on this context from customer reviews:

{context}

Question: {query}

Provide a helpful answer based on the context above:"""
        
        prompt_escaped = prompt.replace("'", "''")
        response = self.session.sql(
            f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{self.model}', '{prompt_escaped}')"
        ).collect()[0][0]
        return response.strip()
    
    @instrument()
    def query(self, query: str) -> str:
        """Main RAG query method."""
        context = self.retrieve_context(query)
        answer = self.generate_completion(query, context)
        return answer
```

* **`@instrument()` decorators**: Tell TruLens to trace these methods
* **Separation of concerns**: Split retrieval and generation into separate methods for better tracing
* **Main entry point**: The `query()` method orchestrates the full RAG pipeline

#### 7. Setting Up TruLens Session

```python
from trulens.core import TruSession
from trulens.connectors.snowflake import SnowflakeConnector

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

tru_rag = tru_session.App(
    rag_app,
    app_name=app_name,
    app_version=unique_app_version,
    main_method=rag_app.query
)
```

* **Singleton clearing**: Prevents conflicts with previous TruLens sessions in Streamlit reruns
* **Fresh session**: Creates a new TruSession for each evaluation run
* **SnowflakeConnector**: Connects TruLens to your Snowflake session
* **Unique versioning**: Combines user version with run counter to prevent collisions
* **App registration**: Register your RAG app with metadata (name, version)
* **main_method**: Specify which method TruLens should call for each query

#### 8. Creating Test Dataset

```python
# Parse questions from text area
test_questions = [q.strip() for q in test_questions_text.split('\n') if q.strip()]

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
session.sql(f"DROP TABLE IF EXISTS {dataset_table}").collect()
test_snowpark_df.write.mode("overwrite").save_as_table(dataset_table)
```

* **Parse from UI**: Splits user-entered text area content by newlines
* **Query IDs**: Adds unique identifiers for tracking
* **Database context**: Sets the working database/schema for table creation
* **Snowflake table**: TruLens reads test data from Snowflake tables (not in-memory DataFrames)
* **Clean slate**: Drops and recreates table to avoid conflicts
* **Reusable dataset**: You can reference this table in future evaluation runs

#### 9. Configuring and Running Evaluation

```python
from trulens.core.run import Run, RunConfig
import time

# Configure the evaluation run
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

# Start the evaluation
run.start()

# Show progress and generate answers
generated_answers = {}
for idx, question in enumerate(test_questions, 1):
    st.write(f"  :orange[:material/check:] Question {idx}/{len(test_questions)}: {question[:60]}...")
    answer = rag_app.query(question)
    generated_answers[question] = answer

# Wait for invocations to complete
max_wait = 180  # 3 minutes
start_time = time.time()
while run.get_status() != "INVOCATION_COMPLETED":
    if time.time() - start_time > max_wait:
        st.warning("Run taking longer than expected, continuing...")
        break
    time.sleep(3)

# Compute RAG Triad metrics
run.compute_metrics([
    "answer_relevance",
    "context_relevance",
    "groundedness",
])

# Show completion message
st.write(":orange[:material/check:] Evaluation complete!")
```

* **Unique run names**: Uses timestamp to ensure no conflicts between runs
* **RunConfig**: Specifies what to evaluate and how
* **Progress tracking**: Shows which question is being processed in real-time
* **Answer capture**: Stores generated answers for display
* **Batch processing**: All questions are processed automatically
* **Timeout protection**: Prevents infinite waiting if something goes wrong
* **Metric computation**: TruLens calculates RAG Triad scores after all queries complete
* **Completion message**: Displays a clear indicator when evaluation finishes

#### 10. Displaying Results

```python
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
    
    # Show generated answers
    with st.expander("Generated Answers", expanded=True):
        for idx, question in enumerate(test_questions, 1):
            st.markdown(f"**Question {idx}:** {question}")
            st.info(generated_answers.get(question, "No answer generated"))
            if idx < len(test_questions):
                st.markdown("---")
```

* **Success summary**: Shows key details about the completed evaluation
* **Snowsight navigation**: Clear instructions on where to view detailed RAG Triad metrics
* **Generated answers**: Displays all Q&A pairs for immediate review in Streamlit
* **Expandable section**: Keeps the UI clean with collapsible answers
* **Separator**: Adds dividers between Q&A pairs for better readability
* **Transparency**: Users can see exactly what the RAG system generated before viewing metrics

#### 11. Accessing Evaluation Results in Snowsight

After the app shows the success message that the evaluation is complete, follow these steps to view detailed metrics:

**Step-by-Step Instructions:**

1. **Open Snowsight** and log in to your Snowflake account

2. **Navigate to the Evaluations page:**
   - In the left sidebar, click on **AI & ML**
   - Then click on **Evaluations**
   - Or use this direct link: [Snowflake AI Evaluations](https://app.snowflake.com/_deeplink/#/ai-evaluations)

3. **Find your evaluation:**
   - In the displayed data table, look for the **Name** column
   - Find **CUSTOMER_REVIEW_RAG** (or your custom app name if you changed it)
   - Click on the app name to open the evaluation details

4. **View detailed results:**
   - **RAG Triad scores** for each question:
     - Context Relevance (retrieval quality)
     - Groundedness (hallucination detection)
     - Answer Relevance (answer quality)
   - **Response metrics**: Length and duration for each query
   - **Detailed traces**: Step-by-step view of retrieval and generation
   - **Version comparison**: Compare metrics across multiple runs/versions
   - **Individual query details**: Click on any question to see its full trace

**What to look for:**
- Scores range from 0 to 1 (higher is better)
- Scores below 0.7 indicate areas that need improvement
- Compare scores across different versions to track improvements

---

### :material/adjust: Key Concepts

**Why Use TruLens?**
- **Automated evaluation**: No manual scoring required
- **Production-ready**: Scales to thousands of evaluations
- **Integrated storage**: Results stored in Snowflake automatically
- **Experiment tracking**: Compare different models, prompts, and configurations
- **Detailed tracing**: See exactly what happened at each step

**TruLens vs Manual Evaluation:**

| Aspect | TruLens | Manual LLM-as-a-Judge |
|--------|---------|----------------------|
| Setup | Requires instrumentation | Custom prompts needed |
| Metrics | RAG Triad built-in | Must define evaluation prompts |
| Storage | Automatic in Snowflake | Must implement yourself |
| Tracing | Automatic method tracking | Manual logging required |
| Comparison | Built-in UI in Snowsight | Must build dashboards |

**Best Practices:**
- **Unique app versions**: Use version numbers to track experiments
- **Representative questions**: Include edge cases in your test set
- **Regular evaluation**: Run before deploying changes
- **Analyze patterns**: Look for consistently low-scoring question types
- **Iterate based on metrics**: Use scores to guide improvements

**When to Run Evaluations:**
- **Development**: After changing prompts, models, or retrieval settings
- **Pre-deployment**: Before releasing to production
- **Regression testing**: Ensure quality doesn't degrade
- **A/B testing**: Compare different configurations

**Interpreting RAG Triad Scores:**
- **Context Relevance < 0.7**: Your search quality needs improvement
  - Solution: Tune chunk size, improve embeddings, or adjust search parameters
- **Groundedness < 0.7**: The LLM is hallucinating or extrapolating
  - Solution: Add stronger grounding instructions to your prompt
- **Answer Relevance < 0.7**: The answer doesn't address the question
  - Solution: Refine prompt instructions or provide examples

---

### :material/library_books: Key Technical Concepts

**TruLens Architecture:**
1. **Instrumentation**: `@instrument()` decorators trace method calls
2. **Session Management**: `TruSession` manages the evaluation lifecycle
3. **App Registration**: Register your application with metadata
4. **Dataset Specification**: Define input/output columns
5. **Run Configuration**: Specify evaluation parameters
6. **Metric Computation**: Calculate RAG Triad after query completion

**Required Dependencies:**

For **pyproject.toml**:
```toml
[project]
dependencies = [
    "trulens-core>=1.0.0",
    "trulens-connectors-snowflake>=1.0.0",
    "trulens-providers-cortex>=1.0.0",
    "snowflake-snowpark-python>=1.18.0,<2.0",
    "pandas>=1.5.0"
]
```

Or for **requirements.txt**:
```
trulens-core>=1.0.0
trulens-connectors-snowflake>=1.0.0
trulens-providers-cortex>=1.0.0
snowflake-snowpark-python>=1.18.0,<2.0
pandas>=1.5.0
```

**TruLens Package Breakdown:**
- `trulens-core` - Core TruLens functionality (TruSession, @instrument decorator)
- `trulens-connectors-snowflake` - Snowflake connector for storing evaluation results
- `trulens-providers-cortex` - Cortex LLM provider for evaluation metrics
- `pandas` - Required for DataFrame operations with test datasets

**Snowflake Stage Requirements:**
TruLens requires a stage with:
- Server-side encryption: `ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )`
- Directory table enabled: `DIRECTORY = ( ENABLE = true )`

```sql
CREATE STAGE TRULENS_STAGE
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );
```

**Session State Management:**
To prevent conflicts across Streamlit reruns:
```python
# Clear TruSession singleton before each run
from trulens.core import TruSession
if hasattr(TruSession, '_singleton_instances'):
    TruSession._singleton_instances.clear()

# Use run counter for unique versions
st.session_state.run_counter = st.session_state.get('run_counter', 1)
app_version = f"v{st.session_state.run_counter}"
st.session_state.run_counter += 1
```

**Production Tips:**
- Store evaluation results for historical analysis
- Set up alerts for quality degradation
- Run evaluations on a schedule (e.g., daily)
- Include production queries in your test set
- Compare metrics across app versions
- Use evaluation results to prioritize improvements

---

### :material/library_books: Resources

- [Snowflake AI Observability Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability)
- [AI Observability Tutorial](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability/tutorial)
- [Getting Started with AI Observability](https://github.com/Snowflake-Labs/sfguide-getting-started-with-ai-observability)
- [RAG Triad Benchmarking Blog](https://www.snowflake.com/en/engineering-blog/eval-guided-optimization-llm-judges-rag-triad/)
- [TruLens Documentation](https://www.trulens.org/)
