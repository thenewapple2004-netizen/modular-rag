from openai import OpenAI
from dotenv import load_dotenv
import os

# Explicitly load .env from the same folder as this file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

def llm_response(query: str, system_prompt: str, history: list = None):
    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        messages.extend(history)
        
    messages.append({"role": "user", "content": query})
    
    response = client.chat.completions.create(
        messages=messages,
        model="llama-3.1-8b-instant",
        max_tokens=200,
    )
    return response.choices[0].message.content