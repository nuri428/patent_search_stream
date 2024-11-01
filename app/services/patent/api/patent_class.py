import os
import pandas as pd
import typing as t
import json
from langchain_core.tools import Tool
from services.patent.api.prompt import Patent_Search_Prompt, Applicant_Search_Prompt
from .util import get_response, get_nested_key_value
from icecream import ic

os.environ["LANGSMITH_API_KEY"] = ""

# os.environ["OPENAI_VERBOSE"] = "True"
# os.environ["OPENAI_BASE_URL"] = "https://api.openai.com/v1/"

class KiprisAPI:
    def __init__(self, **kwargs):
        self.base_url = "http://plus.kipris.or.kr/openapi/rest/"
        if "api_key" in kwargs:
            self.api_key = kwargs["api_key"]
        else:
            if os.getenv("KIPRIS_API_KEY") :
                self.api_key = os.getenv("KIPRIS_API_KEY")
            else:
                raise ValueError("KIPRIS_API_KEY is not set")

    def common_call(self, sub_url:str,**params)->t.Dict:
        """
        KIPRIS API 공통 호출 서비스

        Args:
            sub_url (str): 서브 URL

        Returns:
            t.List[dict]: 응답 데이터
        """
        url = "%s%s?"%(self.base_url, sub_url)
        for k,v in params.items():
            url += "&%s=%s"%(k,v)
        url += "&accessKey=%s"%self.api_key

        print(url)
        return get_response(url)

    def applicantNameSearchInfo(self, applicant:str,
                               docs_start:int=1,
                               docs_count:int=10,
                               patent:bool=True,
                               utility:bool=True,
                               lastvalue:str="",
                               sort_spec:str="AD",
                               desc_sort:bool=False):
        suburl = "patUtiModInfoSearchSevice/applicantNameSearchInfo"
        response = self.common_call(suburl, 
                                    applicant=applicant,
                                    docsStart=str(docs_start),
                                    docsCount=str(docs_count),
                                    patent=str(patent),
                                    lastvalue=str(lastvalue),
                                    utility=str(utility),
                                    sortSpec=str(sort_spec),
                                    descSort= 'true' if desc_sort else 'false'
                                  )
        patents = get_nested_key_value(response, "response.body.items.PatentUtilityInfo")
        return pd.DataFrame(patents)

    def search(self,
               query:str,
               patent:bool=True,
               utility:bool=True,
               lastvalue:str="",
               docs_start:int=1,
               docs_count:int=10,
               desc_sort:bool=False,
               sort_spec:str="reg_date"):
        """
        KIPRIS API 검색 서비스

        Args:
            query (str): 검색어
            patent (bool): 특허 여부
            utility (bool): 특허 여부
            lastvalue (str): 특허 상태값
            docs_start (int, optional): 시작 번호. Defaults to 1.
            docs_count (int, optional): 검색결과 표시 수량. Defaults to 10.
            desc_sort (bool, optional): 내림차순 여부. Defaults to False.
            sort_spec (str, optional): 정렬 기준. Defaults to "reg_date".
        """
        # api url https://plus.kipris.or.kr/portal/data/service/DBII_000000000000001/view.do?menuNo=200100&kppBCode=&kppMCode=&kppSCode=&subTab=SC001&entYn=N&clasKeyword=#soap_ADI_0000000000010162

        suburl = "patUtiModInfoSearchSevice/freeSearchInfo"
        response = self.common_call(suburl, word=query,
                                  patent="true" if patent else "false",
                                  utility="true" if utility else "false",
                                  docsStart=str(docs_start),
                                  docsCount=str(docs_count),
                                  lastvalue=str(lastvalue))        
        patents = get_nested_key_value(response, "response.body.items.PatentUtilityInfo")
        return pd.DataFrame(patents)

class KiprisAPIWraper(KiprisAPI):
    def search_wrapper(self, params:str):
        params = json.loads(params)
        result = self.search(**params)
        if result.empty:
            return json.dumps({"msg":"no result"})
        else:
            ic(result.columns)
            result.drop(columns=["DrawingPath", "ThumbnailPath"], inplace=True)
            return result.to_json(orient="records", force_ascii=False)

    def applicantNameSearchInfo_wrapper(self, params:str):
        params = json.loads(params)
        result = self.applicantNameSearchInfo(**params)
        if result.empty:
            return json.dumps({"msg":"no result"})
        else:
            result.drop(columns=["DrawingPath", "ThumbnailPath"], inplace=True)
            return result.to_json(orient="records", force_ascii=False)


class KiprisAPITool:
    _kipris_api: KiprisAPIWraper

    def __init__(self, kipris_api:t.Optional[KiprisAPIWraper]=None):
        if kipris_api is None:
            raise ValueError("KIPRIS API is not set")
        else:
            self._kipris_api = kipris_api

    def tools(self) -> t.List[Tool]:
        tools = []
        tools.append(Tool.from_function(
            self._kipris_api.search_wrapper,
            name="search_patent",
            description=Patent_Search_Prompt,
            verbose=True
        ))
        tools.append(Tool.from_function(
            self._kipris_api.applicantNameSearchInfo_wrapper,
            name="search_applicant",
            description=Applicant_Search_Prompt,
            verbose=True
        ))
        return tools