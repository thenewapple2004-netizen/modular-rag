import chromadb
from PyPDF2 import PdfReader
import os

# 1. Use an Absolute Path so retrieval can always find the same DB
DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
chroma_client = chromadb.PersistentClient(path=DB_PATH)
collection = chroma_client.get_or_create_collection(name="my-collection")

# 2. Read PDF
pdf_path = r"D:\Noman Bhai AI\VectordB\ariticle\Reinforcement_Learning_Advancements_Limitations_an.pdf"
reader = PdfReader(pdf_path)
full_text = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        full_text += text + "\n"

# 3. Better Chunking (1000 characters is standard for RAG)
CHUNK_SIZE = 1000 
chunks = []

# Split by double newlines first to try and keep paragraphs together
paragraphs = full_text.split('\n\n')
current_chunk = ""

for p in paragraphs:
    if len(current_chunk) + len(p) < CHUNK_SIZE:
        current_chunk += p + "\n\n"
    else:
        chunks.append(current_chunk.strip())
        current_chunk = p + "\n\n"
if current_chunk:
    chunks.append(current_chunk.strip())

# 4. Add to DB
chunk_ids = [f"id_{i}" for i in range(len(chunks))]
print(f"Adding {len(chunks)} high-quality chunks to ChromaDB...")

collection.add(
    ids=chunk_ids,
    documents=chunks
)
print("Done. Ingestion complete.")