# Báo cáo cá nhân - Nguyễn Văn Lĩnh (Failure Analysis & Tổng hợp)
**MSV:** 2A202600412

## 1) Vai trò và phạm vi công việc
- Đảm nhận vị trí **Person 6 — Failure Analysis & Tổng hợp** trong Lab Day 14.
- Mục tiêu chính:
  - Chạy benchmark với dữ liệu và model thật để lấy báo cáo kết quả.
  - Lọc các test case bị chấm trượt (`status: fail`).
  - Viết phân tích **5 Whys** để chỉ ra lỗi ở thành phần nào (Chunking, Retrieval hay Prompting).
  - Đảm bảo script `check_lab.py` pass hoàn toàn các bài kiểm tra chuyên sâu.

## 2) Công việc đã thực hiện
- Thay thế các class mô phỏng (mock) trong `main.py` bằng các component thực tế (`RAGAgent`, `RetrievalEvaluator`, `LLMJudge`).
- Thực thi toàn bộ pipeline benchmark trên tập 55 test cases.
- Phân tích chi tiết file `reports/benchmark_results.json`:
  - Trích xuất 11 test cases bị đánh giá thấp bởi Multi-Judge (Score < 3).
  - Lựa chọn 3 case nghiêm trọng nhất đại diện cho các nhóm lỗi: Hallucination, Incomplete, và Tone Mismatch.
- Cập nhật file `analysis/failure_analysis.md`:
  - Ghi nhận metrics thực tế: Hit Rate: 98.2%, LLM-Judge Score: 3.19.
  - Phân tích 5 Whys truy ngược nguyên nhân gốc rễ (Root Cause) như: thiếu Guardrails trong prompt, kích thước Chunking cố định cắt ngang bảng biểu, và phương pháp Retrieval In-memory/TF-IDF thiếu độ hiểu ngữ nghĩa sâu.
- Xác thực bằng `check_lab.py`, đảm bảo bài lab đạt 100% yêu cầu về định dạng JSON, có đủ Retrieval Metrics và Multi-Judge Metrics.

## 3) Kết quả đầu ra
- File `analysis/failure_analysis.md` hoàn chỉnh với dữ liệu thực và phân tích 3 cases lỗi sâu sắc.
- Pipeline vượt qua `python check_lab.py` với thông báo: `🚀 Bài lab đã sẵn sàng để chấm điểm!`.
- Phát hiện được 3 vấn đề Root Cause lớn trong phiên bản hiện tại để định hướng cho V3.

## 4) Nhận xét kỹ thuật
- **Điểm mạnh**: 
  - Đã kết hợp được góc nhìn từ cả RAGAS (Hit Rate, MRR) và LLM-as-a-Judge để phân tích. Ví dụ: Có case Hit Rate đạt 1.0 (tìm thấy đúng doc) nhưng Judge Score vẫn thấp (1.66) cho thấy lỗi nằm ở Generation/Prompting hoặc Chunking làm hỏng format text.
- **Hạn chế**:
  - Tỉ lệ đồng thuận của 2 Judge (GPT-4o và Claude) còn khá thấp (Agreement Rate ~ 38.2%), cho thấy cần tinh chỉnh (calibrate) lại rubric chấm điểm cho rõ ràng hơn thay vì chỉ dùng prompt đơn giản.

## 5) Bài học rút ra
- Điểm benchmark (Metric) chỉ là bề nổi để đánh giá Agent. Việc đào sâu vào từng case thất bại bằng phương pháp **5 Whys** mới chỉ ra được "nút thắt cổ chai" thực sự của hệ thống RAG (ở bộ Retriever hay Generator).
- Hallucination thường xảy ra không phải do model kém, mà do System Prompt không có Guardrails (rào cản) yêu cầu model kiềm chế khi thông tin trong context không đủ.

## 6) Đề xuất cải tiến cho vòng sau
- **Chunking**: Chuyển từ Fixed-size sang Semantic Chunking hoặc Markdown-aware Chunking để giữ nguyên cấu trúc bảng biểu.
- **Retrieval**: Nâng cấp lên ChromaDB sử dụng mô hình Embedding mạnh hơn (như `text-embedding-3-small`) và bổ sung module Reranker.
- **Prompting**: Thêm Guardrail cứng "Nếu thông tin không có trong context, hãy phản hồi là bạn không biết".
- **Judge Rubric**: Định nghĩa bộ tiêu chí (Rubric) từ 1 đến 5 điểm cụ thể hơn bằng few-shot examples để tăng Agreement Rate giữa các Judge models.
