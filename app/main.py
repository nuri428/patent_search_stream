import sys
from pathlib import Path
import os
import streamlit as st
from streamlit_chat import message
from services.patent.api.simplachain import call_with_tool_stream
import uuid
from langchain_teddynote import logging
import asyncio
from typing import AsyncGenerator

# 패키지 경로 설정
PACKAGE_DIR = Path(__file__).resolve().parent.parent / "pkgs" / "kipris_tools"
sys.path.insert(0, str(PACKAGE_DIR))
import langchain_kipris_tools

# LangSmith 설정
logging.langsmith('patent_search')
for key, value in {
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_ENDPOINT": st.secrets["LANGCHAIN"]["endpoint"],
    "LANGCHAIN_API_KEY": st.secrets["LANGCHAIN"]["api_key"],
    "LANGCHAIN_PROJECT": st.secrets["LANGCHAIN"]["project"],
    "LANGSMITH_API_KEY": st.secrets["LANGCHAIN"]["api_key"],
    "TAVILY_API_KEY": st.secrets["TAVILY"]["api_key"]
}.items():
    os.environ[key] = value

# Streamlit 설정
st.set_page_config(page_title="🤗💬 patent_chatbot", layout="wide")

class ChatProcessor:
    def __init__(self):
        self.messages = st.session_state.messages
        
    def add_message(self, role: str, content: str):
        """메시지를 대화 기록에 추가"""
        self.messages.append({"role": role, "content": content})
        
    def display_message(self, role: str, content: str):
        """메시지를 화면에 표시"""
        with st.chat_message(role):
            st.write(content)

    async def process_response(self, prompt: str, streaming: bool = True):
        """응답 처리를 위한 공통 함수"""
        if not prompt:
            return "검색어를 입력해주세요."
            
        try:
            if streaming:
                return await self._process_streaming(prompt)
            else:
                return await self._process_sync(prompt)
        except Exception as e:
            print(f"Error in process_response: {str(e)}")
            return f"오류가 발생했습니다: {str(e)}"
            
    async def _process_streaming(self, prompt: str) -> str:
        """스트리밍 응답 처리"""
        response_container = st.empty()
        full_response = []
        
        async for chunk in call_with_tool_stream(prompt):
            full_response.append(chunk)
            response_container.write("".join(full_response))
        
        return "".join(full_response)
        
    async def _process_sync(self, prompt: str) -> str:
        """동기식 응답 처리"""
        return await call_with_tool_stream(prompt).__anext__()

# Streamlit 앱 초기화
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요 뭘 도와 드릴까요?"}]
if "chat_processor" not in st.session_state:
    st.session_state.chat_processor = ChatProcessor()

# 기존 메시지 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 사용자 입력 처리
if prompt := st.chat_input():
    processor = st.session_state.chat_processor
    processor.add_message("user", prompt)
    processor.display_message("user", prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = asyncio.run(processor.process_response(prompt))
            processor.add_message("assistant", response)