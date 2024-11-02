import json
import os
import functools
from warnings import filterwarnings

import streamlit as st

# from services.patent.api import react_agent_executor
from langchain_core.messages import HumanMessage, FunctionMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from services.simple_langgraph.tool import python_repl_tool
from services.patent.api.patent_class import KiprisAPITool, KiprisAPIWraper
from langchain.tools.render import format_tool_to_openai_function
from langgraph.prebuilt.tool_executor import ToolExecutor, ToolInvocation
from langchain_core.output_parsers import JsonOutputFunctionsParser

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN"]["endpoint"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN"]["project"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI"]["api_key"]
from icecream import ic
filterwarnings("ignore")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

trimmer = trim_messages(
    max_tokens=100000,
    strategy="last",
    token_counter=llm,
    include_system=True,
)
def agent_node(state, agent, name):
    result = agent.invoke(state)
    if isinstance(result, FunctionMessage):
        pass
    else:
        result = HumanMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        "sender": name,
    }
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
    

def create_agent(llm, tools, system_message: str):
    # 에이전트를 생성합니다.
    functions = [format_tool_to_openai_function(t) for t in tools]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join(
        [tool.name for tool in tools]))
    return prompt | llm.bind_functions(functions)




kipris_api = KiprisAPIWraper(api_key=str(st.secrets["KIPRIS"]["api_key"]))
kirpis_tools = KiprisAPITool(kipris_api).tools()

# Research agent and node
research_agent = create_agent(
    llm,
    kirpis_tools,
    system_message="You should provide accurate data for the chart generator to use.",
)
research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")
# Chart Generator
chart_agent = create_agent(
    llm,
    [python_repl_tool],
    system_message="Any charts you display will be visible by the user.",
)
chart_node = functools.partial(agent_node, agent=chart_agent, name="Chart Generator")

ds_agent = create_agent(
    llm,
    [python_repl_tool],
    system_message="You are a data scientist, you should provide accurate data for user or chart generator to use.",
)
ds_node = functools.partial(agent_node, agent=ds_agent, name="Data Scientist")


tools = [python_repl_tool]
tools.extend(kirpis_tools)
# tool_node = ToolNode(tools)
tool_executor = ToolExecutor(tools)

def tool_node(state):
    # 그래프에서 도구를 실행하는 함수입니다.
    # 에이전트 액션을 입력받아 해당 도구를 호출하고 결과를 반환합니다.
    messages = state["messages"]
    # ic(messages)
    # 계속 조건에 따라 마지막 메시지가 함수 호출을 포함하고 있음을 알 수 있습니다.
    last_message = messages[-1]
    # ToolInvocation을 함수 호출로부터 구성합니다.
    tool_input = json.loads(
        last_message.additional_kwargs["function_call"]["arguments"]
    )
    # 단일 인자 입력은 값으로 직접 전달할 수 있습니다.
    if len(tool_input) == 1 and "__arg1" in tool_input:
        tool_input = next(iter(tool_input.values()))
    tool_name = last_message.additional_kwargs["function_call"]["name"]

    action = ToolInvocation(
        tool=tool_name,
        tool_input=tool_input,
    )
    # 도구 실행자를 호출하고 응답을 받습니다.
    response = tool_executor.invoke(action)
    # 응답을 사용하여 FunctionMessage를 생성합니다.
    function_message = FunctionMessage(
        content=f"{tool_name} response: {str(response)}", name=action.tool
    )
    # 기존 리스트에 추가될 리스트를 반환합니다.
    return {"messages": [function_message]}

def router(state):
    # 상태 정보를 기반으로 다음 단계를 결정하는 라우터 함수
    # ic('router', state)
    messages = state["messages"]
    last_message = messages[-1]
    if "function_call" in last_message.additional_kwargs:
        # 이전 에이전트가 도구를 호출함
        return "call_tool"
    if "FINAL ANSWER" in last_message.content:
        # 어느 에이전트든 작업이 끝났다고 결정함
        return "end"
    if "Data Scientist" in last_message.content:
        return "Data Scientist"
    return "continue"
