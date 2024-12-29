from langchain_core.messages import SystemMessage

from langchain_kipris_tools import LangChainKiprisTools, LangChainKiprisForeignTools, LangChainKiprisKoreanTools

tools = LangChainKiprisTools().get_tools()
tool_names = [tool.name for tool in tools]

korean_tools = LangChainKiprisKoreanTools().get_tools()
korean_tool_names = [tool.name for tool in korean_tools]

foreign_tools = LangChainKiprisForeignTools().get_tools()
foreign_tool_names = [tool.name for tool in foreign_tools]

reseved_system_msg = SystemMessage(
    content=f"""
        you are helpful patent searcher.
        you can answer using tools.
        if user query is not related to patent, you can answer that you don't know.
        - if user want korean patent, you can use korean tools.
            - korean tools : {korean_tool_names}
        - if user want foreign patent, you can use foreign tools.
            and you may be translate user query to english or other language.
            - foreign tools : {foreign_tool_names}
        - if user want both korean and foreign patent, you can use both tools.
        tool : {tool_names}
        """
)