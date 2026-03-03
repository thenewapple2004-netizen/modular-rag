from llm import llm_response

def router(query: str, has_web_context: bool = False, chat_history: list = None):
    history_str = ""
    if chat_history:
        for msg in chat_history[-4:]: # Only need the last few turns for context
            history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
            
    context_instruction = ""
    if has_web_context:
        context_instruction = (
            "IMPORTANT: The user has previously shared a URL and its extracted content is loaded in memory. "
            "If their query sounds like a follow-up about 'it', 'the page', the article, or asks a question related to the webpage they just shared, YOU MUST return 'link_reader'."
        )
    else:
        context_instruction = (
            "IMPORTANT: There is NO URL loaded in memory. If the user asks a follow-up conversational question (e.g. 'make it simpler', 'tell me more', 'what was that?'), YOU MUST return 'vector_db'."
        )

    system_prompt = f"""
    You are a strict routing assistant. 
    
    {context_instruction}
    
    PAST CONVERSATION (For context on what "it" or "that" refers to):
    {history_str}
    
    PRIMARY RULE 1: If the user explicitly provides a URL link (starting with http:// or https://) or explicitly asks you to read or summarize a link, you MUST return "link_reader".
    
    PRIMARY RULE 2: If the user asks ANY question about AI, technical concepts (like RL, Machine Learning), or general knowledge, check if it's related to the recently shared URL. If so, return "link_reader". If not related to the URL, return "vector_db". Assume the general tech answers are in the uploaded pdf documents.
    
    PRIMARY RULE 3: ONLY use "web_search" if the user explicitly asks for "latest news," "current events," or "today's headlines."
    
    PRIMARY RULE 4: ONLY use "weather_api" if the user asks for the weather in a specific city.

    Return ONLY the exact module name ("link_reader", "vector_db", "web_search", or "weather_api"). Do not add any punctuation, conversational text, or explanation.
    """
    
    response = llm_response(query, system_prompt)
    return response.strip().lower()