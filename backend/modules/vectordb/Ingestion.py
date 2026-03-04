import chromadb
from PyPDF2 import PdfReader
import os

# 1. Use an Absolute Path so retrieval can always find the same DB
DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
chroma_client = chromadb.PersistentClient(path=DB_PATH)
collection = chroma_client.get_or_create_collection(name="my-collection")

# Clear existing data to avoid duplicates on re-run
existing = collection.get()
if existing["ids"]:
    collection.delete(ids=existing["ids"])
    print(f"Cleared {len(existing['ids'])} existing chunks.")

# 2. Read PDF
pdf_path = r"D:\Noman Bhai AI\VectordB\ariticle\Reinforcement_Learning_Advancements_Limitations_an.pdf"
reader = PdfReader(pdf_path)
full_text = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        full_text += text + "\n"

print(f"Extracted {len(full_text)} characters from PDF.")

# 3. Chunking with overlap (1000 chars per chunk, 100-char overlap)
CHUNK_SIZE = 1000
OVERLAP = 100
chunks = []

words = full_text.split()
current_chunk = ""
last_words = []   # keep last few words for overlap

for word in words:
    if len(current_chunk) + len(word) + 1 <= CHUNK_SIZE:
        current_chunk += word + " "
    else:
        chunk = current_chunk.strip()
        if chunk:
            chunks.append(chunk)
        # Start next chunk with overlap from end of previous
        overlap_text = current_chunk[-OVERLAP:].strip()
        current_chunk = overlap_text + " " + word + " "

if current_chunk.strip():
    chunks.append(current_chunk.strip())

# 4. Add to DB
chunk_ids = [f"id_{i}" for i in range(len(chunks))]
print(f"Adding {len(chunks)} chunks to ChromaDB (chunk size: {CHUNK_SIZE}, overlap: {OVERLAP})...")

collection.add(
    ids=chunk_ids,
    documents=chunks
)
print("Done. Ingestion complete.")
