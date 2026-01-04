# Day 3
# Write streams

import streamlit as st
from snowflake.cortex import Complete
import time

st.title(":material/airwave: Write Streams")

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create() 

llm_models = ["claude-3-5-sonnet", "mistral-large", "llama3.1-8b"]
model= st.selectbox("Select a model", llm_models)

example_prompt = "What is Python?"
prompt = st.text_area("Enter prompt", example_prompt)

# Choose streaming method
streaming_method = st.radio(
    "Streaming Method:",
    ["Direct (stream=True)", "Custom Generator"],
    help="Choose how to stream the response"
)

if st.button("Generate Response"):

    # Method 1: Direct streaming with stream=True
    if streaming_method == "Direct (stream=True)":
        with st.spinner(f"Generating response with `{model}`"):
            stream_generator = Complete(
                        session=session,
                        model=model,
                        prompt=prompt,
                        stream=True,
                    )
                    
            st.write_stream(stream_generator)
    
    else:
        # Method 2: Custom generator (for compatibility)
        def custom_stream_generator():
            """
            Alternative streaming method for cases where
            the generator is not compatible with st.write_stream
            """
            output = Complete(
                session=session,
                model=model,
                prompt=prompt
            )
            for chunk in output:
                yield chunk
                time.sleep(0.01)  # Small delay for smooth streaming
        
        with st.spinner(f"Generating response with `{model}`"):
            st.write_stream(custom_stream_generator)

# Footer
st.divider()
st.caption("Day 3: Write streams | 30 Days of AI")