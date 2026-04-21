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

import time
def main():
    vectordb = ChromaVectorDB()
    docs = [
        {"id": "doc1", "text": "Bạn có thể đổi mật khẩu trong phần cài đặt tài khoản."},
        {"id": "doc2", "text": "Để reset mật khẩu, hãy nhấn vào quên mật khẩu trên trang đăng nhập."},
        {"id": "doc3", "text": "Bạn nên sử dụng mật khẩu mạnh và không chia sẻ với ai."}
    ]
    vectordb.build(docs)
    agent = RAGAgent(vectordb=vectordb, use_chroma=True)
    evaluator = DummyEvaluator()
    judge = DummyJudge()
    runner = BenchmarkRunner(agent, evaluator, judge)
    dataset = [
        {"question": "Làm thế nào để đổi mật khẩu?", "expected_answer": "Bạn có thể đổi mật khẩu trong phần cài đặt tài khoản."},
        {"question": "Quên mật khẩu thì làm sao?", "expected_answer": "Để reset mật khẩu, hãy nhấn vào quên mật khẩu trên trang đăng nhập."},
        {"question": "Mật khẩu mạnh là gì?", "expected_answer": "Bạn nên sử dụng mật khẩu mạnh và không chia sẻ với ai."},
        {"question": "Tôi có nên chia sẻ mật khẩu không?", "expected_answer": "Bạn nên sử dụng mật khẩu mạnh và không chia sẻ với ai."},
        {"question": "Làm sao để bảo mật tài khoản?", "expected_answer": "Bạn nên sử dụng mật khẩu mạnh và không chia sẻ với ai."}
    ]
    batch_size = 5
    start = time.perf_counter()
    results = asyncio.run(runner.run_all(dataset, batch_size=batch_size))
    elapsed = time.perf_counter() - start
    print(f"Results: {results}\nTổng thời gian chạy: {elapsed:.2f}s (batch_size={batch_size})")

    # Xuất kết quả ra file markdown
    with open("results_runner.md", "w", encoding="utf-8") as f:
        f.write(f"# Kết quả Benchmark Runner\n\n")
        f.write(f"- Tổng thời gian chạy: **{elapsed:.2f}s**  (batch_size={batch_size})\n\n")
        f.write("| # | Câu hỏi | Trả lời Agent | Thời gian (s) | Status |\n")
        f.write("|---|--------|---------------|--------------|--------|\n")
        for idx, r in enumerate(results, 1):
            q = r['test_case'].replace("|", "\\|").replace("\n", " ")[:60] + ("..." if len(r['test_case']) > 60 else "")
            a = r['agent_response'].replace("|", "\\|").replace("\n", " ")[:60] + ("..." if len(r['agent_response']) > 60 else "")
            f.write(f"| {idx} | {q} | {a} | {r['latency']:.2f} | {r['status']} |\n")

if __name__ == "__main__":
    main()
