import os
import pandas as pd
import typing as t
import json
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field
from services.patent.api.prompt import Patent_Search_Prompt, Applicant_Search_Prompt
from services.patent.api.util import get_response, get_nested_key_value
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
        print(f"patents: {patents}")
        if isinstance(patents, t.Dict):
            patents = [patents]
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
                                  lastvalue=str(lastvalue),
                                  desc_sort="true" if desc_sort else "false",
                                  sprtSpec=str(sort_spec))        
        patents = get_nested_key_value(response, "response.body.items.PatentUtilityInfo")
        print(f"patents: {patents}")
        if isinstance(patents, t.Dict):
            patents = [patents]
        return pd.DataFrame(patents)


# class Patent_Search_Args(BaseModel):
#     query:str
#     patent:bool
#     utility:bool
#     lastvalue:str
#     docs_start:int
#     docs_count:int
#     desc_sort:bool
#     sort_spec:str

# class Applicant_Search_Args(BaseModel):
#     applicant:str
#     docs_start:int
#     docs_count:int
#     patent:bool
#     utility:bool
#     lastvalue:str
#     sort_spec:str
#     desc_sort:bool
from pydantic import BaseModel, Field
from typing import Optional

class Patent_Search_Args(BaseModel):
    query: str = Field("", description="Search query, default is an empty string. if this is empty, then i should ask user to input query.")
    patent: bool = Field(True, description="Include patents, default is True")
    utility: bool = Field(False, description="Include utility models, default is False")
    lastvalue:  t.Optional[str] = Field("", description="Patent registration status; leave empty for all, (A, C, F, G, I, J, R, or empty)")
    docs_start: int = Field(0, description="Start index for documents, default is 0")
    docs_count: int = Field(10, description="Number of documents to return, default is 10")
    desc_sort: bool = Field(True, description="Sort in descending order, default is True")
    sort_spec: str = Field("date", description="Field to sort by; default is 'date' (e.g., date, relevance)")


class Applicant_Search_Args(BaseModel):
    applicant: str = Field(..., description="Applicant name is required")
    docs_start: int = Field(1, description="Start index for documents, default is 1")
    docs_count: int = Field(10, description="Number of documents to return, default is 10, range is 1-30")
    patent: bool = Field(True, description="Include patents, default is True")
    utility: bool = Field(True, description="Include utility models, default is True")
    lastvalue:  t.Optional[str] = Field("", description="Patent registration status; leave empty for all, (A, C, F, G, I, J, R, or empty)")
    sort_spec: str = Field("AD", description="Sort field; default is AD")
    desc_sort: bool = Field(False, description="Sort in descending order; default is False")

class KiprisAPIWraper(KiprisAPI):
    def search_wrapper(self, params:str):
        params = json.loads(params)
        return self.search2(**params)

    def search_wrapper2(self, query:str, patent:bool, utility:bool, lastvalue:str, docs_start:int, docs_count:int, desc_sort:bool, sort_spec:str):
        result = self.search(query, patent, utility, lastvalue, docs_start, docs_count, desc_sort, sort_spec)
        if result.empty:
            return json.dumps({"msg":"no result"})
        else:
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
        
    def applicantNameSearchInfo_wrapper2(self, applicant:str, docs_start:int=1, docs_count:int=10, patent:bool=True, utility:bool=False, lastvalue:str="", sort_spec:str="AD", desc_sort:bool=False):
        result = self.applicantNameSearchInfo(applicant, docs_start, docs_count, patent, utility, lastvalue, sort_spec, desc_sort)
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
        tools.append(StructuredTool.from_function(
            self._kipris_api.search_wrapper,
            name="search_patent",
            description=Patent_Search_Prompt,
            args_schema=Patent_Search_Args,
            response_format="content",
            verbose=True
        ))
        tools.append(StructuredTool.from_function(
            self._kipris_api.applicantNameSearchInfo_wrapper,
            name="search_applicant",
            description=Applicant_Search_Prompt,
            args_schema=Applicant_Search_Args,
            response_format="content",
            verbose=True
        ))
        return tools