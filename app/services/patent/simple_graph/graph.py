from langgraph.graph import StateGraph, END 
from services.patent.simple_graph.agent import kipris_model, should_continue, AgentState, call_tool 
from services.patent.simple_graph.prompt import reseved_system_msg
from langchain.schema import HumanMessage

# from services.patent.simple_graph.redis.ASyncSaver import AsyncRedisSaver
from langgraph.checkpoint.memory import MemorySaver
from langfuse.callback import CallbackHandler
from icecream import ic
import asyncio
import traceback
ic.disable()

class PatentSearcherGraph():
    def __init__(self):
        self.app = None
        self.langfuse_handler = CallbackHandler()
        self.graph = StateGraph(AgentState)
        self.memory = MemorySaver()
        self.build_graph()
        
        
    def build_graph(self):
        self._add_nodes()
        self._add_edges()
        self.app = self.graph.compile(checkpointer=self.memory)
        
    def _add_nodes(self):
        self.graph.add_node("agent", kipris_model)
        self.graph.add_node("action", call_tool)
        
        self.graph.set_entry_point("agent")
        
    def _add_edges(self):
        self.graph.add_conditional_edges(
            'agent',
            should_continue,
            {
                "continue": "action",
                "end": END
            }
        )
        self.graph.add_edge("action", 'agent')
        
        
    # @observe
    def run(self, message:str):        
        return self.app.invoke(
            # {"messages": [reseved_system_msg, HumanMessage(content=message)]},
            {"messages": [ HumanMessage(content=message)]},
            config={"callbacks": [self.langfuse_handler]}
            )   
    
    
    async def run_stream(self, message: str, session_id: str):
        try:
            print(f"session_id: {session_id}")
            config = {
                "configurable": {
                    "thread_id": session_id, 
                    # "checkpoint_ns": "patent_search",                     
                }, 
                "callbacks": [self.langfuse_handler]}
            async for event in self.app.astream_events({                
                "messages": [ reseved_system_msg, HumanMessage(content=message)]                
            }, config=config, stream_mode="messages", version="v2",             
            ):
                event_type = event["event"]
                if "data" in event:
                    if "chunk" in event["data"]:
                        if event_type == "on_chat_model_stream":
                            yield event["data"]["chunk"].content
            self.langfuse_handler.flush()        
            state = self.app.get_state(config={"configurable": {"thread_id": session_id}})
            print("---------state------------------")
            print(state.values['messages'])
            print("--------------------------------")            
        except Exception as e:
            ic(f"Streaming error: {str(e)}")
            ic(traceback.format_exc())
            # 스트리밍 중 발생할 수 있는 예외 처리
            raise Exception(f"스트리밍 처리 중 예외 발생: {str(e)}")   
    
    # def __del__(self):
    #     self.langfuse_handler.shutdown()

async def main():
    graph = PatentSearcherGraph()
    print("sync")
    response = graph.run("미국에서 삼성전자가 출원한 최신 특허 3개를 표시해줘")
    print(response['messages'][-1].content)
    
    print("async stream")
    async for chunk in graph.run_stream("미국에서 삼성전자가 출원한 최신 특허 3개를 표시해줘"):    
        print(chunk)
    
    
if __name__ == "__main__":
    asyncio.run(main())