import asyncio
from typing import List, Dict


# Đã thay thế MainAgent bằng RAGAgent thực tế
from agent.rag_agent import RAGAgent
from engine.retrieval_eval import InMemoryVectorDB

Agent = RAGAgent  # Để runner dễ import

if __name__ == "__main__":
    from engine.chromadb_vector import ChromaVectorDB
    vectordb = ChromaVectorDB()
    docs = [
        {"id": "doc1", "text": "Bạn có thể đổi mật khẩu trong phần cài đặt tài khoản."},
        {"id": "doc2", "text": "Để reset mật khẩu, hãy nhấn vào quên mật khẩu trên trang đăng nhập."}
    ]
    vectordb.build(docs)
    agent = RAGAgent(vectordb=vectordb, use_chroma=True)
    async def test():
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)
    asyncio.run(test())

if __name__ == "__main__":
    agent = MainAgent()
    async def test():
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)
    asyncio.run(test())
