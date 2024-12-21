from langchain_kipris_tools import LangChainKiprisTools
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
import json

tool_class = LangChainKiprisTools()
kipris_tools = tool_class.get_tools()
llm = ChatOpenAI(model="gpt-4o-mini")

def call_with_tool(query: str) -> str:
    if not query:
        return "검색어를 입력해주세요."
        
    from datetime import datetime as dt
    start = dt.now()

    try:
        llm_with_tools = llm.bind_tools(kipris_tools)
        chain = llm_with_tools 
        messages = [HumanMessage(content=query)]
        ai_msg = chain.invoke(messages)
        messages.append(ai_msg)

        # 각 도구 호출에 대한 응답 처리
        for tool_call in ai_msg.tool_calls:
            selected_tool = {
                "applicant_search": kipris_tools[0],
                "patent_keyword_search": kipris_tools[1],
                "patent_search": kipris_tools[2],
                "righter_search": kipris_tools[3],
                "application_number_search": kipris_tools[4]
            }[tool_call['name'].lower()]
            
            tool_result = selected_tool.run(tool_input=tool_call['args'])
            
            # ToolMessage로 응답 추가 (tool_call_id 포함)
            tool_msg = ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call['id']
            )
            messages.append(tool_msg)
            
        result = llm_with_tools.invoke(messages).content
        duration = dt.now() - start
        print(f'duration:{duration}')
        return result
        
    except Exception as e:
        print(f"Error in call_with_tool: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"검색 중 오류가 발생했습니다: {str(e)}"
