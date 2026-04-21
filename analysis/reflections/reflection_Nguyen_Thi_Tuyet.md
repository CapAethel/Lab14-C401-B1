# Báo cáo cá nhân - Nguyễn Thị Tuyết (Regression Gate & `main.py`)

## 1) Vai trò và phạm vi công việc
- Thành viên phụ trách phần **Regression Release Gate** trong `main.py`.
- Mục tiêu chính:
  - Hoàn thiện logic so sánh kết quả giữa `Agent_V1_Base` và `Agent_V2_Optimized`.
  - Xây dựng hàm `auto_release_gate()` để đưa ra quyết định **RELEASE** hoặc **ROLLBACK**.
  - Đảm bảo sinh đúng hai file báo cáo: `reports/summary.json` và `reports/benchmark_results.json`.

## 2) Công việc đã thực hiện
- Hoàn thiện pipeline benchmark trong `main.py`:
  - Đọc dữ liệu từ `data/golden_set.jsonl`.
  - Chạy benchmark cho hai phiên bản agent.
  - Tính các metric tổng hợp: `avg_score`, `hit_rate`, `agreement_rate`.
- Cài đặt `auto_release_gate(v1_summary, v2_summary)`:
  - So sánh chênh lệch `avg_score` và `hit_rate`.
  - Rule: chỉ **APPROVE** khi V2 không làm giảm các metric quan trọng.
  - Trả về kết quả có cấu trúc gồm `decision`, `reason`, `deltas`, `v1_metrics`, `v2_metrics`.
- Chuẩn hóa output báo cáo:
  - `reports/summary.json` chứa `metadata`, `metrics`, `regression`.
  - `reports/benchmark_results.json` chứa toàn bộ kết quả từng test case.
- Bổ sung `ensure_golden_set()` để tự tạo dữ liệu offline khi thiếu `golden_set.jsonl`, giúp pipeline chạy ổn định hơn.

## 3) Kết quả đầu ra
- Tổng số test case benchmark: **55**.
- Kết quả tại `reports/summary.json`:
  - `avg_score`: **3.1879**
  - `hit_rate`: **0.9818**
  - `agreement_rate`: **0.3818**
  - Regression decision: **ROLLBACK**
  - Delta so với V1:
    - `avg_score`: **-0.0727**
    - `hit_rate`: **0.0**

## 4) Nhận xét kỹ thuật
- Điểm mạnh:
  - Logic gate rõ ràng, dễ kiểm tra và tự động hóa cho bước release.
  - Cấu trúc JSON output phù hợp cho hậu kiểm và báo cáo nhóm.
- Hạn chế:
  - Quy tắc gate hiện tập trung vào chất lượng (score/retrieval), chưa xét latency và chi phí.
  - Dữ liệu so sánh V1/V2 đang cùng pipeline, cần tách cấu hình model/prompt rõ hơn để phản ánh thay đổi thực tế.

## 5) Bài học rút ra
- Regression gate cần định nghĩa tiêu chí chấp nhận ngay từ đầu để tránh quyết định cảm tính.
- Chất lượng không chỉ đo bằng một metric; cần theo dõi đồng thời retrieval, judge agreement, và độ ổn định.
- Báo cáo machine-readable (`summary.json`) giúp phối hợp tốt với các phần việc sau như failure analysis và kiểm thử nộp bài.

## 6) Đề xuất cải tiến cho vòng sau
- Mở rộng `auto_release_gate()` với ngưỡng tối thiểu cho:
  - `avg_score`, `hit_rate`, `agreement_rate`
  - latency trung bình
  - chi phí trên mỗi case
- Tách cấu hình V1/V2 thành hai profile độc lập để benchmark công bằng và tái lập được.
- Thêm test tự động cho gate logic (unit test cho các tình huống tăng/giảm metric).
