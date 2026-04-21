# Báo cáo cá nhân - Hứa Quang Linh (Agent & Async Runner)
**Mã học viên: 2A202600466**
**Lab Day 14 — AI Evaluation Factory**
**Ngày:** 21/04/2026

## 1) Vai trò và phạm vi công việc
- Thành viên phụ trách phần **Agent & Async Runner** (`main_agent.py`, `runner.py`).
- Mục tiêu chính:
  - Thay thế `MainAgent` mẫu bằng RAG Agent thực tế, kết nối LLM (OpenAI) và Vector DB (ChromaDB).
  - Đảm bảo pipeline benchmark chạy song song (async) đúng chuẩn, tối ưu hiệu năng.
  - Bổ sung báo cáo cost: tổng token, giá tiền mỗi eval case (chuẩn bị cho bước tiếp theo).

## 2) Công việc đã thực hiện
- Thiết kế và triển khai `RAGAgent`:
  - Đọc biến môi trường từ `.env`, tích hợp OpenAI API và ChromaDB thực tế.
  - Xây dựng logic retrieval (Vector DB) + generation (LLM) trả về contexts, answer, metadata.
  - Đảm bảo agent trả về đúng format cho runner.
- Sửa đổi `main_agent.py`:
  - Thay thế hoàn toàn agent mẫu bằng agent thực tế.
  - Test truy vấn trực tiếp với ChromaDB và OpenAI, xác nhận hoạt động đúng.
- Kiểm tra và tối ưu `BenchmarkRunner` (`runner.py`):
  - Đảm bảo các hàm agent, evaluator, judge đều async và được await đúng cách.
  - Chạy thử nghiệm với nhiều test case, batch_size lớn (5), xác nhận pipeline chạy song song hiệu quả.
  - Log tổng thời gian thực thi, xuất kết quả ra file markdown.
- Viết script test_runner.py:
  - Tạo bộ test 5 case, chạy batch song song, xuất kết quả bảng markdown.

## 3) Kết quả đầu ra
- Agent thực tế đã tích hợp thành công với ChromaDB và OpenAI, trả về kết quả đúng format.
- Benchmark runner chạy song song, tổng thời gian benchmark giảm rõ rệt khi tăng batch_size.
- Đã sinh file `results_runner.md` chứa bảng kết quả chi tiết từng case.

## 4) Nhận xét kỹ thuật
- Điểm mạnh:
  - Agent dễ mở rộng, tách biệt retrieval/generation, dễ tích hợp các Vector DB hoặc LLM khác.
  - Pipeline async giúp tiết kiệm thời gian, tận dụng tối đa tài nguyên API.
  - Kết quả benchmark rõ ràng, dễ kiểm tra và báo cáo nhóm.
- Hạn chế:
  - Chưa tích hợp báo cáo chi phí/token chi tiết cho từng case (cần bổ sung ở bước sau).
  - Chưa kiểm thử với bộ dữ liệu lớn thực tế (golden_set.jsonl).

## 5) Bài học rút ra
- Việc thiết kế agent tách biệt retrieval/generation giúp dễ bảo trì, mở rộng và kiểm thử từng thành phần.
- Pipeline async thực sự giúp tiết kiệm thời gian benchmark khi số lượng case lớn, nhưng cần kiểm soát batch_size để tránh rate limit API.
- Việc log kết quả, thời gian, và xuất báo cáo machine-readable (markdown/json) giúp phối hợp nhóm hiệu quả và dễ dàng kiểm thử lại.
- Cần chuẩn hóa format input/output giữa các module để giảm lỗi tích hợp.

## 6) Đề xuất cải tiến cho vòng sau
- Bổ sung báo cáo chi phí (token, giá tiền) chi tiết cho từng case và tổng benchmark.
- Tích hợp thêm các loại Vector DB/LLM khác để so sánh hiệu năng và chi phí.
- Tối ưu batch_size động dựa trên tốc độ trả về và rate limit thực tế.
- Thêm unit test cho agent và runner để phát hiện lỗi sớm khi thay đổi logic.
- Kiểm thử với bộ dữ liệu lớn thực tế (golden_set.jsonl) để đánh giá khả năng mở rộng.