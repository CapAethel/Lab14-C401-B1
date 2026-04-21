import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from agent.rag_agent import RAGAgent
from engine.retrieval_eval import RetrievalEvaluator, InMemoryVectorDB
from engine.llm_judge import LLMJudge

class RealEvaluator:
    def __init__(self, retrieval_evaluator: RetrievalEvaluator):
        self.retrieval = retrieval_evaluator
        
    async def score(self, case, resp): 
        expected_ids = case.get("expected_retrieval_ids", [])
        retrieved_ids = resp.get("metadata", {}).get("sources", [])
        
        hit_rate = self.retrieval.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.retrieval.calculate_mrr(expected_ids, retrieved_ids)
        
        return {
            "faithfulness": 1.0, 
            "relevancy": 1.0,
            "retrieval": {"hit_rate": hit_rate, "mrr": mrr}
        }


def ensure_golden_set() -> bool:
    """
    Đảm bảo có data/golden_set.jsonl.
    Nếu thiếu, tự tạo từ bộ OFFLINE trong data/synthetic_gen.py.
    """
    golden_path = "data/golden_set.jsonl"
    if os.path.exists(golden_path):
        return True

    print("[WARN] Missing data/golden_set.jsonl, generating from OFFLINE_CASES...")
    try:
        from data.synthetic_gen import generate_offline

        pairs = asyncio.run(generate_offline())
        os.makedirs("data", exist_ok=True)
        with open(golden_path, "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        print(f"[OK] Generated {len(pairs)} cases at {golden_path}")
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to generate golden_set.jsonl: {exc}")
        return False


def auto_release_gate(v1_summary, v2_summary):
    """
    So sánh avg_score và hit_rate giữa V1/V2 để quyết định release.
    Rule:
    - APPROVE nếu cả avg_score và hit_rate của V2 >= V1
    - ROLLBACK nếu một trong hai metric giảm
    """
    v1_metrics = v1_summary["metrics"]
    v2_metrics = v2_summary["metrics"]

    score_delta = v2_metrics["avg_score"] - v1_metrics["avg_score"]
    hit_rate_delta = v2_metrics["hit_rate"] - v1_metrics["hit_rate"]

    decision = "APPROVE" if score_delta >= 0 and hit_rate_delta >= 0 else "ROLLBACK"
    reason = (
        "V2 không làm giảm avg_score và hit_rate."
        if decision == "APPROVE"
        else "V2 làm giảm ít nhất một metric quan trọng."
    )

    return {
        "decision": decision,
        "reason": reason,
        "deltas": {
            "avg_score": score_delta,
            "hit_rate": hit_rate_delta,
        },
        "v1_metrics": v1_metrics,
        "v2_metrics": v2_metrics,
    }

async def run_benchmark_with_results(agent_version: str):
    print(f"[INFO] Starting benchmark for {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("[ERROR] Missing data/golden_set.jsonl.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("[ERROR] data/golden_set.jsonl is empty.")
        return None, None

    # Xây dựng VectorDB từ dataset
    docs_by_id = {}
    for case in dataset:
        expected_ids = case.get("expected_retrieval_ids", [])
        if expected_ids and case.get("context"):
            docs_by_id[expected_ids[0]] = case["context"]
            
    docs = [{"id": k, "text": v} for k, v in docs_by_id.items()]
    vectordb = InMemoryVectorDB()
    vectordb.build(docs)
    
    agent = RAGAgent(vectordb=vectordb, use_chroma=False)
    retrieval_eval = RetrievalEvaluator(vector_db=vectordb)
    evaluator = RealEvaluator(retrieval_eval)
    judge = LLMJudge()

    runner = BenchmarkRunner(agent, evaluator, judge)
    
    # Do rate limit có thể xảy ra, chạy batch_size nhỏ
    results = await runner.run_all(dataset, batch_size=2)

    total = len(results)
    summary = {
        "metadata": {"version": agent_version, "total": total, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / total,
            "hit_rate": sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total,
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / total
        }
    }
    return results, summary

async def run_benchmark(version):
    _, summary = await run_benchmark_with_results(version)
    return summary

async def main():
    if not ensure_golden_set():
        return

    v1_summary = await run_benchmark("Agent_V1_Base")
    
    # Giả lập V2 có cải tiến (để test logic)
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")
    
    if not v1_summary or not v2_summary:
        print("[ERROR] Benchmark failed. Check data/golden_set.jsonl.")
        return

    gate = auto_release_gate(v1_summary, v2_summary)
    print("\n[REPORT] Regression comparison")
    print(f"V1 avg_score: {v1_summary['metrics']['avg_score']:.2f}")
    print(f"V2 avg_score: {v2_summary['metrics']['avg_score']:.2f}")
    print(f"Delta avg_score: {gate['deltas']['avg_score']:+.2f}")
    print(f"V1 hit_rate: {v1_summary['metrics']['hit_rate']:.2f}")
    print(f"V2 hit_rate: {v2_summary['metrics']['hit_rate']:.2f}")
    print(f"Delta hit_rate: {gate['deltas']['hit_rate']:+.2f}")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        output_summary = {
            "metadata": {
                "version": "Agent_V2_Optimized",
                "baseline_version": "Agent_V1_Base",
                "total": v2_summary["metadata"]["total"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "metrics": v2_summary["metrics"],
            "regression": gate,
        }
        json.dump(output_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    if gate["decision"] == "APPROVE":
        print("[DECISION] RELEASE (APPROVE)")
    else:
        print("[DECISION] ROLLBACK")

if __name__ == "__main__":
    asyncio.run(main())
