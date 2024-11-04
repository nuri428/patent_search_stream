import typing as t
import argparse
from services.simple_langgraph2.agent import supervisor, kipris_node, ds_node
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
import operator

class PatentState(t.TypedDict):
    messages: t.Annotated[t.List[BaseMessage], operator.add]
    team_members: t.List[str]
    next: str

graph = StateGraph(PatentState)
graph.add_node('patent_search', kipris_node)
graph.add_node('data_scientist', ds_node)
graph.add_node('supervisor', supervisor)

graph.add_edge('patent_search', 'supervisor')
graph.add_edge('data_scientist', 'supervisor')

graph.add_conditional_edges(
    'supervisor',
    lambda x:x['next'],
    {
        'patent_search': 'patent_search',
        'data_scientist': 'data_scientist',
        'FINISH': END,
    }
)
graph.set_entry_point('supervisor')
chain = graph.compile()

def enter_chain(message: str):
    results = {
        "messages": [HumanMessage(content=message)],
         "recursion_limit": 100,
    }
    return results


research_chain = enter_chain | chain

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", type=str, required=True)
    args = parser.parse_args()
    # print(supervisor.invoke({"messages": [HumanMessage(content=args.message)]}))
    # print(kipris_node.({"messages": [HumanMessage(content=args.message)]}))
    # print(args.message)
    step = 0
    for s in research_chain.stream(
        args.message, {"recursion_limit": 100}
    ):
        if "__end__" not in s:
            print(f"step {step} : {s}")
            step += 1
        print("---")
