import sys
import os

# --- Render Deployment SQLite Override ---
# ChromaDB requires SQLite > 3.35, but Render Linux often has an older version.
# This forces the app to use the modern pysqlite3-binary if installed.
if os.name == 'posix':
    try:
        import pysqlite3
        import sys
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass
# ----------------------------------------

import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

# Add backend dir to path 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from orchestrator import orchestrate
from modules.tools.link_reader import scrape_url

app = FastAPI(title="Modular RAG API")

# Setup CORS to allow React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    chat_history: List[Dict[str, str]] = []
    web_content: Optional[str] = ""

class ChatResponse(BaseModel):
    answer: str
    web_content: Optional[str] = ""

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        user_query = request.query
        active_web_content = request.web_content

        # URL Extraction Logic
        url_match = re.search(r'(https?://[^\s]+)', user_query)
        if url_match:
            url = url_match.group(1)
            active_web_content = scrape_url(url)
            
            clean_query = user_query.replace(url, '').strip()
            if not clean_query:
                return ChatResponse(
                    answer="I have read the HTML content of the webpage and stored it in memory. What would you like to know about it?",
                    web_content=active_web_content
                )
            else:
                user_query = clean_query

        # Execute Orchestrator Logic
        response = orchestrate(
            query=user_query, 
            chat_history=request.chat_history, 
            web_content=active_web_content
        )
        
        return ChatResponse(
            answer=response,
            web_content=active_web_content
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
