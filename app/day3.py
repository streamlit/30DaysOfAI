# Day 3
# Write streams

import streamlit as st
from openai import OpenAI

st.title(":material/airwave: Write Streams")

conn = st.secrets["connections"]["snowflake"]
host = conn.get("host") or f"{conn['account']}.snowflakecomputing.com"
client = OpenAI(api_key=conn["password"], base_url=f"https://{host}/api/v2/cortex/v1")

llm_models = ["claude-3-5-sonnet", "mistral-large", "llama3.1-8b"]
model = st.selectbox("Select a model", llm_models)

example_prompt = "What is Python?"
prompt = st.text_area("Enter prompt", example_prompt)

streaming_method = st.radio(
    "Streaming Method:",
    ["Direct", "Real Streaming"],
    help="Choose how to stream the response"
)

if st.button("Generate Response"):
    messages = [{"role": "user", "content": prompt}]
    
    if streaming_method == "Direct":
        with st.spinner(f"Generating response with `{model}`"):
            response = client.chat.completions.create(model=model, messages=messages, stream=False)
            st.write(response.choices[0].message.content)
    else:
        with st.spinner(f"Generating response with `{model}`"):
            stream = client.chat.completions.create(model=model, messages=messages, stream=True)
        st.write_stream(stream)

# Footer
st.divider()
st.caption("Day 3: Write streams | 30 Days of AI")
