from warnings import filterwarnings
import streamlit as st
from langchain_openai import ChatOpenAI
# from langchain import hub
from services.patent.api.prompt import react_prompt
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from services.patent.api.patent_class import KiprisAPIWraper, KiprisAPITool
from logging import getLogger
from langchain.agents.react.output_parser import ReActOutputParser
import json

class CustomReActOutputParser(ReActOutputParser):
    def parse(self, output: str):
        if "Thought" not in output or "Action" not in output:
            raise ValueError("Invalid format: Missing 'Thought' or 'Action'")
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")

filterwarnings("ignore")
logger = getLogger(__name__)

# prompt = hub.pull("hwchase17/react")
prompt = PromptTemplate(template=react_prompt, input_variables=["tools", "tool_names", "input", "agent_scratchpad"])
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=st.secrets["OPENAI"]["api_key"])
kipris_api = KiprisAPIWraper(api_key=str(st.secrets["KIPRIS"]["api_key"]))
tools = KiprisAPITool(kipris_api).tools()

react_agent = create_react_agent(llm, tools, prompt)
react_agent_executor = AgentExecutor(agent=react_agent, 
                                     tools=tools, 
                                     verbose=True, 
                                     handle_parsing_errors=True,
                                    #  max_execution_time=20
                                     )

