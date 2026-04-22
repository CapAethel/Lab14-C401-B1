# Báo cáo cá nhân - Chu Bá Tuấn Anh (Retrieval Evaluator)

## 1) Vai trò và phạm vi công việc
- Đảm nhận vị trí **Person 2 — Retrieval Evaluator** trong Lab Day 14.
- Mục tiêu chính:
  - Hoàn thiện `evaluate_batch()` trong `engine/retrieval_eval.py` (thay cho logic hardcode).
  - Kết nối logic retrieval thực tế để lấy `retrieved_ids`.
  - Tính đúng các chỉ số **Hit Rate** và **MRR** trên toàn bộ golden dataset.

## 2) Công việc đã thực hiện
- Triển khai class `InMemoryVectorDB` với cơ chế TF-IDF + cosine similarity:
  - Tokenize dữ liệu bằng regex Unicode.
  - Tính IDF theo toàn bộ tập docs.
  - Chuẩn hóa vector và search theo `top_k`.
- Hoàn thiện các hàm metric trong `RetrievalEvaluator`:
  - `calculate_hit_rate()`: trả `1.0` khi có ít nhất 1 expected id xuất hiện trong top-k.
  - `calculate_mrr()`: tính reciprocal rank của document đúng đầu tiên.
- Cài đặt `evaluate_batch()` end-to-end:
  - Build lại kho docs từ dataset.
  - Tự động fallback retrieval khi case chưa có `retrieved_ids`.
  - Tổng hợp và trả về `avg_hit_rate`, `avg_mrr`, `total_cases`.

## 3) Kết quả đầu ra
- Chạy benchmark trên **55 test cases**.
- Kết quả retrieval tổng hợp:
  - `avg_hit_rate`: **0.9818**
  - `avg_mrr`: **0.9424**
- Quan sát chi tiết:
  - Chỉ có **1 case** miss hoàn toàn (`hit_rate = 0`).
  - Có **5 cases** tài liệu đúng không đứng hạng 1 (MRR < 1), cho thấy còn dư địa tối ưu ranking.

## 4) Nhận xét kỹ thuật
- Điểm mạnh:
  - Logic metric rõ ràng, tách riêng thành các hàm dễ test.
  - `evaluate_batch()` có cơ chế fallback nên pipeline vẫn chạy ổn ngay cả khi thiếu `retrieved_ids` từ agent.
  - In-memory retrieval nhẹ, phù hợp để benchmark nhanh trong môi trường lab.
- Hạn chế:
  - TF-IDF chưa hiểu ngữ nghĩa sâu như embedding-based vector DB.
  - Kết quả retrieval phụ thuộc nhiều vào overlap từ vựng nên có thể hụt ở các câu hỏi paraphrase mạnh.

## 5) Bài học rút ra
- Với bài toán RAG, **Hit Rate cao chưa đủ**; thứ hạng tài liệu đúng (MRR) quyết định trực tiếp chất lượng câu trả lời cuối.
- Việc chuẩn hóa output retrieval (`retrieved_ids`) giữa Agent và Evaluator là rất quan trọng để tránh sai lệch metric.
- Cần đánh giá retrieval bằng cả metric tổng hợp và inspection từng case miss để tìm đúng điểm nghẽn.

## 6) Đề xuất cải tiến cho vòng sau
- Nâng cấp từ TF-IDF sang vector DB thực thụ (ChromaDB + OpenAI embeddings) để cải thiện semantic retrieval.
- Bổ sung bước reranking cho top-k candidates nhằm tăng MRR.
- Thêm unit test cho `calculate_hit_rate`, `calculate_mrr`, và integration test cho `evaluate_batch()` với dataset mẫu nhiều edge cases.
