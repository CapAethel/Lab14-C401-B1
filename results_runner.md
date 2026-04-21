# So sánh hiệu năng benchmark runner giữa batch_size=5 và batch_size=2

| batch_size | Tổng thời gian chạy (s) | Số lượng test case |
|------------|------------------------|--------------------|
| 2          | 11.91                  | 5                  |
| 5          | 9.05                   | 5                  |

**Nhận xét:**
- Khi tăng batch_size từ 2 lên 5, tổng thời gian benchmark giảm rõ rệt (~24%).
- Điều này chứng minh pipeline async tận dụng tốt tài nguyên, giúp tiết kiệm thời gian khi xử lý nhiều case.
# Kết quả Benchmark Runner

- Tổng thời gian chạy: **11.16s**  (batch_size=5)

| # | Câu hỏi | Trả lời Agent | Thời gian (s) | Status |
|---|--------|---------------|--------------|--------|
| 1 | Làm thế nào để đổi mật khẩu? | Để đổi mật khẩu, bạn có thể làm theo các bước sau:  1. **Tru... | 8.92 | pass |
| 2 | Quên mật khẩu thì làm sao? | Nếu bạn quên mật khẩu, bạn có thể thực hiện các bước sau để ... | 9.61 | pass |
| 3 | Mật khẩu mạnh là gì? | Một mật khẩu mạnh là mật khẩu có độ dài và độ phức tạp đủ để... | 6.83 | pass |
| 4 | Tôi có nên chia sẻ mật khẩu không? | Không, bạn không nên chia sẻ mật khẩu của mình với người khá... | 4.22 | pass |
| 5 | Làm sao để bảo mật tài khoản? | Để bảo mật tài khoản của bạn, bạn có thể thực hiện các bước ... | 6.89 | pass |
