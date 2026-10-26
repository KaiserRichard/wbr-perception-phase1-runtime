# 06 — Các tình huống thử nghiệm

> **Từ khoá**
> - Thử nghiệm trên bàn (bench test) -> kiểm tra thiết bị khi chưa chạy robot tự do.
> - Vòng lặp nội bộ (loopback) -> gửi dữ liệu quay lại bộ nhận để kiểm tra đường nhận.
> - Bộ thu phát (transceiver) -> linh kiện đổi tín hiệu logic của bộ điều khiển thành tín hiệu CAN trên dây.
> - Mạng CAN (CAN bus) -> đường truyền để các nút gửi và nhận khung dữ liệu.
> - UART -> đường truyền nối tiếp giữa các bộ điều khiển.
> - ID (mã định danh) -> số cho biết loại khung hoặc thiết bị theo cách giao thức quy định.
> - ACK -> xác nhận rằng ít nhất một bộ nhận đã nhận đúng khung CAN.
> - QoS -> quy tắc gửi nhận ROS, gồm Best Effort và Reliable.
> - Cố gắng tốt nhất (Best Effort) -> cách gửi không đảm bảo gửi lại.
> - Tin cậy (Reliable) -> cách gửi có yêu cầu xác nhận tin cậy.
> - Dữ liệu hợp lệ (valid data) -> thông điệp đúng định dạng và giá trị được chấp nhận.
> - Dữ liệu cũ (stale data) -> dữ liệu không được cập nhật trong thời gian quy định.
> - Chẩn đoán (diagnostic) -> quan sát để tìm phần nào của đường dữ liệu bị lỗi.
> - Bộ phiên dịch (Agent) -> chương trình nối micro-ROS trên vi điều khiển với ROS 2.
> - micro-ROS -> phiên bản gọn của ROS 2 dành cho vi điều khiển.
> - Thông tin gợi ý (advisory) -> dữ liệu gửi để bộ điều khiển xem xét.
> - USB -> đường truyền dữ liệu qua cổng Universal Serial Bus.
> - UNCERTAIN -> trạng thái cho biết dữ liệu advisory không còn được xem là chắc chắn.

## Vì sao cần biết?
Robot có đường dữ liệu từ dây CAN hoặc USB/UART, qua phần mềm, tới logic ứng dụng. Thử từng phần khi động cơ chưa được cấp nguồn giúp biết lỗi nằm ở đâu mà chưa cần cho robot chuyển động.

## Kiểm tra từ dưới lên
Hãy hình dung kiểm tra như lần theo đường ống: trước tiên xem nguồn và dây, sau đó xem dữ liệu đi qua, cuối cùng mới xem chương trình hiểu nó ra sao.

```text
Nguồn và dây
    ↓
Byte / khung CAN
    ↓
ID, kích thước, dữ liệu
    ↓
Agent, chủ đề, QoS
    ↓
Kiểm tra dữ liệu và thời hạn
    ↓
Trạng thái ứng dụng (động cơ vẫn tắt)
```

Thử CAN loopback trên bộ gá riêng: gửi khung mẫu, rồi kiểm tra loại ID, độ dài dữ liệu và từng byte nhận được. Mạng CAN cần điện trở kết thúc ở hai đầu; bài đầy đủ khuyên không nối nhầm thêm một điện trở.

Thử micro-ROS trên Nucleo F446RE: gửi các mã advisory khác nhau để kiểm tra đèn báo. Gửi mảng sai độ dài hoặc có giá trị không phải số hay vô hạn để xác nhận firmware không chấp nhận dữ liệu sai; ngừng gửi quá 300 ms để xem báo trạng thái cũ theo cấu hình của bộ nhận F446.

Thử tương thích QoS: bên phát advisory dùng Best Effort. Một bên nhận yêu cầu Reliable không tương thích; bên nhận Best Effort là trường hợp so sánh phù hợp.

Với thử nghiệm trên mạng robot, bộ giám sát CAN ở chế độ chỉ nghe để không ACK hay phát lệnh. Thử nghiệm bộ nhận trên H7 phải dùng đúng bản firmware và cấu hình đường truyền đã được kiểm tra; bài đầy đủ lưu ý cấu hình USB của AGV không chứng minh WBR H7 cũng dùng USB.

## Ví dụ nhỏ
F446 nhận mảng advisory gồm đúng 8 số hữu hạn: đó là trường hợp hợp lệ theo giao diện trong bài đầy đủ. Nếu nguồn dừng gửi lâu hơn 300 ms, bộ nhận chuyển trạng thái sang UNCERTAIN; thời gian được đo bởi STM32.

## Tự kiểm tra
1. Có bật động cơ trong thử kiểm tra bộ nhận H7 không?
2. Bộ nhận yêu cầu Reliable có khớp bên phát Best Effort không?
3. Sau khi nhận dữ liệu thô đúng nhưng giải mã sai, nên xem gì?

<details>
<summary>Đáp án</summary>

1. Không.
2. Không.
3. Loại ID, độ dài và cách sắp byte.

</details>

## Muốn đọc sâu hơn
[Bài đầy đủ: Các tình huống thử nghiệm](../06_test_scenarios.md).
