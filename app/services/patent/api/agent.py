from warnings import filterwarnings
import streamlit as st
from langchain_openai import ChatOpenAI
# from langchain import hub
from services.patent.api.prompt import react_prompt
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
import os
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]
os.environ["KIPRIS_API_KEY"] = st.secrets["KIPRIS"]["api_key"]
from langchain_kipris_tools import LangChainKiprisKoreanTools
from logging import getLogger

filterwarnings("ignore")
logger = getLogger(__name__)

prompt = PromptTemplate(template=react_prompt, input_variables=["tools", "tool_names", "input", "agent_scratchpad"])
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=st.secrets["OPENAI"]["api_key"])
kiprisTools = LangChainKiprisKoreanTools()
tools = kiprisTools.get_tools()
kipris_react_agent = create_react_agent(llm, tools, prompt)
kipris_react_agent_executor = AgentExecutor(agent=kipris_react_agent, tools=tools, handle_parsing_errors=True)
