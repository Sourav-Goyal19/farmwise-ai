# python -m venv .venv
# .venv/Scripts/activate
# ctrl+shift+p -> python: select interpretator -> Enter path -> .venv/Scripts/python.exe
# pip install -r requirements.txt
# pip freeze > requirements.txt
# python -m streamlit run app.py

import streamlit as st
from dotenv import load_dotenv
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY is not set in the .env file.")
    st.stop()

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    api_key=api_key
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}")
])

chain = prompt | llm

st.title("💬 Gemini Chat with LangChain")

user_input = st.text_input("Ask something:", "")

if user_input:
    with st.spinner("Thinking..."):
        try:
            response = chain.invoke({"input": user_input})
            output = response.content if hasattr(response, "content") else response
            st.markdown("### 🤖 Response:")
            st.write(output)
        except Exception as e:
            st.error(f"Something went wrong: {e}")
