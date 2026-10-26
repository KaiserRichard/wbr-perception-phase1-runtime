# 01 — CAN và RobStride

> **Từ khoá**
> - Mạng CAN (CAN bus) -> đường truyền chung để nhiều bộ điều khiển gửi thông điệp.
> - Khung truyền (frame) -> một gói dữ liệu có phần đầu, nội dung và phần kiểm tra.
> - Byte -> đơn vị để đếm độ dài dữ liệu; một khung CAN cổ điển có tối đa 8 byte.
> - ID (mã định danh) -> số cho biết loại thông điệp; không nhất thiết là địa chỉ nhận.
> - ACK (xác nhận nhận) -> bit cho biết có bộ nhận nào nhận đúng khung.
> - Mã kiểm tra CRC (cyclic redundancy check) -> phép kiểm tra phát hiện khung dữ liệu bị sai.
> - Bit trội / bit lặn (dominant / recessive bit) -> hai mức tín hiệu dùng để phân xử khi cùng gửi.
> - Bit-tốc độ (bitrate) -> số bit truyền trong một giây.
> - Kp (proportional gain) -> hệ số tỷ lệ trong lệnh điều khiển động cơ.
> - RobStride -> động cơ dùng CAN với ID mở rộng 29 bit trong dự án.
> - Chế độ chỉ nghe (listen-only) -> nhận dữ liệu mà không gửi ACK hay lệnh lên mạng.

## Vì sao cần biết?
STM32 của robot cần trao đổi lệnh và phản hồi với động cơ qua CAN. Hiểu khung truyền giúp phân biệt lỗi đường dây với lỗi giải mã dữ liệu; chế độ chỉ nghe giúp quan sát mà không tác động mạng động cơ.

## Cách hình dung
Mạng CAN giống một nhóm chat chung: mọi nút đều thấy tin nhắn, còn ID quyết định nút nào tiếp tục gửi khi hai nút bắt đầu cùng lúc. Bit trội thắng bit lặn, nên nút thua dừng gửi mà không làm hỏng tin nhắn thắng.

```text
Node A gửi: trội  lặn    lặn
Node B gửi: trội  trội   ...
Mạng thấy:  trội  trội   ...  B tiếp tục

Bắt đầu | ID và điều khiển | 0..8 byte | CRC | ACK | kết thúc
```

Một khung cổ điển mang tối đa 8 byte. CRC là phép kiểm tra giúp phát hiện khung bị sai; ACK chỉ xác nhận ít nhất một bộ nhận thấy khung hợp lệ, không chứng minh động cơ đã làm theo lệnh.

RobStride dùng ID mở rộng 29 bit; ID chia thành loại giao tiếp, thông tin nguồn và ID động cơ đích. Dữ liệu 8 byte có thể mã hoá vị trí, vận tốc, hệ số điều khiển và phản hồi động cơ.

Một bit-tốc độ CAN (bitrate) phải khớp giữa các nút. Trên nhánh giám sát 42 MHz trong bài đầy đủ, cấu hình bộ chia và các đoạn thời gian tạo ra 1 Mbit/s.

Với dữ liệu đã mã hoá thành số nguyên, đổi ngược về giá trị thật gọi là giải tỷ lệ (scaling). Kp được gửi dưới dạng mã số nguyên 16 bit, không phải số thập phân trực tiếp.

Mạng thường có hai điện trở kết thúc 120 Ω ở hai đầu. Chế độ chỉ nghe của bộ giám sát không ACK, không phát cờ lỗi và không gửi lệnh; vì vậy bộ giám sát không thể thay bộ nhận hoạt động.

## Ví dụ nhỏ
Mã hoá Kp=1000 trong khoảng 0–5000 bằng 16 bit cho ra gần mã 13107 (0x3333). Động cơ khôi phục giá trị gần 1000; sai khác nhỏ xuất hiện vì mã là số nguyên.

## Tự kiểm tra
1. ACK có chứng minh động cơ đã thực hiện lệnh không?
2. RobStride trong bài dùng ID dài bao nhiêu bit?
3. Bộ giám sát chỉ nghe có gửi ACK không?

<details>
<summary>Đáp án</summary>

1. Không; ACK chỉ cho biết có bộ nhận nào chấp nhận khung.
2. 29 bit.
3. Không.

</details>

## Muốn đọc sâu hơn
[Bài đầy đủ: CAN và RobStride](../01_can_and_robstride.md).
