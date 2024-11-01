# from warnings import filterwarnings
# import streamlit as st
# from langchain_openai import ChatOpenAI
# from langchain import hub
# from langchain.agents import create_react_agent, AgentExecutor

# # from langchain.prompts import PromptTemplate
# from logging import getLogger
# logger = getLogger(__name__)
# filterwarnings("ignore")

# prompt = hub.pull("react-agent/react-agent")
# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=st.secrets["OPENAI"]["api_key"])
# # prompt = PromptTemplate(template="You are a helpful assistant. The user asked the following question: {input}", input_variables=["input"])
# # chain = prompt | llm

# tools = [search_patent]
