# src/api/groq_client.py
import os
from groq import Groq

try:
    import streamlit as st
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

def ask(messages: list, system_prompt: str = '') -> str:
    """
    Send a conversation to the AI and get a response back.
    messages: list of {'role': 'user' or 'assistant', 'content': 'text'}
    system_prompt: instructions that shape how the AI behaves
    """
    full_messages = []
    if system_prompt:
        full_messages.append({'role': 'system', 'content': system_prompt})
    full_messages.extend(messages)

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=full_messages,
        max_tokens=2048,
        temperature=0.3,
    )

    return response.choices[0].message.content