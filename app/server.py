import streamlit as st

from streamlit_chat import message
from services.patent.api import react_agent_executor
import os
# from icecream import ic
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN"]["endpoint"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN"]["project"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]

st.set_page_config(page_title="🤗💬 patent_chatbot", layout="wide")

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요 뭘 도와 드릴까요?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function for generating LLM response
def generate_response(prompt_input):
    if prompt_input is None:
        return {"output": []}
    return react_agent_executor.invoke({"input": prompt_input})

# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt) 
            if 'log' in response:
                st.markdown(response['log'])
            st.markdown(response['output']) 

    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)