from langchain_kipris_tools import LangChainKiprisTools
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
tool_class = LangChainKiprisTools()
kipris_tools = tool_class.get_tools()
llm = ChatOpenAI(model="gpt-4o-mini")

def call_with_tool(query):
    from datetime import datetime as dt
    start = dt.now()

    llm_with_tools = llm.bind_tools(kipris_tools)
    chain = llm_with_tools 
    messages = [HumanMessage(query)]
    ai_msg = chain.invoke(messages)
    messages.append(ai_msg)

    for tool_call in ai_msg.tool_calls:
        selected_tool = {"applicant_search": kipris_tools[0], "patent_keyword_search": kipris_tools[1], "patent_search":kipris_tools[2]}[tool_call["name"].lower()]
        tool_msg = selected_tool.invoke(tool_call)
        # print(f'call {selected_tool.name}')
        # print(tool_call)
        messages.append(tool_msg)
    result = llm_with_tools.invoke(messages).content
    duration = dt.now() - start
    print(f'duration:{duration}')
    # for msg in messages:
    #     print(msg)
    return result
