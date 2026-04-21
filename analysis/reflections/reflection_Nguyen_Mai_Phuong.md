# Báo cáo cá nhân - Nguyễn Mai Phương (Multi-Judge Engine)

## 1) Vai trò và phạm vi công việc
- Thành viên phụ trách phần **Multi-Judge Engine** (`engine/llm_judge.py`).
- Mục tiêu chính:
  - Cài đặt hàm `evaluate_multi_judge()` tích hợp gọi API thực tế tới ít nhất 2 model LLM (GPT-4o và Claude 3.5 Sonnet).
  - Viết logic xử lý xung đột (conflict resolution) khi điểm số của các Judge bị lệch nhau > 1 điểm, sử dụng `gpt-4-turbo` làm third judge (tie-breaker).
  - Cài đặt `check_position_bias()` để kiểm tra độ thiên vị vị trí của LLM bằng cách đổi chỗ 2 response A và B.
  - Xây dựng logic tính toán các chỉ số đồng thuận thực tế như Cohen's Kappa và Agreement Rate.

## 2) Công việc đã thực hiện
- Thiết kế và triển khai `evaluate_multi_judge`:
  - Gọi song song (async) 2 API của OpenAI (`gpt-4o`) và Anthropic (`claude-3-5-sonnet`) để lấy điểm đánh giá.
  - Bổ sung logic try-except an toàn (fallback) để xử lý khi API gặp sự cố (ví dụ: lỗi rate limit hoặc hết credit của Anthropic).
  - Tự động gọi thêm một model Tie-breaker (`gpt-4-turbo`) để phân xử và tính trung bình điểm khi độ lệch giữa 2 giám khảo lớn hơn 1.
- Triển khai `check_position_bias`:
  - Trình bày cùng 2 response dưới dạng "Forward" (A trước B sau) và "Backward" (B trước A sau).
  - Gửi prompt cho GPT-4o để đối chiếu quyết định lựa chọn, từ đó kết luận xem model có bị "Position Bias" (thiên vị luôn chọn vị trí A) hay không.
- Triển khai tính toán Metrics Đồng Thuận:
  - Cài đặt `calculate_agreement_rate`: Tính tỷ lệ đồng thuận tuyệt đối (Exact Match).
  - Cài đặt `calculate_cohens_kappa`: Áp dụng chuẩn công thức thống kê (Kappa) để tính độ đồng thuận loại trừ yếu tố ngẫu nhiên.
- Cập nhật file `requirements.txt` để thêm thư viện `anthropic`.

## 3) Kết quả đầu ra
- Script `llm_judge.py` chạy hoàn thiện và đã tích hợp thành công vào pipeline test runner chung.
- Đo lường được Agreement Rate và Cohen's Kappa thật trong suốt quá trình chạy 55 cases benchmark.
- Hệ thống giải quyết tốt tình huống Anthropic bị thiếu credit bằng cách dùng fallback và tie-breaker để tính toán chính xác điểm số cuối cùng.

## 4) Nhận xét kỹ thuật
- Điểm mạnh:
  - Sử dụng `asyncio.gather` tối ưu hoá tốc độ khi gọi 2 Judge cùng lúc.
  - Xử lý tốt các ngoại lệ API, đảm bảo hệ thống Benchmark không bị crash giữa chừng.
  - Phân xử bằng Tie-Breaker giúp kết quả Evaluation cuối cùng công bằng và có độ tin cậy cao hơn.
- Hạn chế:
  - Hiện tại, do hạn chế về Credit của Anthropic API, một phần lớn các query chưa thể tận dụng tối đa Claude để so sánh trực tiếp với GPT-4o.
  - Parsing điểm (dùng RegEx) khá hiệu quả nhưng vẫn có rủi ro nếu prompt model trả về output quá phức tạp thay vì số nguyên.

## 5) Bài học rút ra
- Việc sử dụng LLM as a Judge là một phương pháp rất mạnh nhưng cũng tồn tại rủi ro thiên vị (bias). Kiểm tra Position Bias là bước bắt buộc để chứng minh tính khách quan của hệ thống.
- Khi làm việc với nhiều Provider khác nhau (OpenAI, Anthropic), việc xử lý Exception cực kì quan trọng vì mỗi Provider có cấu trúc lỗi và Rate Limit riêng.
- Chỉ số Cohen's Kappa phản ánh thực tế sự đồng thuận tốt hơn là chỉ xem xét tỷ lệ phần trăm Exact Match.

## 6) Đề xuất cải tiến cho vòng sau
- Tích hợp thêm các Framework tối ưu parsing như `Instructor` hoặc dùng tính năng `JSON Schema / Structured Output` của OpenAI/Anthropic để luôn đảm bảo output ra đúng định dạng số.
- Có thể thử nghiệm thêm các Open-source Models qua API của Groq hoặc TogetherAI (như Llama-3-70B) làm Judge phụ thứ 3 thay vì dùng GPT-4-Turbo để tối ưu chi phí.
- Thử nghiệm việc Prompt Tuning riêng cho các tiêu chí khó nhằn (ví dụ Tone/Safety) thay vì đánh giá chung trong một prompt duy nhất.
