# ESP32 Main Controller

## Mục lục
- [Giới thiệu](#giới-thiệu)

- [Phần cứng sử dụng](#phần-cứng-sử-dụng)

- [Cách thức hoạt động](#cách-thức-hoạt-động)

- [Cài đặt](#cài-đặt)

- [Lắp đặt phần cứng](#lắp-đặt-phần-cứng)

- [Cấu hình code](#cấu-hình-code)

- [Lưu ý quan trọng](#lưu-ý-quan-trọng)

---

## Giới thiệu
Đây là chương trình điều khiển chính cho hệ thống thùng rác thông minh sử dụng ESP32.

ESP32 chịu trách nhiệm:
- Nhận tín hiệu kết quả phân loại rác từ ESP32-CAM hoặc hệ thống AI khác
- Điều khiển động cơ DC có encoder để xoay thùng rác đến đúng vị trí
- Điều khiển servo mở và đóng cửa xả rác
- Cung cấp webserver nội bộ để điều khiển thủ công

Webserver cho phép người dùng:
- Điều khiển quay trái / phải
- Dừng động cơ
- Mở / đóng cửa xả rác
- Chuyển thùng đến từng vị trí cụ thể
- Reset về vị trí gốc (Home)

---

## Phần cứng sử dụng
- ESP32
- 1 động cơ DC có encoder  
  - Encoder: khoảng `23550 xung / vòng` sau toàn bộ hệ giảm tốc
- 2 Servo MG996
- 1 cảm biến tiệm cận dùng làm mốc Home
- Mạch cầu H điều khiển động cơ
- Nguồn cấp phù hợp cho:
  - ESP32
  - Servo
  - Động cơ
  - Cảm biến

---

## Cách thức hoạt động
1. ESP32 nhận kết quả phân loại từ ESP32-CAM hoặc AI model
2. Xác định vị trí thùng cần xoay tới
3. Điều khiển động cơ DC quay đến vị trí đích bằng encoder
4. Khi gần tới vị trí:
   - Giảm tốc để tăng độ chính xác
5. Khi tới đúng vị trí:
   - Mở cửa xả rác trong vài giây
   - Đóng cửa lại
6. Có thể reset về vị trí Home bằng cảm biến tiệm cận

---

## Cài đặt
1. Cài Arduino IDE hoặc PlatformIO
(khuyến khích sử dụng PlatformIO)

2. Cài board ESP32:
- ESP32 by Espressif Systems

3. Cài thư viện cần thiết:
- WiFi
- WebServer
- LittleFS

4. Upload code vào ESP32

5. Upload file webserver [data/index.html](https://github.com/Hadebg/Smart-Garbage-Bin/blob/be059cc2ac6cf4b61570932ecdd7f2a1b11d6a7c/data/index.html): Tham khảo các bước làm tại các website sau:
- Đối với PlatformIO: [PlatformIO_SPIFFS](https://randomnerdtutorials.com/esp32-vs-code-platformio-spiffs/)
- Đối với ArduinoIDE: [ArduinoIDE_SPIFFS](https://randomnerdtutorials.com/install-esp32-filesystem-uploader-arduino-ide/)

---

## Lắp đặt phần cứng
- Đặt ESP32 bên trong thùng rác (khuyến nghị ở đáy)
- Gắn động cơ DC vào cơ cấu xoay thùng
- Gắn encoder vào trục động cơ
- Gắn 2 servo vào cửa xả rác
- Gắn cảm biến tiệm cận tại vị trí Thùng 1 (Home)

Khuyến nghị:
- Dùng nguồn riêng cho servo và động cơ để tránh sụt áp reset ESP32

Các chân kết nối được định nghĩa trực tiếp trong code.

---

## Cấu hình code
Chỉnh sửa Wi-Fi trong code:

```cpp
#define STA_SSID  "Your_Wifi_Name"
#define STA_PASS  "Your_Wifi_Password"
```

ESP32 sau khi kết nối thành công sẽ tự đặt IP:

```txt
x.y.z.100
```

Ví dụ:

```txt
172.28.63.100
```

- Kiểm tra Serial Monitor để biết IP

Truy cập webserver tại:

```txt
http://x.y.z.100
```

Ví dụ:

```txt
http://172.28.63.100
```

### API điều khiển
- `/bin1`
- `/bin2`
- `/bin3`
- `/bin4`

- `/reset`

- `/servo/open`
- `/servo/close`

- `/motor/left`
- `/motor/right`
- `/motor/stop`

- `/state`

---

## Lưu ý quan trọng
- Wi-Fi phải được bật **trước khi cấp nguồn cho ESP32**

Nếu không:
- ESP32 không kết nối được Wi-Fi STA
- Tự động chuyển sang chế độ AP mode

Khi đó:
- ESP32-CAM hoặc hệ AI khác có thể không gửi được tín hiệu điều khiển

---

### Nếu dùng AI model riêng thay cho ESP32-CAM
Có thể sử dụng:
- Camera kết nối với máy tính nhúng / mini PC

Yêu cầu:
- Máy tính có khả năng xử lý hình ảnh ổn định
- Kết nối cùng Wi-Fi với ESP32

Sau khi chạy AI:
- Gửi request HTTP đến đúng IP ESP32

Ví dụ:

```txt
http://172.28.63.100/bin2
```

Miễn hệ thống AI gửi đúng request HTTP đến ESP32 thì đều có thể tích hợp.

---

### Chú ý cần thực hiện bước số 5 trong phần cài đặt, tránh trường hợp báo lỗi chưa 'uploadfs'

---
