# Modular RAG Architecture 🚀

Hey there! Welcome to my Modular RAG (Retrieval-Augmented Generation) project. I built this to solve a specific problem: most RAG applications are locked into one data source. I wanted a system that could dynamically route my questions not just to my local PDF documents, but dynamically scrape live URLs on the fly and answer questions about them natively.

This project combines a **FastAPI/Python backend** with a beautiful, fully responsive **React frontend** that looks and feels like a premium AI chatbot (complete with chat history, a glowing sidebar, and a dark/light mode switch!).

## ✨ Key Features
* **Smart LLM Routing:** The core engine (using Groq & LLaMA 3.1) actively decides whether your query needs to search the local Vector Database or if it needs to trigger a web-scraping tool based on what you are asking.
* **Live Web Reader Tool:** Just drop an `http` or `https` link into the chat! The backend will automatically scrape the HTML, clean it with BeautifulSoup, inject the extracted text straight into the LLM's memory context, and let you ask follow-up questions about that exact webpage.
* **Vector Document Storage:** Local document chunking and vector embeddings are stored efficiently using ChromaDB.
* **Context-Aware Memory:** The Assistant remembers up to your last 10 turns of conversation so you can ask natural follow-up questions without repeating yourself.
* **Premium React Frontend:** A custom-built UI using Vite, React, and CSS Glassmorphism. Features auto-scrolling, typing indicators, animated badges when a URL is ingested, and a 260px collapsible sidebar for session history.

## 🏗️ Folder Structure
I've cleanly separated the logic into a standard full-stack layout:
```text
modular-rag/
├── frontend/             # React App (Vite)
│   ├── src/              # App.jsx, index.css, main.jsx
│   └── package.json
│
└── backend/              # Python FastAPI Server
    ├── api.py            # Main API Endpoint (Runs on :8000)
    ├── orchestrator.py   # State Controller & Router Entrypoint
    ├── llm.py            # Groq API Connection
    ├── router.py         # The LLM Routing Logic
    ├── requirements.txt
    ├── .env              # Your API Keys belong here
    └── modules/
        ├── vectordb/     # ChromaDB Ingestion & Retrieval Logic
        │   └── chroma_db/
        └── tools/
            └── link_reader.py # The Web Scraper Module
```

## 🛠️ Getting Started

### Prerequisites
You will need Node.js installed for the frontend and Python 3.9+ installed for the backend.
You also need a free Groq API key: get it from [Groq Console](https://console.groq.com/keys).

### 1. Backend Setup (FastAPI)
1. Open a terminal and navigate to the root folder, then into the backend.
   ```bash
   cd backend
   ```
2. Create and activate a Virtual Environment (Recommended):
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```
3. Install the required Python dependencies (from the root requirements file!):
   ```bash
   pip install -r ../requirements.txt
   ```
4. Create a `.env` file inside the `backend/` folder and add your key:
   ```ini
   GROQ_API_KEY=your_super_secret_api_key_here
   ```
5. Start the backend server!
   ```bash
   uvicorn api:app --reload
   ```
   *(The API will now be listening on `http://127.0.0.1:8000`)*

### 2. Frontend Setup (React)
1. Open a *new* separate terminal window and jump into the frontend folder.
   ```bash
   cd frontend
   ```
2. Install the necessary Node modules (like React, Vite, and Lucide icons):
   ```bash
   npm install
   ```
3. Boot up the Vite development server:
   ```bash
   npm run dev
   ```
   *(The Web App will launch on `http://localhost:5173`)*

## 💡 How to use it
Once both servers are running, just open up your browser to `http://localhost:5173`. 
- **Ask a tech question:** "Explain Machine Learning" -> It routes to your VectorDB.
- **Feed it Web Data:** Paste `https://en.wikipedia.org/wiki/Box2D` into the chat -> It instantly scrapes the wiki. Then ask "What environments are listed on this page?" -> It routes to the `link_reader` tool and answers from the live website context!

## Future Roadmap 🚀
I've designed the `orchestrator.py` to be endlessly expandable. Next up:
* Connect the placeholder `web_search` and `weather_api` routing branches to actual Python tools inside the `modules/tools/` folder!
* Expand session memory storage to a local SQLite database so chat history persists between page reloads.

---
*Built with ❤️ utilizing Python, FastAPI, React, and Groq.*
