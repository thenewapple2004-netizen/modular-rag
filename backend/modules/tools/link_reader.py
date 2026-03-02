import os
import sys
import re
import requests
from bs4 import BeautifulSoup

# Add parent backend directory to path to import llm connection script
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from llm import llm_response

def scrape_url(url: str) -> str:
    """
    Extracts text from the provided URL using BeautifulSoup and regex.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Use HTML parsing
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strip out noisy tags using regex and extraction
        for script in soup(["script", "style", "nav", "footer", "aside", "header"]):
            script.extract()
            
        # Extract purely textual data
        text = soup.get_text(separator='\n', strip=True)
        
        # Use Regex to clean up excessive blank lines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Limit the characters to protect the LLM context window
        return text[:13000]
    except Exception as e:
        return f"Error extracting reading URL: {e}"

def read_link_and_answer(user_query: str, scraped_content: str, chat_history: list = None) -> str:
    """
    Given the pre-extracted scraped_content, answers the user's query.
    """
    if not scraped_content:
        return "I don't have any webpage content loaded. Please provide a link first in the chat."
    
    if scraped_content.startswith("Error"):
        return f"I had trouble reading the page. {scraped_content}"
        
    system_prompt = f"""You are a helpful reading assistant. A webpage has been successfully scraped and extracted for you below.
You also have memory of the full conversation.

Use the WEBPAGE CONTENT to answer questions, analyze, or summarize based on what the user asks.

WEBPAGE CONTENT:
----------------
{scraped_content}
----------------

If neither the context nor the conversation history has the answer, say: 'I don't see this information in the extracted webpage.'"""

    answer = llm_response(user_query, system_prompt, history=chat_history)
    return answer
