import functools
import operator

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai.chat_models import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from typing import Annotated, List, TypedDict
from services.hierarchical_agent_teams.common import agent_node, create_team_supervisor
# from services.hierarchical_agent_teams.research_team.tools import tavily_tool, scrape_webpages
from services.patent_search.tools import kirpis_tools
# ResearchTeam graph state
class ResearchTeamState(TypedDict):
    # A message is added after each team member finishes
    messages: Annotated[List[BaseMessage], operator.add]
    # The team members are tracked so they are aware of
    # the others' skill-sets
    team_members: List[str]
    # Used to route work. The supervisor calls a function
    # that will update this every time it makes a decision
    next: str


llm = ChatOpenAI(model="gpt-4o")

patent_search_agent = create_react_agent(llm, tools=[kirpis_tools])
patent_search_node = functools.partial(agent_node, agent=patent_search_agent, name="PatentSearch")

# research_agent = create_react_agent(llm, tools=[scrape_webpages])
# research_node = functools.partial(agent_node, agent=research_agent, name="WebScraper")

supervisor_agent = create_team_supervisor(
    llm,
    "You are a supervisor tasked with managing a conversation between the"
    " following workers:  PatentSearch. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH.",
    ["PatentSearch", "WebScraper"],
)