import sys
import os
import traceback
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

# Fallback error container
global_startup_error = None

# --- Render Deployment SQLite Override ---
try:
    if os.name == 'posix':
        import pysqlite3
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception as e:
    pass # Ignore override failure
# ----------------------------------------

try:
    import re
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

    @app.get("/")
    async def root_health():
        return {"status": "ok", "message": "Backend is perfectly live"}

except Exception as e:
    global_startup_error = traceback.format_exc()
    
    # Create the Fallback App that prevents Render from crashing
    app = FastAPI(title="Error Reporting API")
    
    @app.get("/")
    async def root_error():
        return PlainTextResponse("SERVER CRASHED DURING STARTUP:\n\n" + global_startup_error)
        
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all(path_name: str):
        return PlainTextResponse("SERVER CRASHED DURING STARTUP:\n\n" + global_startup_error)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    if global_startup_error:
        print("STARTUP ERROR DETECTED. LAUNCHING FALLBACK SERVER...")
        print(global_startup_error)
    uvicorn.run(app, host="0.0.0.0", port=port)
