import json
import logging
from langchain_core.messages import ToolMessage, AnyMessage
from langchain_core.utils.function_calling import format_tool_to_openai_function
from langchain_kipris_tools import LangChainKiprisTools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt import ToolInvocation
from icecream import ic
import operator
from typing import TypedDict, Annotated
import functools
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage   
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)
tools_class = LangChainKiprisTools()
tools = tools_class.get_tools()
tool_executor = ToolExecutor(tools)
llm = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True, stream_options={"include_usage": True}) 
functions = [format_tool_to_openai_function(tool) for tool in tools]
model = llm.bind_tools(functions)
ic.disable()


def create_agent(llm, tools, system_message: str):
    """Create an agent."""
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
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)


# 해당 에이전트의 노드를 만드는데 필요한 헬퍼 함수
def agent_node(state, agent, name):
    result = agent.invoke(state)

    # 에이전트 출력을 전역 상태에 추가될 형식으로 변환한다.
    if isinstance(result, ToolMessage):
        pass
    else:
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        # 엄격한 워크플로우를 가지고 있기 때문에 다음에 누구에게 전달하는지 알 수 있다.
        "sender": name,
    }


# agentState 객체
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

front_agent = create_agent(
    llm,
    [],
    system_message="""You are a helpful AI assistant, collaborating with other assistants.
    you are responsible for the user interface of the qa system.
    you take user's question then you make decistion 
    if you can answer it, you answer it.
    if you can't answer it, you call kipris_model to answer it.
    when call kipris_model, you should provide accurate data for the kipris_model to use.
    and finally you return the answer to the user.    
    
    You have access to the following tools: {tool_names}.
    You should provide accurate data for the kipris_model to use.""",
)
front_node = functools.partial(agent_node, agent=front_agent, name="Front")



def kipris_model(state:AgentState):
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
    return {"messages": [response]}


def call_tool(state:AgentState):
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
        return {"messages":  tool_messages}
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