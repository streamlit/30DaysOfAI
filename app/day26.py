# Day 26
# Introduction to Cortex Agents

import streamlit as st

# Connect to Snowflake
try:
from snowflake.snowpark.context import get_active_session
session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

st.title(":material/smart_toy: Introduction to Cortex Agents")
st.write("Learn how to create Cortex Agents with Cortex Search on sales conversations.")

st.session_state.setdefault("agent_created", False)

# Sidebar config
with st.sidebar:
    st.header(":material/settings: Configuration")
    db_name, schema_name, agent_name, search_service = "CHANINN_SALES_INTELLIGENCE", "DATA", "SALES_CONVERSATION_AGENT", "SALES_CONVERSATION_SEARCH"
    st.text_input("Database:", db_name, disabled=True)
    st.text_input("Schema:", schema_name, disabled=True)
    st.text_input("Agent Name:", agent_name, disabled=True)
    st.text_input("Search Service:", search_service, disabled=True)
    st.caption("These values match the agent configuration in Day 27")
    st.divider()
    if st.button(":material/refresh: Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# Tabs
tab0, tab1 = st.tabs([":material/database: Data Setup", ":material/build: Create Agent"])

# Data Setup Tab
with tab0:
    # Step 1: Database & Schema
    st.markdown("---\n### Step 1: Create Database & Schema")
    setup_step1 = f"""-- Create database and schema (for Days 26-28)
CREATE OR REPLACE DATABASE "{db_name}";
CREATE OR REPLACE SCHEMA "{db_name}"."{schema_name}";
USE DATABASE "{db_name}"; USE SCHEMA "{schema_name}"; USE WAREHOUSE COMPUTE_WH;"""
    st.code(setup_step1, language="sql")
    
    if st.button(":material/play_arrow: Run Step 1", key="run_step1", use_container_width=True):
        with st.spinner("Creating database and schema..."):
            try:
                for sql in [f'CREATE OR REPLACE DATABASE "{db_name}"', f'CREATE OR REPLACE SCHEMA "{db_name}"."{schema_name}"',
                           f'USE DATABASE "{db_name}"', f'USE SCHEMA "{schema_name}"', "USE WAREHOUSE COMPUTE_WH"]:
                    session.sql(sql).collect()
                st.success("✓ Step 1 complete!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Step 2: Sales Conversations
    st.markdown("---\n### Step 2: Create Sales Conversations Table")
    setup_step2 = f"""-- Create table for conversation transcripts
CREATE OR REPLACE TABLE "{db_name}"."{schema_name}".SALES_CONVERSATIONS (
    conversation_id VARCHAR, transcript_text TEXT, customer_name VARCHAR, deal_stage VARCHAR,
    sales_rep VARCHAR, conversation_date TIMESTAMP, deal_value FLOAT, product_line VARCHAR
);
-- Insert 10 comprehensive conversation transcripts (See code for full insertion)"""
    st.code(setup_step2, language="sql")
    
    if st.button(":material/play_arrow: Run Step 2", key="run_step2", use_container_width=True):
        with st.spinner("Creating table and inserting data..."):
            try:
                session.sql(f"""CREATE OR REPLACE TABLE "{db_name}"."{schema_name}".SALES_CONVERSATIONS (
                    conversation_id VARCHAR, transcript_text TEXT, customer_name VARCHAR, deal_stage VARCHAR,
                    sales_rep VARCHAR, conversation_date TIMESTAMP, deal_value FLOAT, product_line VARCHAR)""").collect()
                
                session.sql(f"""INSERT INTO "{db_name}"."{schema_name}".SALES_CONVERSATIONS 
                (conversation_id, transcript_text, customer_name, deal_stage, sales_rep, conversation_date, deal_value, product_line) VALUES
                ('CONV001', 'Initial discovery call with TechCorp Inc''s IT Director and Solutions Architect. Client showed strong interest in our enterprise solution features, particularly the automated workflow capabilities. Main discussion centered around integration timeline and complexity. They currently use Legacy System X for their core operations and expressed concerns about potential disruption during migration. Team asked detailed questions about API compatibility and data migration tools. Action items: 1) Provide detailed integration timeline document 2) Schedule technical deep-dive with their infrastructure team 3) Share case studies of similar Legacy System X migrations. Client mentioned Q2 budget allocation for digital transformation initiatives. Overall positive engagement with clear next steps.', 'TechCorp Inc', 'Discovery', 'Sarah Johnson', '2024-01-15 10:30:00', 75000, 'Enterprise Suite'),
                ('CONV002', 'Follow-up call with SmallBiz Solutions'' Operations Manager and Finance Director. Primary focus was on pricing structure and ROI timeline. They compared our Basic Package pricing with Competitor Y''s small business offering. Key discussion points included: monthly vs. annual billing options, user license limitations, and potential cost savings from process automation. Client requested detailed ROI analysis focusing on: 1) Time saved in daily operations 2) Resource allocation improvements 3) Projected efficiency gains. Budget constraints were clearly communicated - they have a maximum budget of $30K for this year. Showed interest in starting with basic package with room for potential upgrade in Q4. Need to provide competitive analysis and customized ROI calculator by next week.', 'SmallBiz Solutions', 'Negotiation', 'Mike Chen', '2024-01-16 14:45:00', 25000, 'Basic Package'),
                ('CONV003', 'Strategy session with SecureBank Ltd''s CISO and Security Operations team. Extremely positive 90-minute deep dive into our Premium Security package. Customer emphasized immediate need for implementation due to recent industry compliance updates. Our advanced security features, especially multi-factor authentication and encryption protocols, were identified as perfect fits for their requirements. Technical team was particularly impressed with our zero-trust architecture approach and real-time threat monitoring capabilities. They''ve already secured budget approval and have executive buy-in. Compliance documentation is ready for review. Action items include: finalizing implementation timeline, scheduling security audit, and preparing necessary documentation for their risk assessment team. Client ready to move forward with contract discussions.', 'SecureBank Ltd', 'Closing', 'Rachel Torres', '2024-01-17 11:20:00', 150000, 'Premium Security'),
                ('CONV004', 'Comprehensive discovery call with GrowthStart Up''s CTO and Department Heads. Team of 500+ employees across 3 continents discussed current challenges with their existing solution. Major pain points identified: system crashes during peak usage, limited cross-department reporting capabilities, and poor scalability for remote teams. Deep dive into their current workflow revealed bottlenecks in data sharing and collaboration. Technical requirements gathered for each department. Platform demo focused on scalability features and global team management capabilities. Client particularly interested in our API ecosystem and custom reporting engine. Next steps: schedule department-specific workflow analysis and prepare detailed platform migration plan.', 'GrowthStart Up', 'Discovery', 'Sarah Johnson', '2024-01-18 09:15:00', 100000, 'Enterprise Suite'),
                ('CONV005', 'In-depth demo session with DataDriven Co''s Analytics team and Business Intelligence managers. Showcase focused on advanced analytics capabilities, custom dashboard creation, and real-time data processing features. Team was particularly impressed with our machine learning integration and predictive analytics models. Competitor comparison requested specifically against Market Leader Z and Innovative Start-up X. Price point falls within their allocated budget range, but team expressed interest in multi-year commitment with corresponding discount structure. Technical questions centered around data warehouse integration and custom visualization capabilities. Action items: prepare detailed competitor feature comparison matrix and draft multi-year pricing proposals with various discount scenarios.', 'DataDriven Co', 'Demo', 'James Wilson', '2024-01-19 13:30:00', 85000, 'Analytics Pro'),
                ('CONV006', 'Extended technical deep dive with HealthTech Solutions'' IT Security team, Compliance Officer, and System Architects. Four-hour session focused on API infrastructure, data security protocols, and compliance requirements. Team raised specific concerns about HIPAA compliance, data encryption standards, and API rate limiting. Detailed discussion of our security architecture, including: end-to-end encryption, audit logging, and disaster recovery protocols. Client requires extensive documentation on compliance certifications, particularly SOC 2 and HITRUST. Security team performed initial architecture review and requested additional information about: database segregation, backup procedures, and incident response protocols. Follow-up session scheduled with their compliance team next week.', 'HealthTech Solutions', 'Technical Review', 'Rachel Torres', '2024-01-20 15:45:00', 120000, 'Premium Security'),
                ('CONV007', 'Contract review meeting with LegalEase Corp''s General Counsel, Procurement Director, and IT Manager. Detailed analysis of SLA terms, focusing on uptime guarantees and support response times. Legal team requested specific modifications to liability clauses and data handling agreements. Procurement raised questions about payment terms and service credit structure. Key discussion points included: disaster recovery commitments, data retention policies, and exit clause specifications. IT Manager confirmed technical requirements are met pending final security assessment. Agreement reached on most terms, with only SLA modifications remaining for discussion. Legal team to provide revised contract language by end of week. Overall positive session with clear path to closing.', 'LegalEase Corp', 'Negotiation', 'Mike Chen', '2024-01-21 10:00:00', 95000, 'Enterprise Suite'),
                ('CONV008', 'Quarterly business review with GlobalTrade Inc''s current implementation team and potential expansion stakeholders. Current implementation in Finance department showcasing strong adoption rates and 40% improvement in processing times. Discussion focused on expanding solution to Operations and HR departments. Users highlighted positive experiences with customer support and platform stability. Challenges identified in current usage: need for additional custom reports and increased automation in workflow processes. Expansion requirements gathered from Operations Director: inventory management integration, supplier portal access, and enhanced tracking capabilities. HR team interested in recruitment and onboarding workflow automation. Next steps: prepare department-specific implementation plans and ROI analysis for expansion.', 'GlobalTrade Inc', 'Expansion', 'James Wilson', '2024-01-22 14:20:00', 45000, 'Basic Package'),
                ('CONV009', 'Emergency planning session with FastTrack Ltd''s Executive team and Project Managers. Critical need for rapid implementation due to current system failure. Team willing to pay premium for expedited deployment and dedicated support team. Detailed discussion of accelerated implementation timeline and resource requirements. Key requirements: minimal disruption to operations, phased data migration, and emergency support protocols. Technical team confident in meeting aggressive timeline with additional resources. Executive sponsor emphasized importance of going live within 30 days. Immediate next steps: finalize expedited implementation plan, assign dedicated support team, and begin emergency onboarding procedures. Team to reconvene daily for progress updates.', 'FastTrack Ltd', 'Closing', 'Sarah Johnson', '2024-01-23 16:30:00', 180000, 'Premium Security'),
                ('CONV010', 'Quarterly strategic review with UpgradeNow Corp''s Department Heads and Analytics team. Current implementation meeting basic needs but team requiring more sophisticated analytics capabilities. Deep dive into current usage patterns revealed opportunities for workflow optimization and advanced reporting needs. Users expressed strong satisfaction with platform stability and basic features, but requiring enhanced data visualization and predictive analytics capabilities. Analytics team presented specific requirements: custom dashboard creation, advanced data modeling tools, and integrated BI features. Discussion about upgrade path from current package to Analytics Pro tier. ROI analysis presented showing potential 60% improvement in reporting efficiency. Team to present upgrade proposal to executive committee next month.', 'UpgradeNow Corp', 'Expansion', 'Rachel Torres', '2024-01-24 11:45:00', 65000, 'Analytics Pro')
                """).collect()
                st.success("✓ Step 2 complete! Table created with 10 comprehensive conversation transcripts")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Step 3: Cortex Search
    st.markdown("---\n### Step 3: Create Cortex Search Service")
    st.info("**Cortex Search** creates a semantic search index on your text data.\nThis enables the agent to find relevant conversations based on meaning, not just keywords.")
    setup_step3 = f"""-- Enable change tracking (required for Cortex Search)
ALTER TABLE "{db_name}"."{schema_name}".SALES_CONVERSATIONS SET CHANGE_TRACKING = TRUE;
-- Create Cortex Search service (only if it doesn't exist)
CREATE CORTEX SEARCH SERVICE IF NOT EXISTS "{db_name}"."{schema_name}".{search_service}
  ON transcript_text ATTRIBUTES customer_name, deal_stage, sales_rep WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
  AS (SELECT transcript_text, customer_name, deal_stage, sales_rep, conversation_date
      FROM "{db_name}"."{schema_name}".SALES_CONVERSATIONS WHERE conversation_date >= '2024-01-01');"""
    st.code(setup_step3, language="sql")
    
    if st.button(":material/play_arrow: Run Step 3", key="run_step3", use_container_width=True):
        with st.status("Setting up Cortex Search...", expanded=True) as status:
            try:
                # Step 3.1: Check if service already exists
                st.write(":material/search: Checking for existing search service...")
                try:
                    existing = session.sql(f'SHOW CORTEX SEARCH SERVICES IN SCHEMA "{db_name}"."{schema_name}"').collect()
                    service_exists = any(row['name'] == search_service for row in existing)
                except:
                    service_exists = False
                
                if service_exists:
                    st.write(f":material/check_circle: Search service '{search_service}' already exists")
                    status.update(label="✓ Step 3 complete (service already exists)!", state="complete")
                else:
                    # Step 3.2: Enable change tracking
                    st.write(":material/update: Enabling change tracking on table...")
                    session.sql(f'ALTER TABLE "{db_name}"."{schema_name}".SALES_CONVERSATIONS SET CHANGE_TRACKING = TRUE').collect()
                    
                    # Step 3.3: Create search service
                    st.write(":material/build: Creating Cortex Search service (this takes 30-60 seconds)...")
                    session.sql(f"""CREATE CORTEX SEARCH SERVICE "{db_name}"."{schema_name}".{search_service}
                        ON transcript_text ATTRIBUTES customer_name, deal_stage, sales_rep WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
                        AS (SELECT transcript_text, customer_name, deal_stage, sales_rep, conversation_date
                            FROM "{db_name}"."{schema_name}".SALES_CONVERSATIONS WHERE conversation_date >= '2024-01-01')""").collect()
                    
                    st.write(":material/check_circle: Search service created successfully")
                    status.update(label="✓ Step 3 complete! Service is indexing in background (1-2 min)", state="complete")
            except Exception as e:
                st.error(f"Error: {e}")
                status.update(label="Failed", state="error")
    
    # Step 4: Sales Metrics
    st.markdown("---\n### Step 4: Create Sales Metrics Table")
    st.info("**Sales Metrics Table** contains structured deal data that Cortex Analyst will query.\nThis data will be used in Day 28 for natural language SQL generation.")
    setup_step4 = f"""-- Create sales metrics table
CREATE OR REPLACE TABLE "{db_name}"."{schema_name}".SALES_METRICS (
    deal_id VARCHAR, customer_name VARCHAR, deal_value FLOAT, close_date DATE,
    sales_stage VARCHAR, win_status BOOLEAN, sales_rep VARCHAR, product_line VARCHAR);
-- Insert sample sales metrics data (10 deals)"""
    st.code(setup_step4, language="sql")
    
    if st.button(":material/play_arrow: Run Step 4", key="run_step4", use_container_width=True):
        with st.spinner("Creating sales metrics table..."):
            try:
                session.sql(f"""CREATE OR REPLACE TABLE "{db_name}"."{schema_name}".SALES_METRICS (
                    deal_id VARCHAR, customer_name VARCHAR, deal_value FLOAT, close_date DATE,
                    sales_stage VARCHAR, win_status BOOLEAN, sales_rep VARCHAR, product_line VARCHAR)""").collect()
                session.sql(f"""INSERT INTO "{db_name}"."{schema_name}".SALES_METRICS VALUES
                    ('DEAL001', 'TechCorp Inc', 75000, '2024-02-15', 'Closed', true, 'Sarah Johnson', 'Enterprise Suite'),
                    ('DEAL002', 'SmallBiz Solutions', 25000, '2024-02-01', 'Lost', false, 'Mike Chen', 'Basic Package'),
                    ('DEAL003', 'SecureBank Ltd', 150000, '2024-01-30', 'Closed', true, 'Rachel Torres', 'Premium Security'),
                    ('DEAL004', 'GrowthStart Up', 100000, '2024-02-10', 'Pending', false, 'Sarah Johnson', 'Enterprise Suite'),
                    ('DEAL005', 'DataDriven Co', 85000, '2024-02-05', 'Closed', true, 'James Wilson', 'Analytics Pro'),
                    ('DEAL006', 'HealthTech Solutions', 120000, '2024-02-20', 'Pending', false, 'Rachel Torres', 'Premium Security'),
                    ('DEAL007', 'LegalEase Corp', 95000, '2024-01-25', 'Closed', true, 'Mike Chen', 'Enterprise Suite'),
                    ('DEAL008', 'GlobalTrade Inc', 45000, '2024-02-08', 'Closed', true, 'James Wilson', 'Basic Package'),
                    ('DEAL009', 'FastTrack Ltd', 180000, '2024-02-12', 'Closed', true, 'Sarah Johnson', 'Premium Security'),
                    ('DEAL010', 'UpgradeNow Corp', 65000, '2024-02-18', 'Pending', false, 'Rachel Torres', 'Analytics Pro')""").collect()
                st.success("✓ Step 4 complete! Sales metrics table created with 10 deals")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Step 5: Semantic Model YAML
    st.markdown("---\n### Step 5: Upload Semantic Model YAML")
    st.info("**Semantic Model** tells Cortex Analyst how to interpret your database schema.\nDownload the YAML file and upload it to a Snowflake stage in the next step.")
    
    semantic_model_yaml = f"""name: sales_metrics
description: Sales metrics and analytics model
tables:
  - name: SALES_METRICS
    base_table:
      database: {db_name}
      schema: {schema_name}
      table: SALES_METRICS
    dimensions:
      - name: DEAL_ID
        expr: DEAL_ID
        data_type: VARCHAR(16777216)
        sample_values: [DEAL001, DEAL002, DEAL003]
        description: Unique identifier for a sales deal, used to track and analyze individual sales agreements.
        synonyms: [Transaction ID, Agreement ID, Contract ID, Sale ID, Order ID, Deal Number]
      - name: CUSTOMER_NAME
        expr: CUSTOMER_NAME
        data_type: VARCHAR(16777216)
        sample_values: [TechCorp Inc, SmallBiz Solutions, SecureBank Ltd]
        description: The name of the customer associated with a particular sale or transaction.
        synonyms: [client, buyer, purchaser, account_name, account_holder]
      - name: SALES_STAGE
        expr: SALES_STAGE
        data_type: VARCHAR(16777216)
        sample_values: [Closed, Lost, Pending]
        description: The current stage of a sales opportunity, indicating whether it has been successfully closed, lost to a competitor, or is still pending a decision.
        synonyms: [deal_status, sales_phase, opportunity_state, pipeline_position]
      - name: WIN_STATUS
        expr: WIN_STATUS
        data_type: BOOLEAN
        sample_values: ['TRUE', 'FALSE']
        description: Indicates whether a sale was won (TRUE) or lost (FALSE).
        synonyms: [won, success, closed, converted, achieved, accomplished]
      - name: SALES_REP
        expr: SALES_REP
        data_type: VARCHAR(16777216)
        sample_values: [Sarah Johnson, Mike Chen, Rachel Torres]
        description: The sales representative responsible for the sale.
        synonyms: [salesperson, account_manager, representative, agent]
      - name: PRODUCT_LINE
        expr: PRODUCT_LINE
        data_type: VARCHAR(16777216)
        sample_values: [Enterprise Suite, Basic Package, Premium Security]
        description: This column categorizes sales by the type of product or service offered, distinguishing between the comprehensive Enterprise Suite, the standard Basic Package, and the advanced Premium Security package.
        synonyms: [product family, item category, merchandise type, goods classification, commodity group]
    time_dimensions:
      - name: CLOSE_DATE
        expr: CLOSE_DATE
        data_type: DATE
        sample_values: ['2024-02-15', '2024-02-01', '2024-01-30']
        description: The date on which a sale was closed or finalized.
        synonyms: [completion date, sale date, deal close date, transaction date, sale completion date]
    measures:
      - name: DEAL_VALUE
        expr: DEAL_VALUE
        data_type: FLOAT
        sample_values: ['75000', '25000', '150000']
        description: The total monetary value of a sales deal or transaction.
        synonyms: [revenue, sale_amount, transaction_value, deal_amount, sale_price]
"""
    
    st.code(semantic_model_yaml, language="yaml")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(":material/download: Download YAML", semantic_model_yaml, "sales_metrics_model.yaml", 
                          "application/x-yaml", use_container_width=True)
    with col2:
        if st.button(":material/cloud_upload: Auto-Upload to Stage", key="run_step5", use_container_width=True, type="primary"):
            with st.spinner("Creating stage and uploading YAML..."):
                try:
                    import tempfile, os
                    session.sql(f'CREATE STAGE IF NOT EXISTS "{db_name}"."{schema_name}".MODELS').collect()
                    
                    # Clean up old files
                    try:
                        files = session.sql(f'LIST @"{db_name}"."{schema_name}".MODELS').collect()
                        for row in files:
                            fname = str(row['name']).split('/')[-1]
                            if 'sales_metrics_model' in fname.lower():
                                session.sql(f'REMOVE @"{db_name}"."{schema_name}".MODELS/{fname}').collect()
                    except: pass
                    
                    # Upload new file
                    temp_dir = tempfile.mkdtemp()
                    temp_file_path = os.path.join(temp_dir, 'sales_metrics_model.yaml')
                    try:
                        with open(temp_file_path, 'w', encoding='utf-8') as f:
                            f.write(semantic_model_yaml)
                        session.file.put(temp_file_path, f'@"{db_name}"."{schema_name}".MODELS', auto_compress=False, overwrite=True)
                        
                        # Verify
                        files = session.sql(f'LIST @"{db_name}"."{schema_name}".MODELS').collect()
                        uploaded_files = [str(row['name']).split('/')[-1] for row in files]
                        if 'sales_metrics_model.yaml' in uploaded_files:
                            st.success("✓ Step 5 complete! YAML uploaded as `sales_metrics_model.yaml`")
                        else:
                            found_file = next((f for f in uploaded_files if 'sales_metrics_model' in f.lower()), None)
                            if found_file:
                                st.warning(f"⚠️ File uploaded as `{found_file}` instead of `sales_metrics_model.yaml`")
                                st.info("Day 28 will automatically detect this file.")
                            else:
                                st.error("Upload succeeded but file not found in stage listing")
                    finally:
                        try:
                            if os.path.exists(temp_file_path): os.remove(temp_file_path)
                            if os.path.exists(temp_dir): os.rmdir(temp_dir)
                        except: pass
                except Exception as e:
                    st.error(f"Auto-upload failed: {str(e)}")
                    st.info("💡 Use the 'Download YAML' button and upload manually via Snowsight instead")
    
    with st.expander("📋 Manual Upload Instructions (if auto-upload fails)"):
        st.markdown("""
        1. Click **"Download YAML"** button above
        2. In Snowsight: **Data** → **Databases** → **30DAYS_SALES_INTELLIGENCE** → **DATA**
        3. Click **"Stages"** tab → **MODELS** stage
        4. Click **"+ Files"** → Upload `sales_metrics_model.yaml`
        """)
    
    # Step 6: Verification
    st.markdown("---\n### Step 6: Verify Complete Setup")
    if st.button(":material/verified: Check if Data is Ready", type="primary", use_container_width=True):
        with st.status("Verifying setup...", expanded=True) as status:
            all_good = True
            checks = [
                (f'USE DATABASE "{db_name}"', "Database exists"),
                (f'SELECT COUNT(*) as cnt FROM "{db_name}"."{schema_name}".SALES_CONVERSATIONS', "Conversations table", True),
                (f'SHOW CORTEX SEARCH SERVICES IN SCHEMA "{db_name}"."{schema_name}"', "Cortex Search service", False, search_service),
                (f'SELECT COUNT(*) as cnt FROM "{db_name}"."{schema_name}".SALES_METRICS', "Sales metrics table", True, None, True),
                (f'SHOW STAGES IN SCHEMA "{db_name}"."{schema_name}"', "MODELS stage", False, "MODELS", True)
            ]
            
            for check in checks:
                sql, name = check[0], check[1]
                try:
                    result = session.sql(sql).collect()
                    if len(check) > 2 and check[2]:  # Count query
                        st.write(f":material/check_circle: {name} with {result[0]['CNT']} records")
                    elif len(check) > 3 and check[3]:  # Check for specific value
                        found = any(check[3] in str(r) for r in result)
                        if found:
                            st.write(f":material/check_circle: {name}")
                        else:
                            st.write(f":material/{'warning' if len(check) > 4 else 'cancel'}: {name} not found")
                            if len(check) <= 4: all_good = False
                    else:
                        st.write(f":material/check_circle: {name}")
                except:
                    st.write(f":material/{'warning' if len(check) > 4 else 'cancel'}: {name} not found")
                    if len(check) <= 4: all_good = False
            
            if all_good:
                status.update(label=":material/celebration: Day 27 data ready! (Day 28+ data optional)", state="complete")
                st.balloons()
    else:
                status.update(label="Complete Steps 1-3 for Day 27, Steps 4-5 for Day 28+", state="error")

# Create Agent Tab
with tab1:
    st.markdown("### Create Sales Conversation Agent")
    
    instructions = """You are a Sales Intelligence Assistant with access to two data sources:
1. Sales conversation transcripts (via ConversationSearch tool)
2. Sales metrics and deal data (via SalesAnalyst tool)

IMPORTANT CONSTRAINTS:
- ONLY answer questions about sales data, conversations, deals, customers, and sales metrics
- DECLINE questions about: weather, coding, general knowledge, current events, or any non-sales topics
- Use ONLY the data from the tools - do NOT make up or hallucinate information
- If data is not found, clearly state that no data is available
- For metrics questions (totals, averages, counts), use the SalesAnalyst tool
- For conversation questions (summaries, discussions), use the ConversationSearch tool"""
    
    create_sql = f"""CREATE OR REPLACE AGENT "{db_name}"."{schema_name}".{agent_name}
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: '{instructions.replace("'", "''")}'
    orchestration: 'For metrics questions (totals, averages, counts, aggregations), use SalesAnalyst. For conversation questions (summaries, what was discussed), use ConversationSearch. Decline off-topic questions politely.'
    system: 'You are a helpful but constrained sales intelligence assistant. Answer ONLY from available data.'
  tools:
    - tool_spec:
        type: "cortex_search"
        name: "ConversationSearch"
        description: "Searches sales conversation transcripts"
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "SalesAnalyst"
        description: "Generates and executes SQL queries on sales metrics"
  tool_resources:
    ConversationSearch:
      name: "{db_name}.{schema_name}.{search_service}"
      max_results: "5"
    SalesAnalyst:
      semantic_model_file: "@chaninn_sales_intelligence.data.models/sales_metrics_model.yaml"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
        query_timeout: 60
  $$;"""
    
    st.code(create_sql, language="sql")
    
    if st.button(":material/play_arrow: Create Agent", type="primary", use_container_width=True):
        try:
            with st.status("Creating agent...") as status:
                try:
                    session.sql("SHOW AGENTS").collect()
                    st.write(":material/check: Cortex Agents available")
                except Exception as e:
                    if "syntax error" in str(e).lower():
                        st.error(":material/error: Cortex Agents not available in your account")
                        st.info("Contact your Snowflake admin to enable this feature.")
                        st.stop()
                
                st.write(":material/check: Creating agent...")
                session.sql(create_sql).collect()
                st.write(f"  Agent created: {db_name}.{schema_name}.{agent_name}")
                st.session_state.agent_created = True
                status.update(label=":material/check_circle: Agent Ready!", state="complete")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {str(e)}")
            status.update(label="Failed", state="error")

st.divider()
st.caption("Day 26: Introduction to Cortex Agents | Create Your First Agent | 30 Days of AI with Streamlit")
