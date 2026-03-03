import sys
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from router import router
    from modules.vectordb.generation import vectordb_answer
    from modules.tools.link_reader import read_link_and_answer, scrape_url
except ImportError as e:
    print(f"\n[Error] Could not find a required module: {e}")
    sys.exit(1)


def orchestrate(query: str, chat_history: list = None, web_content: str = "", forced_route: str = None) -> str:
    """
    Decides which tool to use and calls the appropriate module.
    If forced_route is provided, skips the LLM router entirely.
    """
    has_web_context = bool(web_content)
    if forced_route:
        route = forced_route
        print(f"[Router] → {route} (forced by frontend)")
    else:
        route = router(query, has_web_context=has_web_context, chat_history=chat_history)
        print(f"[Router] → {route}")

    if route == "vector_db":
        # Calls the full Advanced RAG pipeline
        return vectordb_answer(query, chat_history=chat_history)

    elif route == "link_reader":
        return read_link_and_answer(query, scraped_content=web_content, chat_history=chat_history)

    elif route == "web_search":
        return "[Web Search] Tool not connected yet. This will search the live internet."

    elif route == "weather_api":
        return "[Weather API] Tool not connected yet. This will fetch real-time weather data."

    else:
        return f"[Orchestrator] Unknown route received: '{route}'"


# --- Main Chat Loop ---
if __name__ == "__main__":
    print("\n" + "="*30)
    print("=== Modular RAG Orchestrator ===")
    print("="*30)
    print("Type your query below. Press Ctrl+C to exit.\n")

    chat_history = []
    active_web_content = ""

    while True:
        try:
            user_query = input("You: ").strip()
            
            # Skip empty inputs
            if not user_query:
                continue

            # 1. Native URL Extraction logic BEFORE Routing
            url_match = re.search(r'(https?://[^\s]+)', user_query)
            if url_match:
                url = url_match.group(1)
                print(f"\n[System] Found URL: {url}")
                print("[System] Extracting data through beautifulsoup HTML parsing and regex...")
                active_web_content = scrape_url(url)
                
                # Check if the user only dropped a link, or asked a question too
                clean_query = user_query.replace(url, '').strip()
                if not clean_query:
                    # User only provided link, ask for follow-up
                    print(f"\nAssistant: I have read the HTML content of the webpage and stored it in memory. What would you like to know about it?\n")
                    print("-" * 20)
                    continue
                else:
                    # User asked a question ALONG with the link
                    user_query = clean_query

            # 2. Process the query using the orchestrator function
            response = orchestrate(user_query, chat_history=chat_history, web_content=active_web_content)
            
            # Add to memory
            chat_history.append({"role": "user", "content": user_query})
            chat_history.append({"role": "assistant", "content": response})
            
            # Keep history manageable (last 5 turns, up to 10 entries)
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
            
            # Print the final answer
            print(f"\nAssistant: {response}\n")
            print("-" * 20)

        except KeyboardInterrupt:
            print("\n\nExiting. Goodbye!")
            break
        except Exception as e:
            print(f"\n[System Error]: {e}")