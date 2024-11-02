from warnings import filterwarnings
import streamlit as st
from langchain_openai import ChatOpenAI
# from langchain import hub
from services.patent.api.prompt import react_prompt
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from services.patent.api.patent_class import KiprisAPIWraper, KiprisAPITool
from logging import getLogger

filterwarnings("ignore")
logger = getLogger(__name__)

prompt = PromptTemplate(template=react_prompt, input_variables=["tools", "tool_names", "input", "agent_scratchpad"])
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=st.secrets["OPENAI"]["api_key"])
kipris_api = KiprisAPIWraper(api_key=str(st.secrets["KIPRIS"]["api_key"]))
tools = KiprisAPITool(kipris_api).tools()

react_agent = create_react_agent(llm, tools, prompt)
react_agent_executor = AgentExecutor(agent=react_agent, 
                                     tools=tools, 
                                     verbose=True, 
                                     handle_parsing_errors=True)

