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

# Calibrated from real distance measurements:
#   RL in-scope queries  → ~0.7   (clearly in document)
#   RAG/other topics     → ~1.4+  (out of scope)
# Threshold of 1.2 gives clean separation with a safety margin.
REJECTION_DISTANCE = 1.2

def vectordb_answer(user_query: str, chat_history: list = None) -> str:
    """
    Advanced RAG pipeline — single LLM call:
    1. Query clean-up  (Python, no LLM)
    2. Vector retrieval (ChromaDB)
    3. Distance gate    (reject out-of-scope, no LLM)
    4. Grounded answer  (one LLM call, strictly from document)
    """

    # ── Step 1: Clean up query ────────────────────────────────────────────────
    refined_query = " ".join(user_query.strip().split())
    print(f"[Query] '{refined_query}'")

    # ── Step 2: Retrieval ─────────────────────────────────────────────────────
    retrieved_docs, best_distance = get_context(refined_query)
    print(f"[Distance] {best_distance:.4f}  (threshold: {REJECTION_DISTANCE})")

    # ── Step 3: Distance gate — reject clearly out-of-scope queries ───────────
    if best_distance > REJECTION_DISTANCE:
        print(f"[Rejected] Distance {best_distance:.4f} > {REJECTION_DISTANCE}")
        return (
            "⚠️ **This topic is not covered in your document.**\n\n"
            "Your uploaded document is about **Reinforcement Learning** — including topics like "
            "policies, rewards, agents, Q-learning, deep RL, and RL algorithms.\n\n"
            "Please ask something related to those topics."
        )

    # ── Step 4: Strictly grounded answer ─────────────────────────────────────
    print(f"[Generating] Distance {best_distance:.4f} passed gate.")

    system_prompt = f"""You are a document Q&A assistant. Your ONLY job is to answer questions using the DOCUMENT CONTEXT provided below.

STRICT RULES — you MUST follow these without exception:
1. ONLY use information that is EXPLICITLY present in the DOCUMENT CONTEXT below.
2. Do NOT use your general training knowledge, even if you know the answer from elsewhere.
3. If the DOCUMENT CONTEXT does not contain enough information to answer the question, respond with:
   "⚠️ This specific topic is not covered in your Reinforcement Learning document."
4. Never guess, infer beyond the text, or fill gaps with outside knowledge.
5. Always finish your answer completely — never truncate mid-sentence.

DOCUMENT CONTEXT:
{retrieved_docs}

USER QUERY: {refined_query}

Remember: answer ONLY from the document above. If it's not there, say so."""

    answer = llm_response(refined_query, system_prompt, history=chat_history, max_tokens=8000)
    return answer
