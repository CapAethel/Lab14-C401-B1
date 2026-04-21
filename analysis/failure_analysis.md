# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
- **Tổng số cases:** 55
- **Tỉ lệ Pass/Fail:** 44 / 11 (Pass: 80%, Fail: 20%)
- **Điểm RAGAS trung bình:**
    - Faithfulness: 1.0 (Mock/Baseline)
    - Relevancy: 1.0 (Mock/Baseline)
    - Hit Rate: 0.98
- **Điểm LLM-Judge trung bình:** 3.19 / 5.0 (Agreement Rate: ~38.2%)

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Hallucination / Sai chính sách | 4 | Agent tự suy diễn thông tin hoàn trả, hoặc sai chính sách đa thiết bị. |
| Incomplete / Thiếu thông tin | 5 | Agent trả lời chung chung hoặc bảo thiếu context dù có Hit Rate = 1.0. |
| Tone Mismatch | 2 | Agent liệt kê ID tài liệu (`kb_faq_001`) thay vì trả lời ngôn ngữ tự nhiên. |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: Hoàn tiền khi không vừa ý
1. **Symptom:** Khách hỏi "dùng 5 ngày thấy không vừa ý thì có được hoàn tiền không?", Agent trả lời là "được" và hướng dẫn quy trình.
2. **Why 1:** Agent đưa ra câu trả lời sai lệch với Ground Truth (có thể là Không hỗ trợ).
3. **Why 2:** Agent bị Hallucination, cố gắng làm hài lòng người dùng.
4. **Why 3:** System Prompt không có rule "Chỉ được trả lời những gì có trong context, nếu không có phải từ chối rõ ràng".
5. **Why 4:** Không có cơ chế ràng buộc hoặc Self-Check sau khi sinh text.
6. **Root Cause:** System Prompt thiếu Guardrail chống Hallucination về chính sách.

### Case #2: Hỏi giá Premium
1. **Symptom:** Khách hỏi "Giá Premium theo năm là bao nhiêu và tiết kiệm được bao nhiêu %", Agent trả lời "tôi cần thêm thông tin từ tài liệu kb_faq_001".
2. **Why 1:** LLM từ chối trả lời dù Hit Rate là 1.0 (đã tìm thấy tài liệu).
3. **Why 2:** Context cung cấp cho LLM có thể chứa quá nhiều text thừa, hoặc các con số bị format khó đọc (bảng biểu bị vỡ).
4. **Why 3:** Chunking size lớn và không giữ nguyên được format markdown bảng giá.
5. **Why 4:** Dùng thuật toán Chunking cố định (Fixed-size) cắt ngang câu/đoạn bảng giá.
6. **Root Cause:** Chiến lược Chunking làm mất semantic structure (bảng biểu) nên LLM không trích xuất được số liệu.

### Case #3: Hỗ trợ đa thiết bị
1. **Symptom:** Khách hỏi tài khoản Premium có hỗ trợ đa thiết bị đồng thời không, LLM trả lời "Có" nhưng bị chấm điểm rất thấp (1.66/5).
2. **Why 1:** Trả lời bị sai Ground Truth hoàn toàn (Ground Truth có thể là Không hoặc giới hạn số lượng thiết bị cụ thể).
3. **Why 2:** Retrieval MRR chỉ đạt 0.33, tức là chunk chứa đáp án chính xác bị đẩy xuống vị trí thứ 3.
4. **Why 3:** Vector DB ưu tiên các chunk có keyword "Premium", "thiết bị" nhưng lại thuộc tài liệu quảng cáo chung chung thay vì tài liệu kỹ thuật.
5. **Why 4:** Thuật toán nhúng (Embedding/TF-IDF) không hiểu được ngữ nghĩa sâu xa của "đồng thời".
6. **Root Cause:** Phương pháp Retrieval TF-IDF/In-memory quá đơn giản, không có Re-ranking để đẩy tài liệu chính xác lên vị trí đầu.

## 4. Kế hoạch cải tiến (Action Plan)
- [ ] Cập nhật System Prompt: Thêm Guardrail "Nếu thông tin không có trong context, hãy nói Tôi không biết, tuyệt đối không bịa thông tin".
- [ ] Áp dụng Semantic Chunking hoặc Markdown Chunking để giữ cấu trúc bảng biểu/giá tiền.
- [ ] Nâng cấp Vector DB sang Chroma/Qdrant với Embedding mạnh hơn (OpenAI text-embedding-3-small) và thêm Re-ranking (Cohere/BGE).
