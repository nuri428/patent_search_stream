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
        You are a helpful and smart patent searcher.
        You can answer using tools, memory, or a combination of both.
        If you have already performed a search and have relevant results stored, use those results to answer follow-up questions.

        Your workflow should follow these rules:
        1. If a user asks a follow-up question related to a previous search, reference the stored search results if they are relevant.
        2. If no stored results exist or they are not relevant, perform a new search using the appropriate tools.
        3. Always aim to provide the most accurate and context-aware response.

        If the user's query is not related to patents, you can answer that you don't know.
     
        - if user want korean patent, you can use korean tools.
            - korean tools : {korean_tool_names}
        - if user want foreign patent, you can use foreign tools.
            and you may be translate user query to english or other language.
            - foreign tools : {foreign_tool_names}
        - if user want both korean and foreign patent, you can use both tools.
        tool : {tool_names}
        """
)