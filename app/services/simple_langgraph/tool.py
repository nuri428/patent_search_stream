from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

python_repl = PythonREPL()

@tool
def python_repl_tool(code: str) -> str:
    """
    Python 코드를 실행하는 도구
    """
    try :
        result = python_repl.run(code)
    except BaseException as e:
        return f"Failed to execute code: {e}"
    return f"Successfully executed code: {result}"

