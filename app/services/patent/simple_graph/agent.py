import json
import logging
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.utils.function_calling import format_tool_to_openai_function
from langchain_kipris_tools import LangChainKiprisTools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt import ToolInvocation
from icecream import ic
from typing import TypedDict
logger = logging.getLogger(__name__)
tools_class = LangChainKiprisTools()
tools = tools_class.get_tools()
tool_executor = ToolExecutor(tools)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)   
functions = [format_tool_to_openai_function(tool) for tool in tools]
model = llm.bind_tools(functions)
ic.disable()

# agentState 객체
class AgentState(TypedDict):
    messages: BaseMessage
    sender: str

def call_model(state):
    """langgraph에서 model을 호출 하는 노드

    Args:
        state (AgentState): 현재 상태값

    Returns:
        dict: 모델 호출 결과 messages
    """
    ic("call_model")
    
    messages = state["messages"]
    
    # 이전 메시지들을 모두 포함하여 모델에 전달
    response = model.invoke(messages)
    ic(response)
    
    # 이전 메시지들과 함께 새로운 응답을 반환
    return {"messages": messages + [response]}

def call_tool(state):
    """langgraph에서 tool을 호출 하는 노드

    Args:
        state (AgentState): 현재 상태값

    Returns:
        dict: 모델 호출 결과 messages
    """
    messages = state["messages"]
    last_message = messages[-1]
    try:
        tool_messages = []
        for tool_call in last_message.additional_kwargs["tool_calls"]:
            action = ToolInvocation(
                tool=tool_call["function"]["name"],
                tool_input=json.loads(tool_call["function"]["arguments"]),
            )
            response = tool_executor.invoke(action)
            tool_messages.append(
                ToolMessage(
                    role='tool',
                    content=str(response),
                    name=action.tool,
                    tool_call_id=tool_call["id"]                    
                )
            )
        # 이전 메시지들과 함께 tool 응답을 반환
        return {"messages": messages + tool_messages}
    except (KeyError, json.JSONDecodeError) as e:
        raise Exception(f"Tool 호출 중 에러 발생: {str(e)}")

def should_continue(state):
    """call_model에서 call_tool 혹은 종료를 결정할 브랜치 도구

    Args:
        state (AgentState): 현재 상태값

    Returns:
        str: end, continue 둘 중 하나
    """
    try:
        messages = state["messages"]
        last_message = messages[-1]
        ic(last_message.additional_kwargs)
        return "continue" if "tool_calls" in last_message.additional_kwargs else "end"
    except (KeyError, IndexError) as e:
        ic(f"Error in should_continue: {e}")
        return "end"  # 에러 발생시 안전하게 종료