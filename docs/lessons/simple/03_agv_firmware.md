# 03 — Firmware đế AGV

> **Từ khoá**
> - AGV -> tên robot di động được điều khiển trong bài đầy đủ.
> - Động học ngược (inverse kinematics) -> đổi tốc độ tiến/quay thành tốc độ bánh.
> - Bánh chủ động vi sai (differential drive) -> hai bánh có thể quay tốc độ khác nhau để robot rẽ.
> - Bão hoà (saturation) -> giới hạn lệnh để không vượt tốc độ cho phép.
> - Tác vụ tuần hoàn (periodic task) -> phần chương trình lặp theo chu kỳ thời gian.
> - Watchdog -> bộ đếm phát hiện một việc không được cập nhật đúng hạn.
> - Dừng khẩn cấp (emergency stop) -> yêu cầu đưa hệ thống vào trạng thái dừng.

## Vì sao cần biết?
Đế AGV biến lệnh vận tốc thành lệnh cho bánh xe, nên sai ở phép đổi này làm robot chạy lệch hướng. Watchdog và dừng khẩn cấp giúp firmware nhận ra khi lệnh điều khiển không còn đáng tin.

## Hai bánh và lệnh chuyển động
Hai bánh chủ động giống hai chân chèo: chạy bằng nhau thì robot đi thẳng; chạy lệch nhau thì robot quay. Động học ngược là phép đổi từ tốc độ tiến và tốc độ quay của thân robot sang tốc độ từng bánh.

$$
\omega_L=(v-\Omega b/2)/R,\quad \omega_R=(v+\Omega b/2)/R
$$

Trong đó `v` là tốc độ tiến (m/s), `Ω` là tốc độ quay (rad/s), `b` là khoảng cách hai bánh (m), `R` là bán kính bánh (m), còn `ωL`, `ωR` là tốc độ bánh (rad/s).

```text
          tiến v →
   bánh trái       bánh phải
     ωL   [ AGV ]    ωR
             ↻ Ω
```

Nếu tốc độ yêu cầu vượt giới hạn, firmware dùng bão hoà để giảm lệnh. Khi muốn giữ hướng rẽ, giảm cả hai tốc độ theo cùng tỉ lệ thay vì cắt một bánh riêng biệt.

Tác vụ tuần hoàn đọc lệnh, tính tốc độ bánh rồi cập nhật động cơ theo nhịp lặp. Watchdog kiểm tra xem lệnh mới có đến kịp không; mất cập nhật quá 500 ms thì AGV báo timeout.

## Ví dụ nhỏ
Robot có bán kính bánh `R=0.06 m` và được yêu cầu đi thẳng `v=0.3 m/s`, không quay (`Ω=0`). Mỗi bánh cần `0.3/0.06=5 rad/s`.

## Tự kiểm tra
1. Hai bánh quay bằng nhau tạo chuyển động nào?
2. Bão hoà dùng để làm gì?
3. Watchdog AGV báo timeout sau bao lâu không cập nhật?

<details>
<summary>Đáp án</summary>

1. Đi thẳng.
2. Giữ lệnh trong giới hạn.
3. 500 ms.

</details>

## Muốn đọc sâu hơn
[Bài đầy đủ: Firmware đế AGV](../03_agv_base_firmware.md).
