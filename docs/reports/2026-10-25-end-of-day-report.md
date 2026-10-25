# Báo cáo cuối ngày — 25/10/2026

## 1. Tóm tắt trong 5 dòng

- Dựng rig bìa với D435 và chạy kiểm tra LED cùng các bài thử vật cản tĩnh, tiếp cận.
- Bài tĩnh phân biệt được mặt bàn trống, sách và hộp; dữ liệu gửi/nhận qua UART không mất gói trong các lần đếm.
- Ghi nhận LED nhấp nháy ở rìa ngưỡng; phát lại dữ liệu với hysteresis làm giảm số lần đổi trạng thái.
- ORB-SLAM3 đi được đoạn thẳng khoảng 2 m; tạo thêm bản đồ 3D dày đặc theo đường đi.
- Hoàn thành thử nghiệm micro-ROS giữa Pi và Nucleo-F446RE; đây là thử nghiệm bàn, chưa tích hợp lên robot.

## 2. Thí nghiệm hôm nay

| Thử nghiệm | Kết quả |
|---|---|
| Rig bìa, D435 cao 29 cm, nghiêng khoảng 13° | Đo được: chiều cao 29 cm; góc nghiêng khoảng 13°. Dựng rig thử nghiệm trên bàn. |
| LED self-test | Đo được: đủ 4 trạng thái và nhấp nháy khi dữ liệu hết hạn; 9.420 phản hồi. |
| Bàn trống | Đo được: NONE 553/553 khung hình; phản hồi 553/553. |
| Sách cao 4,6 cm, cách 1,00 m | Đo được: JUMP 561/563; 2 khung UNCERTAIN trong lúc xác nhận. Ước lượng cao 4,75 cm, cách 0,998 m. |
| Hộp cao 13,1 cm, cách 1,00 m | Đo được: STOP khi hộp còn trên bàn; về NONE sau khi lấy hộp đi. Ước lượng cao 13,4 cm, cách 0,993 m. |
| Tiếp cận hộp từ xa | Phát hiện tại giới hạn 1,3 m; thước đo 1,285–1,31 m, detector 1,27–1,30 m. LED nhấp nháy ở rìa phạm vi. |
| Giảm nhấp nháy | Đo được trên replay 60 giây: với hysteresis khoảng cách 0,10 m và chiều cao 0,01 m, số lần đổi trạng thái giảm 156→2 và 218→25. Chưa phải kết quả LED live. |
| ORB-SLAM3 và bản đồ | Đo được: đoạn tiến 2,009 m; mốc thước 2,00 m; một map, không thấy nhảy pose. Đo được trên bản đồ dày: 225 khung, khoảng 354 nghìn điểm, độ phân giải 1 cm, RMS mặt bàn 5,8 mm. |

## 3. Foxglove — xem file nào để thấy gì

Trong Foxglove, chọn **Open local file** để mở MCAP; sau đó chọn **Import layout** để nạp layout JSON tương ứng. Các bản ghi MCAP phát lại theo thời gian.

| File cần mở | Nội dung | Mở bằng | Phát theo thời gian? |
|---|---|---|---|
| `~/wbr-evidence-archive/lab-day-20261025/foxglove/3-box13.mcap` + `foxglove_demo_layout.json` | Video thật, hộp được phát hiện và cảnh báo; dùng để demo. | Open local file + Import layout | Có |
| `~/wbr-evidence-archive/lab-day-20261025/MAP-2m-r3-foxglove/MAP-2m-r3-foxglove.mcap` + `map_demo_layout.json` | Video hồng ngoại, đường đi ORB-SLAM3 và bản đồ thưa. | Open local file + Import layout | Có |
| `~/wbr-evidence-archive/lab-day-20261025/MAP-2m-r3-dense-growing/map_growing.mcap` + `foxglove_layout.json` | Bản đồ 3D dày đặc lớn dần theo đường đi. | Open local file + Import layout | Có |
| `~/wbr-evidence-archive/mobile-demo-20261024-01/foxglove-demo/*.mcap` | Các bài sách/hộp ngày 24/10 để tham khảo. | Open local file; chọn layout đi kèm nếu cần | Có |

Các file còn lại là dữ liệu thô, không cần mở để xem demo.

## 4. micro-ROS

Theo thông tin từ anh ở lab, STM32 trên robot dự kiến chạy micro-ROS qua USB. Để thử giao diện, hôm nay dựng publisher trên Pi cho topic `/terrain_advisory`, kiểu `Float64MultiArray` gồm 8 trường theo giao diện; tạo firmware micro-ROS cho Nucleo-F446RE làm board thử và chạy micro-ROS Agent trên Pi. Phân công: Codex viết publisher trên Pi, tài liệu topic, node cầu nối và mã firmware micro-ROS cho F446RE; Claude build thư viện micro-ROS, thêm phương án truyền qua UART, nạp firmware, cài agent trên Pi, chạy thử và kiểm tra kết quả.

Kết quả đo được: board nhận và xác nhận đủ 712/712 rồi 739/739 gói phát lại từ bản ghi hộp 13 cm. LED thể hiện đỏ khi STOP, xanh khi NONE và trạng thái hết hạn khi ngừng nhận dữ liệu. Đây là kết quả trên Nucleo thử nghiệm, không phải trên bo mạch robot.

Gặp kết nối USB ST-Link chập chờn; chuyển sang UART và cấp nguồn E5V để chạy ổn định. Khi nạp qua ST-Link không thành công, nạp firmware qua ROM bootloader UART. Chủ firmware robot cần thêm subscriber theo ví dụ `docs/interfaces/terrain_advisory_microros_example.c`; trước khi tích hợp cần xác nhận giao diện và chạy thử trên bo H723.

## 5. Hạn chế và việc chưa làm

- ORB-SLAM3 và detector chưa chạy đồng thời trên luồng camera trực tiếp; chưa đo CPU khi chạy chung.
- IMU chưa được dùng. Bản đồ dày đặc là thử nghiệm ban đầu và còn phụ thuộc chất lượng pose.
- Chưa hoàn tất vòng dài: bản ghi ORB-SLAM3 kết thúc trước khi ghi được lượt quay về.
- Ngưỡng nhảy 3–12 cm là giả định thiết kế, chưa được xác nhận trên robot.
- Chưa thử hệ thống trên robot thật; các kết quả hôm nay là trên rig bàn/board thử.

## 6. Hướng tiếp theo đề xuất

1. Tích hợp subscriber vào firmware H723 và thử trên bàn, tắt motor; trước tiên chỉ nhận/hiển thị dữ liệu.
2. Chạy luồng camera → Pi → H723 và xác nhận dữ liệu live đến đúng nơi.
3. Chạy ORB-SLAM3 cùng detector, đo tải CPU và hành vi khi không xử lý kịp khung hình.
4. Chốt cổng logic cho nhảy: yêu cầu của operator **AND** trạng thái JUMP còn mới, cùng các điều kiện an toàn do STM32 kiểm soát.
5. Sau khi kiểm tra bàn đạt yêu cầu, thử trên robot thật có giá đỡ và quy trình thử được kiểm soát.

