# Reflection Cá nhân — Chu Thị Ngọc Huyền
**Lab Day 14 — AI Evaluation Factory**
**Ngày:** 21/04/2026

---

## 1. Engineering Contribution — Đóng góp kỹ thuật (Module SDG)

Tôi đảm nhận **Person 1 — Synthetic Data Generation**: xây dựng `data/synthetic_gen.py` và `data/golden_set.jsonl` làm nền tảng cho toàn bộ pipeline đánh giá.

**Những gì tôi build:**
- **`KNOWLEDGE_BASE`** gồm 10 documents mô phỏng hệ thống tài liệu nội bộ: 2 policy, 2 technical, 2 FAQ, 2 ops, 2 AI assistant
- **55 test cases** với đầy đủ cấu trúc `question / expected_answer / context / expected_retrieval_ids / metadata`
- **Dual-mode generation**: OpenAI API mode (4 regular + 1 adversarial per doc) + offline fallback (55 hand-written cases) khi hết quota
- **Red Teaming cases** (9 total): adversarial (prompt injection, edge case chính sách) + hallucination-bait (thông tin không có trong KB)

**Tại sao module này là nền tảng:** `expected_retrieval_ids` tôi gán cho mỗi case là ground truth cho **Hit Rate** và **MRR** của nhóm Person 2. Nếu gán sai, toàn bộ retrieval metrics sai theo — đây là điểm dễ gây lỗi cascade nhất trong pipeline.

---

## 2. Thống kê Golden Dataset

| Thuộc tính | Chi tiết |
|---|---|
| Tổng số cases | **55** |
| Số documents trong KB | **10** (2 policy, 2 technical, 2 FAQ, 2 ops, 2 AI) |
| Documents có cross-doc cases | **5 cases** từ nhiều docs |

**Phân bố theo độ khó:**
| Độ khó | Số cases | Đặc điểm |
|--------|---------|-----------|
| Easy | 27 | Câu hỏi trực tiếp, 1 document, đáp án rõ ràng |
| Medium | 12 | Cần suy luận thêm hoặc tổng hợp thông tin |
| Hard | 16 | Adversarial, hallucination-bait, multi-doc reasoning |

**Phân bố theo loại câu hỏi:**
| Loại | Số cases | Mục đích kiểm tra |
|------|---------|-------------------|
| fact-check | 25 | Độ chính xác thông tin cụ thể (số liệu, ngày tháng, điều kiện) |
| reasoning | 10 | Khả năng suy luận từ nhiều mảnh thông tin |
| procedural | 6 | Hướng dẫn từng bước có đúng thứ tự không |
| adversarial | 5 | Agent có bị trick bởi câu hỏi bẫy không |
| hallucination-bait | 4 | Agent có bịa thông tin không có trong KB không |
| ambiguous | 2 | Câu hỏi mơ hồ, nhiều cách hiểu |
| multi-doc-reasoning | 2 | Cần tổng hợp từ nhiều documents |
| out-of-context | 1 | Câu hỏi ngoài phạm vi KB |

---

## 3. Technical Depth — Kiến thức kỹ thuật

### 3.1 MRR (Mean Reciprocal Rank)

$$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$

Trong bài này, MRR = **0.903** — trung bình document đúng nằm ở rank ~1.1.

**Tại sao MRR quan trọng hơn Hit Rate?** Hit Rate chỉ hỏi "có tìm thấy không?" — nhưng nếu document đúng ở rank 3 trong khi LLM ưu tiên đọc rank 1-2, thì hit_rate = 1.0 mà câu trả lời vẫn sai. Case "đa thiết bị đồng thời" trong bài là ví dụ điển hình: Hit Rate = 1.0, document đúng ở rank 3 → agent đọc sai document → hallucinate "Có hỗ trợ đa thiết bị".

### 3.2 Cohen's Kappa — Đo độ đồng thuận thực sự

Agreement Rate đơn thuần (38.2% full agreement) không loại bỏ yếu tố ngẫu nhiên. **Cohen's Kappa** làm được điều đó:

$$\kappa = \frac{P_o - P_e}{1 - P_e}$$

Trong đó $P_o$ = tỉ lệ đồng ý quan sát được, $P_e$ = tỉ lệ đồng ý ngẫu nhiên kỳ vọng.

Thang giải thích: $\kappa$ < 0.2 = kém | 0.2–0.4 = vừa | 0.4–0.6 = khá | 0.6–0.8 = tốt | > 0.8 = rất tốt.

