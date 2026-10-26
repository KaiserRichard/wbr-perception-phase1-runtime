# 02 — micro-ROS trên STM32

> **Từ khoá**
> - ROS 2 -> hệ thống phần mềm để các chương trình robot trao đổi thông điệp.
> - micro-ROS -> phiên bản gọn để vi điều khiển tham gia hệ thống ROS 2.
> - micro-ROS Agent -> bộ phiên dịch giữa STM32 và môi trường ROS 2 trên máy Linux.
> - Phần mềm trung gian (middleware) -> phần mềm giúp các chương trình trao đổi dữ liệu.
> - Chủ đề (topic) -> tên đường dữ liệu, ví dụ `/cmd_vel`.
> - Nhà xuất bản (publisher) -> phần mềm gửi dữ liệu lên chủ đề.
> - Đăng ký nhận (subscription) -> phần mềm nhận dữ liệu từ chủ đề.
> - Bộ thực thi (executor) -> bộ điều phối gọi hàm nhận dữ liệu khi có tin.
> - USB CDC -> cách USB biểu diễn kết nối như một cổng nối tiếp.
> - UART -> đường truyền nối tiếp thường dùng giữa các bộ điều khiển.
> - QoS -> quy tắc chất lượng gửi nhận, gồm cách đảm bảo và lưu tin.
> - Cố gắng tốt nhất (Best Effort) -> gửi dữ liệu mà không đảm bảo gửi lại khi thất lạc.
> - Tin cậy (Reliable) -> kiểu gửi có xác nhận và thử gửi lại.
> - Dữ liệu cũ (stale data) -> giá trị trước đó còn trong bộ nhớ dù nguồn đã ngừng gửi.
> - Timeout -> báo hết thời gian chờ khi lệnh không được cập nhật kịp.
> - RAM -> bộ nhớ tạm thời mà chương trình dùng khi đang chạy.

## Vì sao cần biết?
Robot có STM32 điều khiển động cơ và máy Linux chạy ROS 2. micro-ROS chuyển dữ liệu giữa hai bên để STM32 nhận được `/cmd_vel`; hiểu luồng này giúp tìm lỗi khi chủ đề im lặng hoặc lệnh cũ còn được dùng.

## Đường đi của tin nhắn
Hãy coi Agent như phiên dịch giữa hai người nói những “ngôn ngữ” phần mềm trung gian khác nhau. Nó chuyển tiếp và quản lý các đối tượng ROS của STM32, nhưng không tự điều khiển động cơ.

```text
ROS 2 trên máy → Agent → STM32 micro-ROS → executor → hàm nhận lệnh
      /cmd_vel         USB CDC hoặc UART
```

STM32 có thể nối máy qua USB CDC hoặc UART. Cả hai chỉ là đường chuyển byte; nội dung ROS vẫn cùng ý nghĩa. UART cần khớp tốc độ truyền và cách chia byte thành ký tự ở hai đầu.

Khi hàm nhận được gọi, nên kiểm tra dữ liệu rồi chuyển một bản lệnh gọn cho tác vụ điều khiển. Tác vụ (task) là một phần chương trình chạy độc lập theo lịch; không nên để hàm nhận tự gửi khung CAN trong ngữ cảnh executor.

QoS có hai kiểu tin cậy: Best Effort gửi nhanh nhưng không đảm bảo gửi lại; Reliable có cơ chế xác nhận và thử gửi lại. Bên nhận yêu cầu Reliable không khớp với bên gửi chỉ cung cấp Best Effort.

Agent còn phản hồi ping (kiểm tra có thể liên lạc), nhưng ping thành công không chứng minh chủ đề đúng, QoS tương thích hay lệnh còn mới. AGV trong bài đầy đủ dùng watchdog lệnh 500 ms: bộ đếm thời gian này phát hiện lệnh không được cập nhật trong khoảng đã định.

## Ví dụ nhỏ
Nếu nguồn `/cmd_vel` ngừng gửi, giá trị cuối vẫn có thể nằm trong RAM của STM32. Watchdog 500 ms của AGV phát hiện thời gian không cập nhật vượt ngưỡng và báo timeout; ping tới Agent không thay cho kiểm tra độ mới của lệnh.

## Tự kiểm tra
1. Agent có phải bộ điều khiển động cơ không?
2. Best Effort có đảm bảo gửi lại không?
3. Ping Agent có chứng minh lệnh mới không?

<details>
<summary>Đáp án</summary>

1. Không, nó chuyển tiếp và quản lý kết nối.
2. Không.
3. Không.

</details>

## Muốn đọc sâu hơn
[Bài đầy đủ: micro-ROS trên STM32](../02_micro_ros_on_stm32.md).
