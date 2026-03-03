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
    if confidence_score < 60:
        return (
            f"**Query Rejected** (Confidence Score: {confidence_score}/100)\n\n"
            "The retrieved context does not have enough information to answer "
            "your question confidently.\n\n"
            "**Please refine your query** and try again with more specific keywords "
            "or a clearer question."
        )

    system_prompt = f"""
ROLE:
You are an expert Research Assistant specialized in analyzing technical documents. You have full memory of the past conversation context.

CONTEXT HANDLING (The "Forgiving Reader" Protocol):
1. RECONSTRUCT FRAGMENTS: The provided context is extracted from a PDF. If you encounter split words, missing symbols, or mangled LaTeX/Math, reconstruct the meaning logically.
2. CONTINUITY: If a list or explanation ends abruptly in one chunk, search other provided chunks for the continuation.

RESPONSE GUIDELINES:
- GROUNDING: Answer based on the provided DOCUMENT CONTEXT. 
- MEMORY: You MUST use the conversation history to answer follow-up questions (e.g., "explain that last point again" or "what did I just ask?"). Do not say "I don't have this information" if the answer is literally inside your chat history memory.
- SYNTHESIS: Synthesize information into a cohesive answer.
- STRUCTURE: Use clear headings, bold text, and bullet points.

USER QUERY:
{user_query}

DOCUMENT CONTEXT:
{retrieved_docs}

FINAL REMINDER: Do not hallucinate. If neither the context nor the conversation history contains the answer, explain what is missing.
"""

    answer = llm_response(refined_query, system_prompt, history=chat_history)
    return answer