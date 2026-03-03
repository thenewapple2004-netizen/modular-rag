import chromadb
import os

def get_context(user_query):
    # Use absolute path to ensure we always read from the correct folder
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_or_create_collection(name="my-collection")

    context = collection.query(
        query_texts=[user_query],
        n_results=5
    )
    return "\n".join(context["documents"][0])