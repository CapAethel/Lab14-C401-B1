## Phân công 6 người — Lab Day 14

### 👤 Người 1 — SDG & Golden Dataset
**File:** synthetic_gen.py
- Implement `generate_qa_from_text()` dùng OpenAI/Anthropic API thật
- Tạo đủ 50+ test cases có trường `expected_retrieval_ids`
- Thêm ít nhất 10 câu hỏi adversarial/khó (red teaming)
- Đảm bảo file `data/golden_set.jsonl` đúng format

---

### 👤 Người 2 — Retrieval Evaluator
**File:** retrieval_eval.py
- Implement `evaluate_batch()` thật (hiện đang hardcode `0.85`)
- Kết nối với Vector DB thực tế để lấy `retrieved_ids`
- Kiểm tra Hit Rate & MRR có chạy đúng trên 50 cases

---

### 👤 Người 3 — Multi-Judge Engine
**File:** llm_judge.py
- Implement `evaluate_multi_judge()` gọi **cả GPT-4o lẫn Claude** thật sự
- Viết logic xử lý xung đột khi lệch > 1 điểm (dùng tie-breaker hoặc third judge)
- Implement `check_position_bias()` — đổi vị trí A/B để test bias
- Tính Cohen's Kappa / Agreement Rate thật

---

### 👤 Người 4 — Agent & Async Runner
**File:** main_agent.py + runner.py
- Thay thế `MainAgent` bằng RAG agent thực tế (kết nối LLM + Vector DB)
- Đảm bảo runner.py chạy async song song đúng (`asyncio.gather`)
- Thêm báo cáo cost: tổng token dùng, giá tiền mỗi eval case

---

### 👤 Người 5 — Regression Gate & main.py
**File:** main.py
- Hoàn thiện logic so sánh V1 vs V2 (hiện main.py bị cắt ngang)
- Viết hàm `auto_release_gate()`: so sánh `avg_score`, `hit_rate` giữa 2 version → quyết định Release/Rollback
- Sinh đúng `reports/summary.json` và `reports/benchmark_results.json`

---

### 👤 Người 6 — Failure Analysis & Tổng hợp
**File:** failure_analysis.md + check_lab.py
- Chạy benchmark, lọc các case `status: fail`
- Viết phân tích **5 Whys** chỉ ra lỗi ở đâu (Chunking? Retrieval? Prompting?)
- Đảm bảo `python check_lab.py` pass hoàn toàn
- Thu thập `reflection_[Tên_SV].md` từ các thành viên

---

### Thứ tự phụ thuộc quan trọng
```
Người 1 (golden_set.jsonl) 
    → Người 2 (retrieval_eval) + Người 4 (agent)
        → Người 3 (judge) + Người 4 (runner)
            → Người 5 (regression gate)
                → Người 6 (failure analysis)
```

Người 1 nên **bắt đầu sớm nhất** vì mọi người đều cần `golden_set.jsonl` để chạy test.