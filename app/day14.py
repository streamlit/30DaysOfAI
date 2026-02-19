# Day 14
# Adding Avatars and Error Handling

import streamlit as st
import json
from snowflake.snowpark.functions import ai_complete
import time

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

def call_llm(prompt_text: str) -> str:
    """Call Snowflake Cortex LLM."""
    df = session.range(1).select(
        ai_complete(model="claude-3-5-sonnet", prompt=prompt_text).alias("response")
    )
    response_raw = df.collect()[0][0]
    response_json = json.loads(response_raw)
    if isinstance(response_json, dict):
        return response_json.get("choices", [{}])[0].get("messages", "")
    return str(response_json)

st.title(":material/account_circle: Adding Avatars and Error Handling")

# Initialize system prompt if not exists
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful assistant."

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your AI assistant. How can I help you today?"}
    ]

# Sidebar configuration
with st.sidebar:
    st.header(":material/settings: Settings")
    
    # Avatar customization
    st.subheader(":material/palette: Avatars")
    user_avatar = st.selectbox(
        "Your Avatar:",
        ["👤", "🧑‍💻", "👨‍🎓", "👩‍🔬", "🦸", "🧙"],
        index=0
    )
    
    assistant_avatar = st.selectbox(
        "Assistant Avatar:",
        ["🤖", "🧠", "✨", "🎯", "💡", "🌟"],
        index=0
    )
    
    st.divider()
    
    # System prompt
    st.subheader(":material/description: System Prompt")
    st.text_area(
        "Customize behavior:",
        height=100,
        key="system_prompt",
        help="Define how the AI should behave and respond"
    )
    
    st.divider()
    
    # Debug toggle to simulate errors
    st.subheader(":material/bug_report: Debug Mode")
    simulate_error = st.checkbox(
        "Simulate API Error",
        value=False,
        help="Enable this to test the error handling mechanism"
    )
    
    st.divider()
    
    # Conversation stats
    st.header("Conversation Stats")
    user_msgs = len([m for m in st.session_state.messages if m["role"] == "user"])
    assistant_msgs = len([m for m in st.session_state.messages if m["role"] == "assistant"])
    st.metric("Your Messages", user_msgs)
    st.metric("AI Responses", assistant_msgs)
    
    if st.button("Clear History"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your AI assistant. How can I help you today?"}
        ]
        st.rerun()

# Display all messages from history with custom avatars
for message in st.session_state.messages:
    avatar = user_avatar if message["role"] == "user" else assistant_avatar
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    # Add and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(prompt)
    
    # Generate response with error handling
    with st.chat_message("assistant", avatar=assistant_avatar):
        try:
            # Simulate error if debug mode is enabled
            if simulate_error:
                raise Exception("Simulated API error: Service temporarily unavailable (429)")
            
            # Custom generator for reliable streaming
            def stream_generator():
                # Build the full conversation history for context
                conversation = "\n\n".join([
                    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                    for msg in st.session_state.messages
                ])
                
                # Create prompt with system instruction
                full_prompt = f"""{st.session_state.system_prompt}

Here is the conversation so far:
{conversation}

Respond to the user's latest message."""
                
                response_text = call_llm(full_prompt)
                for word in response_text.split(" "):
                    yield word + " "
                    time.sleep(0.02)
            
            with st.spinner("Processing"):
                response = st.write_stream(stream_generator)
            
            # Add assistant response to state
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()  # Force rerun to update sidebar stats
            
        except Exception as e:
            error_message = f"I encountered an error: {str(e)}"
            st.error(error_message)
            st.info(":material/lightbulb: **Tip:** This might be a temporary issue. Try again in a moment, or rephrase your question.")

st.divider()
st.caption("Day 14: Adding Avatars and Error Handling | 30 Days of AI")