Bài này implement `calculate_cohens_kappa()` trong `engine/llm_judge.py`. Agreement Rate 38% trông thấp nhưng với scoring 1-5 thì $P_e$ cũng không nhỏ — kappa thực tế có thể cao hơn tỉ lệ raw agreement.

### 3.3 Position Bias trong LLM Judge

**Position Bias** là hiện tượng judge LLM có xu hướng chọn response ở vị trí đầu (A) hoặc cuối (B) bất kể chất lượng thực tế.

Cách phát hiện (implement trong `check_position_bias()`): swap vị trí A và B, nếu judge vẫn chọn cùng *vị trí* (luôn A) thì có bias. Nếu nhất quán chọn cùng *nội dung* (chọn A lần đầu, chọn B lần sau khi A/B đã đổi chỗ) thì là consistent — không có bias.

### 3.4 Trade-off Chi phí vs Chất lượng

| Judge | Cost/call (est.) | Chất lượng | Phù hợp khi |
|-------|-----------------|------------|-------------|
| GPT-4o | ~$0.005 | Cao | Evaluation chính thức |
| Claude 3.5 Sonnet | ~$0.003 | Cao | Cross-check, giảm bias |
| GPT-4o-mini | ~$0.0002 | Trung bình | CI/CD pipeline |
| Deterministic (TF-IDF offline) | $0 | Thấp nhưng consistent | Smoke test, debug |

Với 55 cases × 2 judges = 110 API calls: GPT-4o ~$0.55/run vs GPT-4o-mini ~$0.02/run (27× rẻ hơn). Trong bài này khi cả hai API không khả dụng, deterministic fallback giữ pipeline hoạt động với $0 cost — minh họa tốt cho graceful degradation trong production.

---

## 4. Problem Solving — Xử lý vấn đề thực tế

### Vấn đề 1: OpenAI API quota exhausted khi generate golden set

**Triệu chứng:** `synthetic_gen.py` crash sau 0/10 documents với `RateLimitError 429`.

**Giải pháp — Dual-mode design với graceful degradation:**

```python
try:
    pairs = await generate_with_openai()
except RateLimitError:
    pairs = generate_offline()  # fallback sang 55 hand-written cases
```

Pattern này quan trọng trong production RAG systems vì API luôn có khả năng gián đoạn — hệ thống vẫn chạy được và cho ra golden set chất lượng dù không có external dependency.

### Vấn đề 2: Claude API 404 — model không tồn tại trên key này

**Triệu chứng:** `claude-3-5-sonnet-20240620` trả về 404 liên tục. Thử nhiều model khác cũng 404.

**Giải pháp — Sentinel-based fallback trong judge:**

Dùng sentinel value (-1) để phân biệt "judge thất bại" với "judge cho điểm 0". Khi cả hai judge fail, kích hoạt **deterministic dual-judge**: một judge strict, một judge lenient — vẫn cho ra scoring phân tán từ 1.67 đến 4.33 thay vì hardcode 3.0. Logic multi-judge và conflict resolution vẫn hoạt động đầy đủ.

### Vấn đề 3: Cost tracking trả về `{}`

**Triệu chứng:** `benchmark_results.json` có `"cost": {}` — không capture được token usage.

**Root cause:** `runner.py` gọi `resp.get("cost", {})` nhưng agent trả về key `"metadata"` chứa cost info. Mismatch key không gây exception nhưng silently mất data.

**Hướng fix:**

```python
# runner.py > run_single_test()
result["cost"] = resp.get("metadata", resp.get("cost", {}))
```

Hoặc chuẩn hoá output schema của agent về 1 key duy nhất ngay từ đầu.

---

## 5. Điều tôi sẽ làm khác nếu làm lại

1. **Thêm `difficulty_rationale`** vào metadata: giải thích *tại sao* case này là hard/easy — giúp failure analysis phân biệt "agent kém" vs "case thiết kế quá khó".

2. **Thêm flag `"hallucination_risk": true`** cho hallucination-bait cases, kèm note về thông tin *không có* trong KB để dễ trace khi phân tích failure.

3. **Tăng cross-doc reasoning cases** từ 2 lên ít nhất 5–6: đây là loại câu hỏi thực tế nhất nhưng cũng khó thiết kế `expected_retrieval_ids` chính xác nhất.

4. **Viết integration test cho agent response schema**: kiểm tra output agent có đúng format (`retrieved_ids`, `metadata.cost_usd`) trước khi tích hợp với runner — tránh lỗi key mismatch như Vấn đề 3.
