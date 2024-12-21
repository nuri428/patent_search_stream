from langgraph.graph import StateGraph, END
from services.hierarchical_agent_teams.kor_patent_search_team.agent import PatentSearchState, call_model, call_tool, should_continue

workflow = StateGraph(PatentSearchState)
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END
    }
)
workflow.add_edge('action', 'agent')

patent_search_chain = workflow.compile()