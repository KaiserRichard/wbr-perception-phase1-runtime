# 04 — Giữ thăng bằng: LQR và VMC

> **Từ khoá**
> - WBR -> robot hai bánh có chân liên kết.
> - Bộ điều chỉnh LQR (Linear Quadratic Regulator) -> bộ điều khiển phản hồi tuyến tính tối ưu; trong dự án, các hệ số phản hồi được tính theo mô hình.
> - Trạng thái (state) -> các đại lượng mô tả robot hiện tại, như góc và vận tốc.
> - Hệ số phản hồi (gain) -> số nhân mức sai lệch để tạo lệnh điều khiển.
> - Lập lịch hệ số (gain scheduling) -> chọn bộ hệ số theo chiều dài chân.
> - VMC (Virtual Model Control) -> đổi lực mong muốn tại chân thành mô-men động cơ.
> - Mô-men (torque) -> tác dụng xoay do động cơ tạo ra.

## Vì sao cần biết?
WBR phải giữ thân đứng trên hai bánh dù thân và chân thay đổi tư thế. LQR tính phản ứng từ trạng thái robot, còn VMC biến lực chân cần thiết thành mô-men mà động cơ có thể nhận.

## Từ trạng thái đến động cơ
Hãy hình dung LQR như bộ tự chọn độ mạnh phản ứng: nó xem góc và tốc độ hiện tại rồi kết hợp chúng bằng các hệ số phản hồi. Trong firmware, trạng thái có các đại lượng như góc thân, tốc độ góc, vị trí và tốc độ bánh.

```text
góc, tốc độ, vị trí → LQR → lực/mô-men ảo → VMC → mô-men động cơ
                                      chân liên kết
```

Robot không dùng một bộ hệ số duy nhất cho mọi tư thế: bài đầy đủ mô tả chọn hệ số theo chiều dài chân. Việc chọn này gọi là lập lịch hệ số.

VMC xem chân như cơ cấu liên kết. Nó nhận lực mong muốn theo các hướng tại bàn chân, rồi tính các mô-men khớp tương ứng; sau đó firmware gửi lệnh mô-men tới động cơ. Khi hình học chân ở vị trí bất lợi, cùng một lực mong muốn có thể đòi mô-men lớn hơn.

Vòng điều khiển (control loop) lặp việc đo trạng thái, tính lệnh và gửi lệnh. Thời gian giữa hai lần lặp ảnh hưởng đến việc lệnh có kịp với chuyển động hay không; số đo tần số trong bài là tốc độ các vòng lặp được cấu hình, không phải bằng chứng tự thân về hiệu năng thực tế.

## Ví dụ nhỏ
Mã nguồn giới hạn lệnh mô-men bánh từ −2 đến +2. Nếu phép tính yêu cầu +3, giới hạn khiến lệnh gửi đi không vượt quá +2.

## Tự kiểm tra
1. LQR đọc loại thông tin nào?
2. VMC đổi lực chân mong muốn thành gì?
3. Vì sao hệ số có thể đổi theo chiều dài chân?

<details>
<summary>Đáp án</summary>

1. Trạng thái hiện tại của robot.
2. Mô-men tại các khớp/động cơ.
3. Chân dài hay ngắn làm trọng tâm cao hay thấp, nên robot "đổ" nhanh chậm khác nhau; mỗi chiều dài chân cần một bộ hệ số riêng.

</details>

## Muốn đọc sâu hơn
[Bài đầy đủ: Giữ thăng bằng WBR, LQR và VMC](../04_wbr_balance_lqr_vmc.md).
