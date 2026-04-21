import asyncio
from agent.rag_agent import RAGAgent
from engine.chromadb_vector import ChromaVectorDB
from engine.runner import BenchmarkRunner

class DummyEvaluator:
    async def score(self, test_case, response):
        return {"dummy_score": 1.0}

class DummyJudge:
    async def evaluate_multi_judge(self, question, answer, expected_answer):
        return {"final_score": 5}

def main():
    vectordb = ChromaVectorDB()
    docs = [
        {"id": "doc1", "text": "Bạn có thể đổi mật khẩu trong phần cài đặt tài khoản."},
        {"id": "doc2", "text": "Để reset mật khẩu, hãy nhấn vào quên mật khẩu trên trang đăng nhập."}
    ]
    vectordb.build(docs)
    agent = RAGAgent(vectordb=vectordb, use_chroma=True)
    evaluator = DummyEvaluator()
    judge = DummyJudge()
    runner = BenchmarkRunner(agent, evaluator, judge)
    dataset = [
        {"question": "Làm thế nào để đổi mật khẩu?", "expected_answer": "Bạn có thể đổi mật khẩu trong phần cài đặt tài khoản."}
    ]
    results = asyncio.run(runner.run_all(dataset, batch_size=1))
    print(results)

if __name__ == "__main__":
    main()
