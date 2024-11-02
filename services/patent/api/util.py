import typing as t
import datetime
import requests
import xmltodict
import traceback
from xml.parsers.expat import ExpatError
import json
from logging import getLogger
from icecream import ic
logger = getLogger(__name__)


def get_nested_key_value(dictionary: t.Dict, nested_key: str, sep: str = ".", default_value=None) -> t.Any:
    """[get_nested_key_value]
        계측정 dict 객체에서 단계별 키를 입력하여 해당 키의 값을 가져옴.

    Args:
        nested_key ([str]): [계층적 키, 계측적 dict타입 에서 dict[A][B] 일 경우 A.B .-> sep 값 ]
        sep (str, optional): [계측정 키 구분자 ]. 기본값은 "."
        default_value ([None], optional): [계측적 키로 값 인출 실패시 넘길 기본 값]. 기본값은 None

    Returns:
        Any: [계층적 키를 통해 인출된 값, list, dict, str 혹은 None ]
    """

    if dictionary is None:
        return default_value

    try:
        current = dictionary
        for keys in nested_key.split(sep):
            if current and keys in current:
                temp = current[keys]
                current = temp
            else:
                return default_value

        if current is None and default_value is not None:
            return default_value
        else:
            return current
    except ValueError as e:
        logger.error("get_nested_key_value, %s %s value extract error", dictionary, nested_key)
        logger.error(e)
        return default_value

def get_response(url: str) -> t.Tuple[t.Any, t.Dict]:
    """_summary_
        url을 입력 받아서 해당 url에 대한 get 요청을 보내고, 결과를 json으로 반환함.
    Args:
        url (str): url 주소

    Returns:
        t.Any: url에 대한 get 요청 결과 json
    """
    response = None

    try:
        key_str = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M:%S")

        response_text = ""
        with requests.Session() as sess:
            response = sess.get(url, timeout=300)
            ic(url)
            response_text = response.text
        try:
            dict_type = xmltodict.parse(response_text)
        except ExpatError:
            logger.error("response is not xml[%s]", response_text[0:100])
            return None
        json_data = json.loads(json.dumps(dict_type))
        result_header = get_nested_key_value(json_data, "response.header", default_value="")
        logger.info("__kipris__:[%s]:[%s] :result header : [%s]",
                            key_str, url[24:], result_header)
        return json_data

    except requests.exceptions.Timeout as e:
        logger.error("timeout:[%s]", e)
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error("connectoin Error:[%s]", e)
        return None
    except requests.exceptions.HTTPError as e:
        logger.error("http Error:[%s]", e)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("request Exception Error:[%s]", e)
        return None
    except Exception as e:
        logger.error("Exception Error:[%s]", e)
        logger.error("url error [%s]", url)
        logger.error("response error [%s]", response)
        
        logger.error(traceback.format_exc())
        return None