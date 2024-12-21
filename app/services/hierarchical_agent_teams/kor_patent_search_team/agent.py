import json
import operator
import typing as t
from dotenv import load_dotenv
from langchain.tools.render import format_tool_to_openai_function
from langchain_core.messages import (
    BaseMessage,
    FunctionMessage,
)
from langchain_kipris_tools import LangChainKiprisTools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolInvocation
from langgraph.prebuilt.tool_executor import ToolExecutor
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

load_dotenv()
tool_class = LangChainKiprisTools()
kipris_tools = tool_class.get_tools()

llm = ChatOpenAI(model_name="gpt-4o", temperature=0.0, seed=42)

functions = [format_tool_to_openai_function(t) for t in kipris_tools]
model = llm.bind_functions(functions)

class PatentSearchState(TypedDict):
    # This tracks the team's conversation internally
    messages: t.Annotated[t.List[BaseMessage], operator.add]
    # This provides each worker with context on the others' skill sets
    team_members: str
    # This is how the supervisor tells langgraph who to work next
    next: str
    # This tracks the shared directory state
    current_files: str

## Nodes
tool_executor = ToolExecutor(kipris_tools)

def call_model(state):
    messages = state['messages']
    response = model.invoke(messages)
    return {"messages": [response]} 

def call_tool(state):
    messages = state['messages']
    last_message = messages[-1] 
    action = ToolInvocation(
        tool=last_message.additional_kwargs["function_call"]["name"],
        tool_input=json.loads(last_message.additional_kwargs["function_call"]["arguments"]),
    )
    # print(f"The agent action is {action}")
    response = tool_executor.invoke(action)
    # print(f"The tool result is: {response}")
    function_message = FunctionMessage(content=str(response), name=action.tool)
    return {"messages": [function_message]}

def should_continue(state):
    messages = state['messages']
    last_message = messages[-1]
    if "function_call" not in last_message.additional_kwargs:
        return "end"
    else:
        return "continue"