import chromadb
import fitz
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "modules", "vectordb")
DB_PATH  = os.path.join(BASE_DIR, "chroma_db")
PDF_PATH = os.path.join(BASE_DIR, "rl_document.pdf")

client = chromadb.PersistentClient(path=DB_PATH)
col    = client.get_or_create_collection("my-collection")

# Clear old data
existing = col.get()
if existing["ids"]:
    col.delete(ids=existing["ids"])
    print(f"Cleared {len(existing['ids'])} old chunks")

# Extract with pymupdf
doc = fitz.open(PDF_PATH)
full_text = ""
for page in doc:
    t = page.get_text("text")
    if t.strip():
        full_text += t + "\n"
print(f"Extracted {len(full_text):,} chars from {doc.page_count} pages")

# Chunk with overlap
CHUNK_SIZE, OVERLAP = 1000, 150
words   = full_text.split()
chunks  = []
current = ""
for word in words:
    if len(current) + len(word) + 1 <= CHUNK_SIZE:
        current += word + " "
    else:
        if current.strip():
            chunks.append(current.strip())
        current = current[-OVERLAP:].strip() + " " + word + " "
if current.strip():
    chunks.append(current.strip())

print(f"Created {len(chunks)} chunks")
col.add(ids=[f"chunk_{i}" for i in range(len(chunks))], documents=chunks)
print("Ingestion done!")

# Test distances
tests = [
    "what is Reinforcement Learning",
    "advancements of reinforcement learning",
    "what is embedding in rag",
    "python programming",
]
print("\nDistance check:")
for q in tests:
    d = col.query(query_texts=[q], n_results=1)["distances"][0][0]
    status = "PASS" if d < 1.2 else "REJECT"
    print(f"  [{status}] {d:.4f}  {q}")
