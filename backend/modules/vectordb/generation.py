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
    Full Advanced RAG pipeline:
    1. Pre-retrieval: Refine the query
    2. Retrieval: Get context + distance score from ChromaDB
    3. Confidence check: Use distance score (fast) + LLM score (fallback)
    4. Generation: Answer using context
    """

    # --- Step 1: Pre-Retrieval — Query Refinement ---
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
    retrieved_docs, best_distance = get_context(refined_query)
    print(f"[Retrieval] Best ChromaDB distance: {best_distance:.4f}")

    # --- Step 3: Confidence Check ---
    # Primary signal: ChromaDB cosine distance (0 = identical, 2 = completely different)
    # Distance < 1.0  → strong match, skip LLM scorer entirely
    # Distance 1.0-1.4 → borderline, ask LLM to score
    # Distance > 1.4  → likely out-of-scope

    if best_distance < 1.0:
        # Strong vector match — trust it and answer
        confidence_score = 80
        print(f"[Confidence] Fast-pass via distance ({best_distance:.3f} < 1.0) → score set to {confidence_score}")
    else:
        # Borderline or weak — ask LLM to score
        history_str = ""
        if chat_history:
            for msg in chat_history:
                history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
        if not history_str:
            history_str = "None"

        confidence_prompt = (
            "You are a relevance evaluator. "
            "Given a user query and a document context retrieved from a knowledge base, "
            "output ONLY a single integer between 0 and 100. "
            "Score 70+ if the context contains ANY useful information related to the query topic, "
            "even if incomplete. Score 40-69 if the context is partially related. "
            "Score below 40 ONLY if the context has absolutely nothing to do with the query. "
            "Do NOT output anything else — just the number."
        )
        confidence_input = (
            f"User Query: {refined_query}\n\n"
            f"Document Context:\n{retrieved_docs}"
        )
        raw_score = llm_response(confidence_input, confidence_prompt).strip()
        match = re.search(r"\d+", raw_score)
        confidence_score = int(match.group()) if match else 0
        print(f"[Confidence] LLM score: {confidence_score}/100 (distance was {best_distance:.3f})")

    # --- Step 4: Generation ---
    REJECTION_THRESHOLD = 40

    if confidence_score < REJECTION_THRESHOLD:
        return (
            f"**No relevant information found** in your documents for this query.\n\n"
            f"Your documents are about **Reinforcement Learning** — try asking something related to that topic, "
            f"such as policies, rewards, agents, Q-learning, or specific RL algorithms.\n\n"
            f"*(Confidence Score: {confidence_score}/100)*"
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
