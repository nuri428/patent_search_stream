from warnings import filterwarnings
import operator
import typing as t
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from services.simple_langgraph.agent import research_node, chart_node, ds_node, router, tool_node
from langchain_core.messages import HumanMessage, BaseMessage
import traceback
filterwarnings("ignore")
memory = MemorySaver()
class AgentState(t.TypedDict):
    messages: t.Annotated[t.Sequence[BaseMessage], operator.add]
    sender: str

## 그래프 생성
graph = StateGraph(AgentState)
graph.add_node("Researcher", research_node)
graph.add_node("Chart Generator", chart_node)
graph.add_node("Data Scientist", ds_node)
graph.add_node("call_tool", tool_node)

graph.add_conditional_edges(
    "Researcher",
    router,
    {   
        "Data Scientist": "Data Scientist",
        "continue": "Chart Generator",
        "call_tool": "call_tool",
        "end": END}
    )
graph.add_conditional_edges(
    "Chart Generator",
    router,
    {
        "Data Scientist": "Data Scientist",
        "continue": "Researcher",
        "call_tool": "call_tool",
        "end": END}
    )

graph.add_conditional_edges(
    "call_tool",
    lambda x: x["sender"],
    {
        "Researcher": "Researcher",
        "Chart Generator": "Chart Generator",
        "Data Scientist": "Data Scientist",
        "end": END
    },
)
## 그래프 컴파일
graph.set_entry_point("Researcher")
# app = graph.compile(ckpointer=memorchey)
app = graph.compile()

if __name__ == "__main__":
    # app.invoke({"messages":
    #     [HumanMessage(
    #         content="출원인이 '삼성전자'인 특허를 최근 순서대로 10개를 가져와서 핵심 키워드를 추출해서 워드 클라우드를 출력해주세요.")]})
    print(app.get_graph().draw_mermaid())
    try:
        for s in app.stream(
            {
                "messages":
                    [HumanMessage(
                        content="출원인이 '삼성전자'인 특허를 최근 순서대로 10개를 가져와서 핵심 키워드를 추출해서 워드 클라우드를 출력해주세요.")],
                "sender": "user"
            }
        ):
            print(s)
            print("-"*100)
    except Exception as e:
        traceback.print_exc()
        print(e)
