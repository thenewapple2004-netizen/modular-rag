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
    Optimised Advanced RAG pipeline — single LLM call:
    1. Pre-retrieval: Lightweight Python query clean-up (no LLM)
    2. Retrieval:     ChromaDB vector search
    3. Generation:    One LLM call for the final answer
    (No hard distance rejection — the LLM handles "not found" gracefully)
    """

    # ── Step 1: Clean up query ────────────────────────────────────────────────
    refined_query = " ".join(user_query.strip().split())
    print(f"[Pre-Retrieval] Query: '{refined_query}'")

    # ── Step 2: Retrieval ─────────────────────────────────────────────────────
    retrieved_docs, best_distance = get_context(refined_query)
    print(f"[Retrieval] Best ChromaDB distance: {best_distance:.4f} (informational only)")

    # ── Step 3: Generation — the only LLM call ───────────────────────────────
    print(f"[Generation] Sending to LLM...")

    system_prompt = f"""
ROLE:
You are an expert Research Assistant specialised in analysing technical documents.
You have full memory of the past conversation.

CONTEXT HANDLING:
1. RECONSTRUCT FRAGMENTS: Context is extracted from a PDF. Reconstruct split words or mangled LaTeX logically.
2. CONTINUITY: If a list ends abruptly in one chunk, look for continuation in other chunks.

RESPONSE GUIDELINES:
- GROUNDING: Base your answer on the DOCUMENT CONTEXT below.
- MEMORY: Use conversation history for follow-up questions. Never say "I don't have this" if the answer is in the chat history.
- SYNTHESIS: Synthesise information into a cohesive answer.
- STRUCTURE: Use clear headings, bold text, and bullet points.
- COMPLETENESS: Always finish your answer fully — never truncate mid-sentence or mid-list.

USER QUERY:
{refined_query}

DOCUMENT CONTEXT:
{retrieved_docs}

FINAL REMINDER: Do not hallucinate. If the context does not contain the answer, say so clearly.
"""

    answer = llm_response(refined_query, system_prompt, history=chat_history, max_tokens=8000)
    return answer

