# test_groq.py
from src.api.groq_client import ask

# Test message — a real research question
messages = [
    {'role': 'user', 'content': 'What is the mechanism of CRISPR base editing and how does it differ from standard CRISPR-Cas9?'}
]

# System prompt — tells the AI who it is and how to respond
system = 'You are an expert research assistant for life science PhDs. Give mechanistic, detailed answers with evidence. Cite specific studies where relevant.'
# Call the function
response = ask(messages, system_prompt=system)

print('AI Response:')
print('-' * 50)
print(response)
