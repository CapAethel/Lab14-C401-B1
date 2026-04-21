import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

class ChromaVectorDB:
    def __init__(self, collection_name="rag_collection"):
        self.client = chromadb.Client(Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(collection_name)
        self.embedder = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name=os.getenv("EMBED_MODEL", "text-embedding-3-small")
        )

    def build(self, docs):
        # docs: [{"id": ..., "text": ...}]
        ids = [doc["id"] for doc in docs]
        texts = [doc["text"] for doc in docs]
        # Tạo embedding bằng OpenAI trước khi upsert
        embeddings = self.embedder(texts)
        self.collection.upsert(ids=ids, documents=texts, embeddings=embeddings)

    def search(self, query, top_k=3):
        # Tạo embedding cho query
        query_embedding = self.embedder([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results["ids"][0] if results["ids"] else []
