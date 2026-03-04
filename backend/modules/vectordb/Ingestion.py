import chromadb
import fitz  # pymupdf — much better PDF extraction than PyPDF2
import os

# ── Paths (all relative — works locally AND on Render) ────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(BASE_DIR, "chroma_db")
PDF_PATH  = os.path.join(BASE_DIR, "rl_document.pdf")

# ── ChromaDB setup ─────────────────────────────────────────────────────────────
chroma_client = chromadb.PersistentClient(path=DB_PATH)
collection    = chroma_client.get_or_create_collection(name="my-collection")

# ── Skip if already ingested (avoids re-embedding on every server restart) ─────
existing_count = collection.count()
if existing_count > 0:
    print(f"[Ingestion] Skipped — {existing_count} chunks already in ChromaDB.")
else:
    print(f"[Ingestion] Starting... PDF: {PDF_PATH}")

    # ── Extract text with pymupdf (handles complex layouts, tables, multi-column) ─
    doc       = fitz.open(PDF_PATH)
    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text("text")       # plain text extraction
        if text.strip():
            full_text += text + "\n"
    page_count = doc.page_count
    doc.close()

    print(f"[Ingestion] Extracted {len(full_text):,} characters from {page_count} pages.")

    # ── Chunk with overlap ─────────────────────────────────────────────────────
    CHUNK_SIZE = 1000   # characters
    OVERLAP    = 150    # characters carried over to next chunk for continuity

    words   = full_text.split()
    chunks  = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= CHUNK_SIZE:
            current += word + " "
        else:
            chunk = current.strip()
            if chunk:
                chunks.append(chunk)
            # Start next chunk with overlap tail
            overlap_text = current[-OVERLAP:].strip()
            current = overlap_text + " " + word + " "

    if current.strip():
        chunks.append(current.strip())

    print(f"[Ingestion] Created {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={OVERLAP}).")

    # ── Add to ChromaDB ────────────────────────────────────────────────────────
    chunk_ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(ids=chunk_ids, documents=chunks)
    print(f"[Ingestion] ✅ Done — {len(chunks)} chunks stored in ChromaDB.")


if __name__ == "__main__":
    # When run directly (forced re-ingest), clear first then re-run
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        print(f"[Force Re-ingest] Cleared {len(existing['ids'])} old chunks.")
    # Re-run by temporarily clearing and calling again — handled above by count check
