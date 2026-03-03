from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY", "dummy-key-to-prevent-startup-crash"),
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
        max_tokens=500,
    )
    return response.choices[0].message.content