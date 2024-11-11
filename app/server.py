import streamlit as st

from streamlit_chat import message
# from services.patent.api import react_agent_executor
# from services.simple_langgraph.graph import app
# from services.simple_langgraph2.graph import research_chain
from services.patent.api.simplachain import call_with_tool
import os
import uuid
from langchain_teddynote import logging
logging.langsmith('patent_search')
# from icecream import ic
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN"]["endpoint"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN"]["project"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGCHAIN"]["api_key"]

st.set_page_config(page_title="🤗💬 patent_chatbot", layout="wide")
if "session_id" not in st.session_state.keys():
    st.session_state.session_id = str(uuid.uuid4())
# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": " 안녕하세요 뭘 도와 드릴까요?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function for generating LLM response
def generate_response(prompt_input):
    if st.session_state.session_id is None:
        return {"content": []}
    # history_list = st.session_state.messages
    # history_contents = []
    # for message in history_list:
    #     history_contents.append(message['content'])
    #     print(message['content'])

    # history_contents.append(prompt_input)
    # return react_agent_executor.invoke({"input": prompt_input})
    # total_history = "\n".join(history_contents)
    # config = {"configurable": {"thread_id": str(st.session_state.session_id)}}    
    # print(total_history)
    # res =  app.invoke({
    #             "messages":
    #                 [HumanMessage(content=prompt_input)],
    #             "sender": "user",
    #         })
    # res = research_chain.invoke(prompt_input)
    # return res['messages']
    res = call_with_tool(prompt_input)
    return res
# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt)
            # display_msg = ''
            # if len(response) > 0:
            #     display_msg = response[-1].content
            # else:
            #     display_msg = response.content
            st.markdown(response)

    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)