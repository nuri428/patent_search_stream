import sys
from pathlib import Path
import os

# 절대 경로로 지정
PACKAGE_DIR = Path(__file__).resolve().parent.parent / "pkgs" / "kipris_tools"
sys.path.insert(0, str(PACKAGE_DIR))

# 디버깅을 위한 출력
print("PYTHONPATH:", os.environ['PYTHONPATH'])
print("sys.path:", sys.path)

import langchain_kipris_tools

import streamlit as st

from streamlit_chat import message
# from services.patent.api import react_agent_executor
# from services.simple_langgraph.graph import app
# from services.simple_langgraph2.graph import research_chain
from services.patent.api.simplachain import call_with_tool
import os
import uuid
from langchain_teddynote import logging
logging.langsmith('patent_search')
# from icecream import ic
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN"]["endpoint"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN"]["project"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY"]["api_key"]
st.set_page_config(page_title="🤗💬 patent_chatbot", layout="wide")
if "session_id" not in st.session_state.keys():
    st.session_state.session_id = str(uuid.uuid4())
# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": " 안녕하세요 뭘 도와 드릴까요?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function for generating LLM response
def generate_response(prompt_input: str) -> str:
    if not prompt_input:
        return "검색어를 입력해주세요."
    
    try:
        res = call_with_tool(prompt_input)
        return res
    except Exception as e:
        print(f"Error in generate_response: {str(e)}")
        return f"오류가 발생했습니다: {str(e)}"
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
            st.markdown(response)

    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)