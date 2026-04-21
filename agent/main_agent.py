import asyncio
from typing import List, Dict


# Đã thay thế MainAgent bằng RAGAgent thực tế
from agent.rag_agent import RAGAgent
from engine.retrieval_eval import InMemoryVectorDB

Agent = RAGAgent  # Để runner dễ import

if __name__ == "__main__":
    vectordb = InMemoryVectorDB()
    agent = RAGAgent(vectordb=vectordb)
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
