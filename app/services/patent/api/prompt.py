# react_prompt = """ You are an assistant that responds with a specific format. Every response should be in JSON format:
#     Action: the action to take, should be one of [{tool_names}]
#     {{
#         "Question": {input}
#         "Thought": {agent_scratchpad}
#         "Thought": "Explain your thought process here.",
#         "Action": "Specify the action name here.",
#         "Action Input": "Provide the required input for the action."
#     }}

#     Given the input: {input}
#     """
react_prompt = """
Answer the following questions as best you can. You have access to the following tools:
{tools}
Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: 

Begin!
on additional message must be korean
Question: {input}
Thought:{agent_scratchpad}
"""

Patent_Search_Prompt = """
 특허 검색 서비스
    this tool is used to search patents from KIPRIS API
    input query is a string that contains the search keywords and options
    i will parser input_query as dict.
    if search_query_and_options is empty, it does not search and return empty list

    fields :
        query : str, search keyword,
        patent: bool, include patent, search with patent then pass value true or false
        utility: bool, include utility, search with utility then pass value true or false
        lastvalue: str, patent registration status this values one of A, C, F, G, I,J,R, and empty string
            (전체:공백입력, 공개:A, 취하:C, 소멸:F, 포기:G, 무효:I, 거절:J, 등록:R)
        docs_count: int, number of documents to return, default is 10
        sort: str, sort by field, default is reg_date


    output is a list of dictionaries that contain the patent information
    Args:
        search_query_and_options (str): search keyword and options

    Returns:
        t.List[dict]: 특허 검색 결과
        each dictionary contains the following fields:
            Applicant : str, applicator
            ApplicationDate : str, application date
            ApplicationNumber : str, application number
            Abstract : str, abstract
            DrawingPath : str, drawing path
            ThumbnailPath : str, thumbnail path
            SerialNumber : str, serial number
            InventionName : str, invention name
            InternationalpatentclassificationNumber : str, international patent classification number
            OpeningDate : str, opening date
            OpeningNumber : str, opening number
            PublicNumber : str, public number
            PublicDate : str, public date
            RegistrationDate : str, registration date
            RegistrationNumber : str, registration number
            RegistrationStatus : str, registration status
"""

Applicant_Search_Prompt = """
 특허 출원인 검색 서비스
    this tool is used to search patents from KIPRIS API
    input query is a string that contains the applicant name and options
    i will parser input_query as dict.
    if search_query_and_options is empty, it does not search and return empty list

    fields :
        applicant : str, applicant name,
        patent: bool, include patent, search with patent then pass value true or false
        utility: bool, include utility, search with utility then pass value true or false
        lastvalue: str, patent registration status this values one of A, C, F, G, I,J,R, and empty string
            (전체:공백입력, 공개:A, 취하:C, 소멸:F, 포기:G, 무효:I, 거절:J, 등록:R)
        docs_count: int, number of documents to return, default is 30 maximum is 50
        docs_start: int, start index of documents to return, default is 1
            if you want to get next page, increase docs_start value
        sort_spec: str, sort by field, default is AD
            (PD-공고일자, AD-출원일자, GD-등록일자, OPD-공개일자, FD-국제출원일자, FOD-국제공개일자, RD-우선권주장일자)
        desc_sort: bool, sort by descending order, default is false


    output is a list of dictionaries that contain the patent information
    Args:
        search_query_and_options (str): search keyword and options

    Returns:
        t.List[dict]: 특허 검색 결과
        each dictionary contains the following fields:
            Applicant : str, applicator
            ApplicationDate : str, application date
            ApplicationNumber : str, application number
            Abstract : str, abstract
            DrawingPath : str, drawing path
            ThumbnailPath : str, thumbnail path
            SerialNumber : str, serial number
            InventionName : str, invention name
            InternationalpatentclassificationNumber : str, international patent classification number
            OpeningDate : str, opening date
            OpeningNumber : str, opening number
            PublicNumber : str, public number
            PublicDate : str, public date
            RegistrationDate : str, registration date
            RegistrationNumber : str, registration number
            RegistrationStatus : str, registration status

"""
