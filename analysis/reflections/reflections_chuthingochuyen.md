# Reflection Cá nhân — Chu Thị Ngọc Huyền
**Lab Day 14 — AI Evaluation Factory**
**Ngày:** 21/04/2026

---

## 1. Tôi đã làm gì trong bài lab này?

Trong bài lab này, tôi đảm nhận vai trò **Person 1 — Synthetic Data Generation (SDG)**: xây dựng bộ Golden Dataset làm nền tảng cho toàn bộ pipeline đánh giá. Cụ thể:

- **Thiết kế KNOWLEDGE_BASE** gồm 10 documents mô phỏng hệ thống tài liệu nội bộ thực tế: chính sách bảo mật, hoàn tiền, hướng dẫn kỹ thuật, vận hành, FAQ và AI assistant
- **Viết 55 test cases thủ công** (offline fallback) với đầy đủ cấu trúc: `question`, `expected_answer`, `context`, `expected_retrieval_ids`, `metadata`
- **Đa dạng hoá loại câu hỏi**: fact-check, reasoning, procedural, hallucination-bait, adversarial, ambiguous, multi-doc-reasoning, out-of-context
- **Tích hợp OpenAI generation mode** cho phép tạo cases tự động từ documents khi có API key, với offline fallback khi không có quota

---

## 2. Thống kê Golden Dataset tôi tạo ra

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

## 3. Điều tôi học được

### 3.1 Thiết kế test case là công việc cần tư duy, không phải chỉ viết câu hỏi

Ban đầu tôi nghĩ viết câu hỏi là đơn giản — chỉ cần hỏi về nội dung document. Nhưng thực tế, một test case tốt phải có:

- **`expected_retrieval_ids`** chính xác: không chỉ đúng document mà còn đúng thứ tự ưu tiên — điều này ảnh hưởng trực tiếp đến MRR
- **`expected_answer`** rõ ràng và có thể so sánh được: nếu viết quá dài hoặc diễn đạt khác với document, LLM Judge sẽ chấm thiếu chính xác
- **`context`** đủ ngắn để test case focused, không bị noise từ thông tin thừa

Ví dụ: câu hỏi *"Dùng 5 ngày thấy không vừa ý có được hoàn tiền không?"* — `expected_answer` phải là **"Không"** rõ ràng, không phải giải thích dài về chính sách, để judge có thể so sánh được.

### 3.2 Tầm quan trọng của adversarial và hallucination-bait cases

Qua benchmark, tôi thấy đây là hai loại case "lộ" điểm yếu của agent rõ nhất:

- **Hallucination-bait** (avg score 2.79): Agent bị hallucinate khi document không chứa câu trả lời rõ ràng — ví dụ hỏi về "đa thiết bị đồng thời" → agent đoán "có" trong khi KB không có thông tin này.
- **Adversarial** (avg score 3.33): Prompt injection (`"Ignore all previous instructions"`) và câu hỏi phức tạp về điều kiện ngoại lệ (không phải lỗi sản phẩm) giúp kiểm tra guardrail của agent.

Bài học: **Nên có ít nhất 20-25% cases thuộc nhóm khó/adversarial** trong một golden set để đảm bảo benchmark không bị inflated.

### 3.3 `expected_retrieval_ids` ảnh hưởng đến toàn bộ pipeline

Tôi là người xác định `expected_retrieval_ids` cho mỗi case. Nếu tôi gán sai — ví dụ thiếu 1 doc cần thiết hoặc thêm doc không liên quan — thì:
- **Hit Rate** bị tính sai → nhóm Person 2 có kết quả không đáng tin
- **Failure analysis** của nhóm Person 6 phân tích sai nguyên nhân

Điều này cho thấy **chất lượng SDG là nền tảng của toàn bộ evaluation factory** — nếu golden set sai, mọi metric downstream đều sai theo.

---

## 4. Điều tôi sẽ làm khác nếu làm lại

1. **Thêm `difficulty_rationale`** vào metadata: giải thích *tại sao* case này là hard/easy. Khi phân tích failure, rất khó phân biệt "agent kém" vs "case được thiết kế quá khó" nếu không có context này.

2. **Viết negative cases rõ ràng hơn**: Với hallucination-bait, nên thêm flag `"hallucination_risk": true` và ghi rõ thông tin *không có* trong KB. Hiện tại phải đọc lại KB để biết case nào là bẫy.

4. **Tăng số cross-doc reasoning cases**: Chỉ có 2 cases loại này là ít. Đây là loại câu hỏi thực tế nhất (người dùng thường hỏi câu hỏi liên quan đến nhiều chính sách cùng lúc), nhưng cũng khó nhất để thiết kế `expected_retrieval_ids` đúng.

---

## 5. Câu hỏi còn mở

- **Cần bao nhiêu cases để golden set có ý nghĩa thống kê?** — 55 cases có thể chưa đủ, đặc biệt với các nhóm ít (ambiguous: 2, out-of-context: 1). Confidence interval của avg score sẽ rất rộng ở nhóm nhỏ.
- **Làm thế nào để đảm bảo `expected_answer` "fair" cho cả V1 và V2?** — V2 có guardrail tiếng Việt nên câu trả lời ngắn gọn hơn. Nếu `expected_answer` viết dài, V2 sẽ bị chấm thấp hơn không phải vì kém hơn mà vì khác style.
- **Có nên include "No answer" cases nhiều hơn không?** — Chỉ có 1 out-of-context case. Thực tế người dùng hay hỏi những thứ ngoài KB, và khả năng agent từ chối đúng chỗ cũng quan trọng không kém khả năng trả lời đúng.

