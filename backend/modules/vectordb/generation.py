import re
import sys
import os

# --- Robust Path Handling ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from llm import llm_response
from retrival import get_context

def vectordb_answer(user_query: str, chat_history: list = None) -> str:
    """
    Full Advance RAG pipeline:
    1. Pre-retrieval: Refine the query
    2. Retrieval: Get context from ChromaDB
    3. Confidence check: Score how relevant the context is
    4. Generation: Answer using context if confident enough
    """

    # --- Step 1: Pre-Retrieval — Query Refinement ---
    # FIXED INDENTATION HERE
    refine_prompt = (
      "You are a query refinement assistant. "
                "Your ONLY job is to fix spelling and grammar mistakes in the user's query. "
                "Rules:\n"
                "1. If the query is already correct, return it EXACTLY as-is — no changes, no explanation.\n"
                "2. If there are spelling or grammar mistakes, return ONLY the corrected query — nothing else.\n"
                "Do NOT add any extra words, explanations, or punctuation beyond the corrected query."
    )
    refined_query = llm_response(user_query, refine_prompt).strip()

    if refined_query.lower() != user_query.lower():
        print(f"[Pre-Retrieval] Query refined: '{user_query}' → '{refined_query}'")

    # --- Step 2: Retrieval ---
    retrieved_docs = get_context(refined_query)

    # --- Step 3: Confidence Check ---
    confidence_prompt = (
        "You are a relevance evaluator. "
        "Given a user query, the conversation memory, and a document context, output ONLY a single integer "
        "between 0 and 100 representing how confident you are (0 = not at all, "
        "100 = completely) that EITHER the document context contains enough information "
        "to answer the query OR the conversation memory contains the answer (for follow-up questions). "
        "Do NOT output anything else."
    )
    
    # Format the past conversation
    history_str = ""
    if chat_history:
        for msg in chat_history:
            history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
    if not history_str:
        history_str = "None"
            
    confidence_input = f"Past Conversation:\n{history_str}\n\nUser Query: {refined_query}\n\nDocument Context:\n{retrieved_docs}"
    raw_score = llm_response(confidence_input, confidence_prompt).strip()

    # Extract the number safely
    match = re.search(r"\d+", raw_score)
    confidence_score = int(match.group()) if match else 0
    print(f"[Confidence Check] Score: {confidence_score}/100")

    # --- Step 4: Generation ---
    if confidence_score < 80: 
        return (
            f"**Query Rejected** (Confidence Score: {confidence_score}/100)\n\n"
            "The retrieved context does not have enough information to answer "
            "your question confidently.\n\n"
            "**Please refine your query** and try again with more specific keywords "
            "or a clearer question."
        )

    system_prompt = f"""You are a helpful assistant with memory of the full conversation.
You also have access to a relevant document chunk below.

Use the DOCUMENT CONTEXT to answer questions about the topic.
Use the CONVERSATION HISTORY to answer follow-up questions like:
- "what was my last question?"
- "explain that again"
- "summarize what we talked about"

DOCUMENT CONTEXT:
{retrieved_docs}

If neither the context nor the conversation history has the answer, say: 'I don't have this information yet.'"""

    answer = llm_response(refined_query, system_prompt, history=chat_history)
    return answer