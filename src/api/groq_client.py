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
    try:
        full_messages = []
        if system_prompt:
            full_messages.append({'role': 'system', 'content': system_prompt})

        # Trim conversation history if too long
        # Keep only last 10 messages to avoid context window errors
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        full_messages.extend(recent_messages)

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=full_messages,
            max_tokens=2048,
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        error_msg = str(e)
        print(f'Groq API error: {error_msg}')

        # Return a helpful message instead of crashing
        if '401' in error_msg or 'auth' in error_msg.lower():
            return '⚠️ API key error. Please check your Groq API key in Streamlit secrets.'
        elif '429' in error_msg or 'rate' in error_msg.lower():
            return '⚠️ Rate limit reached. Please wait 30 seconds and try again.'
        elif '413' in error_msg or 'too large' in error_msg.lower():
            return '⚠️ Conversation too long. Please start a new chat session.'
        else:
            return f'⚠️ AI service error. Please try again. Details: {error_msg[:200]}'