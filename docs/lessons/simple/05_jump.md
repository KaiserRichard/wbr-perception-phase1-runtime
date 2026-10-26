# 05 — Chuỗi nhảy của WBR

> **Từ khoá**
> - Máy trạng thái (state machine) -> cách chương trình chia hành vi thành các bước và điều kiện chuyển bước.
> - Pha (phase) -> một bước trong chuỗi hành vi.
> - Ngồi thấp (crouch) -> pha đầu, khi chân hướng tới chiều dài thấp.
> - Đẩy (thrust) -> pha tạo lực đẩy bằng cách tăng chiều dài chân mục tiêu.
> - Thu chân (retract) -> pha đưa chân về mục tiêu thu lại.
> - Ổn định sau tiếp đất (landed/settle) -> pha kết thúc chuỗi trong mã nguồn.
> - PS2 R1 -> nút được firmware dùng làm yêu cầu nhảy.
> - Giá trị đặt (setpoint) -> mục tiêu mà bộ điều khiển cố đạt.
> - Bộ đếm (counter) -> số lần một điều kiện được ghi nhận.
> - Rào đồng bộ (barrier) -> chờ hai phía cùng đạt điều kiện trước khi chuyển bước.
> - Thông tin gợi ý (advisory) -> dữ liệu tham khảo, không phải lệnh trực tiếp cho động cơ.

## Vì sao cần biết?
Trong WBR, một lần nhấn nút có thể bắt đầu chuỗi thay đổi chiều dài chân và mô-men. Hiểu các pha giúp đọc firmware chính xác và thấy rằng thông tin từ camera chỉ nên là gợi ý cho bộ điều khiển trên STM32.

## Bốn pha
Máy trạng thái giống danh sách việc cần làm: firmware chỉ sang bước kế tiếp khi điều kiện hiện tại đạt. Trong mã nguồn, chuỗi có bốn pha: ngồi thấp (crouch), đẩy (thrust), thu chân (retract), rồi ổn định sau tiếp đất (landed/settle).

```text
Đứng → Ngồi thấp → Đẩy → Thu chân → Ổn định → Đứng
        0.08 m     0.21 m
```

PS2 R1 là nút khởi phát: firmware tăng bộ đếm khi nút được giữ; khi vượt 10 lần xử lý và chưa có lần nhảy đang hoạt động, nó bật trạng thái yêu cầu nhảy và lưu mục tiêu chân hiện thời. Đây là yêu cầu của người vận hành, không tự kiểm tra địa hình hay tình trạng hai bên.

Ở pha ngồi thấp, mục tiêu chiều dài chân là 0.08 m; ở pha đẩy là 0.21 m. Pha sau dùng mục tiêu thu chân. Bộ điều khiển so chiều dài đo được với ngưỡng để quyết định khi nào tăng bộ đếm pha.

Hai phía dùng rào đồng bộ: cần cả hai bộ đếm đạt 10 thì trạng thái chung mới tiến. Đây là đồng bộ bằng biến dùng chung trong chương trình, không đảm bảo hai động cơ đổi lệnh đúng cùng một thời điểm.

Thông tin camera có thể được gửi như advisory (gợi ý): STM32 vẫn giữ quyền quyết định pha và điều khiển động cơ. Bài đầy đủ nói rõ một số điều kiện như khoảng cách an toàn chưa được định nghĩa, nên không tự điền giá trị.

## Ví dụ nhỏ
Nếu nhấn giữ R1 qua hơn 10 lần xử lý trong lúc không có lần nhảy đang chạy, firmware đặt cờ yêu cầu và lưu mục tiêu chân hiện tại. Sau đó chuỗi bắt đầu với mục tiêu 0.08 m ở pha ngồi thấp.

## Tự kiểm tra
1. Mục tiêu chiều dài chân ở pha đẩy là bao nhiêu?
2. Cần điều kiện từ mấy phía để đồng bộ chuyển pha?
3. Camera có trực tiếp đặt lực chân không?

<details>
<summary>Đáp án</summary>

1. 0.21 m.
2. Cả hai phía.
3. Không; dữ liệu chỉ là gợi ý, STM32 giữ điều khiển.

</details>

## Muốn đọc sâu hơn
[Bài đầy đủ: Chuỗi nhảy WBR](../05_wbr_jump_sequence.md).
