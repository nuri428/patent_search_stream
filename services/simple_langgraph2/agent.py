import functools
import operator
import os
import typing as t
from warnings import filterwarnings

import streamlit as st
from langchain.agents import create_react_agent
from langchain_core.messages import  HumanMessage, trim_messages
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from services.patent.api.prompt import ds_react_prompt
# from services.patent.api import kipris_react_agent_executor, kipris_openapi_agent_executor
from services.patent.api import kipris_react_agent_executor
from services.simple_langgraph.tool import python_repl_tool
from langchain.agents import AgentExecutor

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN"]["endpoint"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN"]["project"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI"]["api_key"]
# from icecream import ic

filterwarnings("ignore")

llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

trimmer = trim_messages(
    max_tokens=100000,
    strategy="last",
    token_counter=llm,
    include_system=True,
)

# def agent_node(state, agent, name):
#     result = agent.invoke(state)
#     return {
#         "messages": [HumanMessage(content=result["messages"][-1].content, name=name)]
#     }

def create_team_supervisor(llm: ChatOpenAI, system_prompt, members) -> str:
    """An LLM-based router."""
    options = ["FINISH"] + members
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": options},
                    ],
                },
            },
            "required": ["next"],
        },
    }
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), team_members=", ".join(members))
    return (
        prompt
        | trimmer
        | llm.bind_functions(functions=[function_def], function_call="route")
        | JsonOutputFunctionsParser()
    )

# kipris_node = functools.partial(agent_node, agent=kipris_react_agent, name="patent_search")

def kipris_node (state):
    messages = state["messages"]

    result = kipris_react_agent_executor.invoke({"input":messages})
    # print(result)
    return {
        "messages": [HumanMessage(content=result['output'], name='patent_search')]
    }

ds_prompt = PromptTemplate(template=ds_react_prompt, input_variables=["tools", "tool_names", "input", "agent_scratchpad"])
ds_agent = create_react_agent(llm, tools=[python_repl_tool], prompt=ds_prompt)
agent_executor = AgentExecutor.from_agent_and_tools(agent = ds_agent, tools=[python_repl_tool], handle_parsing_errors=True) # Add this line.

def ds_node(state):
    messages = state["messages"]
    res = agent_executor.invoke({"input":messages})
    return {"messages": [HumanMessage(content=res['output'], name='data_scientist')]}

supervisor = create_team_supervisor(llm, 
            """You are a supervisor tasked with managing a conversation 
            between the following workers: patent_search, data_scientist
            patent_search is specialized in searching korean patents
            data_scientist is specialized in data science tasks.
            Given the following user request, who should act next?
            Or should we FINISH?
            Each worker will respond perform a task and repond with their results and status. 
            when finished, respond with FINISH
            """, 
            ["patent_search", "data_scientist"])



