import chromadb
import os

def get_context(user_query):
    # Use absolute path to ensure we always read from the correct folder
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_or_create_collection(name="my-collection")

    results = collection.query(
        query_texts=[user_query],
        n_results=5
    )
    docs = results["documents"][0]
    distances = results["distances"][0]  # lower = more similar
    context_text = "\n".join(docs)
    best_distance = min(distances) if distances else 999
    return context_text, best_distance