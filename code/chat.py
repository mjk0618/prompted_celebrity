from io import BytesIO

import streamlit as st
from assistant import ChatAssistant
from openai import OpenAI
from utils import decrypt_api_key

api_key = decrypt_api_key("api.txt")

instructions = None
name = "성동일"
pdf_file_name = None
txt_file_name = None

client = ChatAssistant(name="성동일")
client.set_assistant(instructions=instructions, pdf_file=pdf_file_name, txt_file=txt_file_name) 

st.title(f"🤖 Chat Assistant Demo")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = client._retrieve_assistant(client.assistant_id).model

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

client._create_thread()

if prompt := st.chat_input(f"{name}씨와 대화를 나눠보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        responses = client.get_answers(prompt)

        for response in responses:
            full_response += response
            message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})