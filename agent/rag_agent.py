import os
import asyncio
from typing import List, Dict, Optional

from dotenv import load_dotenv
import openai
from engine.chromadb_vector import ChromaVectorDB

load_dotenv()

class RAGAgent:
    """
    Agent thực tế: Retrieval + LLM (OpenAI)
    """
    def __init__(self, vectordb=None, model_name=None, use_chroma=False):
        env_model = os.getenv("MODEL_NAME")
        self.model_name = model_name or (env_model if env_model else "gpt-4o")
        if use_chroma:
            self.vectordb = ChromaVectorDB()
        else:
            self.vectordb = vectordb
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.aoai = openai.AsyncOpenAI(api_key=self.openai_api_key)

    async def retrieve(self, question: str, top_k: int = 3) -> List[str]:
        if self.vectordb:
            return self.vectordb.search(question, top_k=top_k)
        return []

    async def generate(self, question: str, contexts: List[str]) -> Dict:
        prompt = f"Context:\n{chr(10).join(contexts)}\n\nQuestion: {question}\nAnswer:"
        response = await self.aoai.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.2
        )
        answer = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
        return {"answer": answer, "tokens_used": tokens_used, "model": self.model_name}

    async def query(self, question: str) -> Dict:
        # 1. Retrieval
        contexts = await self.retrieve(question)
        # 2. Generation
        gen = await self.generate(question, contexts)
        return {
            "answer": gen["answer"],
            "contexts": contexts,
            "metadata": {
                "model": gen["model"],
                "tokens_used": gen["tokens_used"],
                "sources": contexts
            }
        }
