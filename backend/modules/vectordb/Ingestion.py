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

# 3. Better Chunking (300 characters requested)
CHUNK_SIZE = 300 
chunks = []

# Split by words to guarantee we strictly enforce the CHUNK_SIZE limit
words = full_text.split()
current_chunk = ""

for word in words:
    if len(current_chunk) + len(word) + 1 <= CHUNK_SIZE:
        current_chunk += word + " "
    else:
        chunks.append(current_chunk.strip())
        current_chunk = word + " "
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