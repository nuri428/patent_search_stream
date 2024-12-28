from langchain_kipris_tools import LangChainKiprisKoreanTools
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
import json
from typing import AsyncGenerator
from langfuse.decorators import observe, langfuse_context

tool_class = LangChainKiprisKoreanTools()
kipris_tools = tool_class.get_tools()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
prompt = SystemMessage(content="""
    너는 특허 검색 도구를 사용해서 특허 검색을 도와주는 도우미야.
    질문에 애매하면 사용자에게 질문을 더 명확히 알려 달라고 요청해.
    특허를 검색해서 결과를 보일때 특허명칭은 기본적으로 표시해야 해.
""")

@observe
def call_with_tool(query: str) -> str:
    if not query:
        return "검색어를 입력해주세요."
        
    from datetime import datetime as dt
    start = dt.now()

    try:
        llm_with_tools = llm.bind_tools(kipris_tools)
        chain = llm_with_tools 
        messages = [prompt, HumanMessage(content=query)]
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

        langfuse_context.update_current_trace(
            name="patent_search"
        )
        langfuse_handler = langfuse_context.get_current_langchain_handler()

        result = llm_with_tools.invoke(messages, config={"callbacks": [langfuse_handler]}).content
        duration = dt.now() - start
        print(f'duration:{duration}')
        langfuse_handler.flush()        
        return result
        
    except Exception as e:
        print(f"Error in call_with_tool: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"검색 중 오류가 발생했습니다: {str(e)}"
    finally:
        duration = dt.now() - start
        print(f'duration:{duration}')        
        

@observe
async def call_with_tool_stream(query: str) -> AsyncGenerator[str, None]:
    if not query:
        yield "검색어를 입력해주세요."
        return
        
    from datetime import datetime as dt
    start = dt.now()

    try:
        llm_with_tools = llm.bind_tools(kipris_tools)
        chain = llm_with_tools 
        messages = [prompt, HumanMessage(content=query)]
        ai_msg = chain.invoke(messages)
        messages.append(ai_msg)

        # 각 도구 호출에 대한 응답 처리
        for tool_call in ai_msg.tool_calls:
            selected_tool = {
                kipris_tools[0].name: kipris_tools[0],
                kipris_tools[1].name: kipris_tools[1],
                kipris_tools[2].name: kipris_tools[2],
                kipris_tools[3].name: kipris_tools[3],
                kipris_tools[4].name: kipris_tools[4]
            }[tool_call['name'].lower()]
            
            tool_result = selected_tool.run(tool_input=tool_call['args'])
            
            # ToolMessage로 응답 추가 (tool_call_id 포함)
            tool_msg = ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call['id']
            )
            messages.append(tool_msg)
        langfuse_context.update_current_trace(
            name="patent_search"
        )
        langfuse_handler = langfuse_context.get_current_langchain_handler()

        async for chunk in llm_with_tools.astream(messages, config={"callbacks": [langfuse_handler]}):
            yield chunk.content        
        langfuse_handler.flush()        
        
    except Exception as e:
        print(f"Error in call_with_tool: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        yield f"검색 중 오류가 발생했습니다: {str(e)}"
        return 
    finally:
        duration = dt.now() - start
        print(f'duration:{duration}')
        
