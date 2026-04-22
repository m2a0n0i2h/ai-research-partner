# src/api/groq_client.py
import os
from groq import Groq
from dotenv import load_dotenv

# This loads your API key from the .env file
load_dotenv()

# This creates a connection to the Groq AI service
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def ask(messages: list, system_prompt: str = '') -> str:
    """
    Send a conversation to the AI and get a response back.
    messages: list of {'role': 'user' or 'assistant', 'content': 'text'}
    system_prompt: instructions that shape how the AI behaves
    """
    # Build the full message list with system prompt at the start
    full_messages = []
    if system_prompt:
        full_messages.append({'role': 'system', 'content': system_prompt})
    full_messages.extend(messages)

    # Send to Groq and get response
    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=full_messages,
        max_tokens=2048,
        temperature=0.3,  # Lower = more consistent, less creative
    )

    # Extract just the text from the response
    return response.choices[0].message.content
