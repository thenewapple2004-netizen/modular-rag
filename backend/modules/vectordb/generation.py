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

# Calibrated from real query distances:
#   RL in-scope  → ~0.65–0.85   (clearly in document)
#   Out-of-scope → ~1.4–1.9     (unrelated topics)
REJECTION_DISTANCE = 1.2


def build_search_query(user_query: str, chat_history: list) -> str:
    """
    Short follow-up queries ("can you give examples?", "explain more", "why?")
    have no domain keywords — they'll get a high distance score and be wrongly rejected.
    Fix: if the query is short AND we have chat history, prepend the last user
    message so ChromaDB gets a semantically complete search string.
    The original query is still used for the LLM answer.
    """
    words = user_query.strip().split()
    is_short_followup = len(words) <= 8  # short = likely a follow-up

    if is_short_followup and chat_history:
        # Find the last user turn in history
        last_user_msg = next(
            (m["content"] for m in reversed(chat_history) if m.get("role") == "user"),
            None
        )
        if last_user_msg:
            expanded = f"{last_user_msg} {user_query}"
            print(f"[Query Expanded] '{user_query}' → '{expanded[:80]}...'")
            return expanded

    return user_query


def vectordb_answer(user_query: str, chat_history: list = None) -> str:
    """
    Advanced RAG pipeline — single LLM call, fully context-aware:
    1. Query clean-up + follow-up expansion (Python, no LLM)
    2. Vector retrieval (ChromaDB, using expanded query for distance)
    3. Distance gate (reject out-of-scope queries)
    4. Grounded answer (one LLM call, strictly from document + chat memory)
    """
    chat_history = chat_history or []

    # ── Step 1: Clean up + expand follow-ups for better retrieval ─────────────
    refined_query = " ".join(user_query.strip().split())
    search_query  = build_search_query(refined_query, chat_history)

    # ── Step 2: Retrieval using the semantically-expanded query ───────────────
    retrieved_docs, best_distance = get_context(search_query)
    print(f"[Distance] {best_distance:.4f}  (threshold: {REJECTION_DISTANCE})")

    # ── Step 3: Distance check & Context Prep ─────────────────────────────────
    # If we're in a conversation (history exists), be slightly more lenient
    effective_threshold = REJECTION_DISTANCE + (0.2 if chat_history else 0.0)
    is_out_of_scope = best_distance > effective_threshold

    print(f"[Generating] Distance {best_distance:.4f} (threshold: {effective_threshold:.1f})")

    # Format conversation history explicitly in the prompt
    history_text = ""
    if chat_history:
        history_text = "\n\nCONVERSATION SO FAR:\n"
        for msg in chat_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_text += f"{role}: {msg.get('content', '')}\n"
        history_text += "\n(Use the conversation above to understand follow-ups, repeated questions, and meta-questions.)"

    # Strict fallback handling for out-of-scope queries
    out_of_scope_instruction = ""
    if is_out_of_scope:
        out_of_scope_instruction = """
[CRITICAL WARNING]: The user's query topic is NOT found in the document.
IF the user is asking a new general knowledge question (e.g., Python, math, recipes, or general RAG not in doc), YOU MUST REFUSE by saying: "⚠️ **This topic is not covered in your document.** Please ask something related to Reinforcement Learning."
HOWEVER, IF the user is asking about the chat history itself (e.g., "what did I just ask?", "what was my last question?"), answer it normally using the CONVERSATION SO FAR.
"""

    system_prompt = f"""You are an expert assistant on Reinforcement Learning, answering questions based on the provided document and conversation memory.
{history_text}

DOCUMENT CONTENT (For RL domain questions):
{retrieved_docs}
{out_of_scope_instruction}
RULES:
1. REPEATED QUESTIONS: If the user asks a question they have already asked in the CONVERSATION SO FAR (or very similar), politely say "You already asked that!" and provide only a brief summary or any NEW insights.
2. META-QUESTIONS: If the user asks about the conversation itself (e.g. "what was my previous question?"), answer accurately using the CONVERSATION SO FAR.
3. CONTEXT-AWARE: Read the CONVERSATION SO FAR carefully. For follow-ups ("give examples", "explain more"), figure out the topic from the conversation and answer using the DOCUMENT.
4. DOCUMENT-FIRST: Base your RL answers exclusively on the DOCUMENT CONTENT above.
5. HONEST GAPS: If the document doesn't cover a specific RL detail, say "Your document doesn't specifically cover this detail, but it DOES discuss..." and explain what is related.
6. COMPLETE: Always finish your sentence. Use headings/bullets for readability.

Current question: {refined_query}"""

    answer = llm_response(refined_query, system_prompt, history=chat_history, max_tokens=8000)
    return answer
