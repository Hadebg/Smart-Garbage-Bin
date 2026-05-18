# ESP32-CAM Code

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

Đây là code dành cho module **ESP32-CAM**, có nhiệm vụ:

- Chụp ảnh vật thể (rác)
- Gửi ảnh đến Python Flask Server
- Nhận kết quả phân loại từ server
- Gửi tín hiệu đến ESP32 chính để điều khiển thùng rác mở đúng ngăn

ESP32-CAM đóng vai trò là **camera và bộ truyền dữ liệu hình ảnh** trong hệ thống Smart Garbage Bin.

---

## Phần cứng sử dụng

- ESP32-CAM AI Thinker
- Camera OV2640
- Push Button (nút chụp ảnh)

---

## Cách thức hoạt động

### 1. Kết nối Wi-Fi
ESP32-CAM kết nối tới Wi-Fi.

**Wi-Fi này phải giống với:**
- Python Flask Server
- ESP32 chính

Sau khi kết nối thành công, ESP32-CAM sẽ:

- khởi tạo camera
- thiết lập thông số camera
- sẵn sàng chụp ảnh

---

### 2. Chụp ảnh
Người dùng nhấn nút được nối với ESP32-CAM.

Khi nút được nhấn:

- nút sẽ bị khóa tạm thời để tránh spam
- camera chụp ảnh
- bật flash LED hỗ trợ ánh sáng

---

### 3. Gửi ảnh đến Flask Server
ESP32-CAM:

- mã hóa ảnh thành Base64
- đóng gói thành JSON
- gửi HTTP POST request đến Python Flask Server

Server sẽ gửi ảnh tới Gemini AI để phân loại.

---

### 4. Nhận kết quả phân loại
Sau khi Flask server xử lý xong, ESP32-CAM nhận kết quả:

- Organic
- Plastic
- Recyclable can
- Recyclable paper

---

### 5. Gửi tín hiệu đến ESP32 chính
Dựa trên kết quả phân loại, ESP32-CAM gửi request tới ESP32 chính:

- bin1 → Organic
- bin2 → Plastic
- bin3 → Recyclable can
- bin4 → Recyclable paper

ESP32 chính sẽ điều khiển servo/motor để mở đúng ngăn rác.

---

### 6. Kết thúc chu trình
Sau khi gửi tín hiệu:

- bộ nhớ ảnh được giải phóng
- flash tắt
- nút chụp được mở khóa

ESP32-CAM sẵn sàng cho lần phân loại tiếp theo.

---

## Cài đặt

### Cấu hình Wi-Fi

Thay đổi:

```cpp
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
```

Wi-Fi phải trùng với mạng của:

- Flask Server
- ESP32 chính

---

## Lắp đặt phần cứng

### Vị trí camera
ESP32-CAM nên được lắp:

- phía trên cửa thả rác
- hướng camera xuống khu vực vật thể rơi vào

Điều này giúp camera chụp được toàn bộ vật thể.

---

### Test camera trước khi lắp chính thức
Khuyến nghị test trước bằng code streaming:

[ESP32-CAM Streaming Test Guide](https://randomnerdtutorials.com/esp32-cam-video-streaming-face-recognition-arduino-ide/)

Mục đích:

- kiểm tra góc camera
- kiểm tra khoảng cách
- đảm bảo ảnh không quá gần hoặc quá xa

Nên điều chỉnh sao cho:

- vật thể luôn nằm trong khung hình
- hình ảnh rõ nét
- camera cố định chắc chắn

---

## Cấu hình code

### 1. Địa chỉ Flask Server

Thay đổi:

```cpp
const char* serverHost = "YOUR_FLASK_SERVER_IP";
```

Ví dụ:

```cpp
const char* serverHost = "192.168.1.10";
```

Đây là IP của máy chạy Python Flask Server.

Xem cách lấy IP của Python Flask Server [tại đây](https://github.com/Hadebg/Smart-Garbage-Bin/blob/MAIN-PYTHON-FLASK-SERVER-CODE/README.md#ch%E1%BA%A1y-server)

---

### 2. Địa chỉ ESP32 chính

Thay đổi:

```cpp
const char* serverHost2 = "YOUR_MAIN_ESP32_IP";
```

Đây là IP của ESP32 chính dùng để điều khiển thùng rác.

Xem cách lấy IP của ESP32 chính [tại đây](https://github.com/Hadebg/Smart-Garbage-Bin/blob/MAIN-ESP32-CODE/README.md#c%E1%BA%A5u-h%C3%ACnh-code)

---

### 3. Nút chụp ảnh

Cấu hình:

```cpp
const int BUTTON_PIN = 13;
```

Có thể thay đổi tùy chân nối nút.

---

### 4. Pin camera
Code mặc định sử dụng pin mapping cho:

- ESP32-CAM AI Thinker

Nếu dùng module khác, cần chỉnh lại các chân:

```cpp
#define PWDN_GPIO_NUM
...
#define PCLK_GPIO_NUM
```

(từ dòng 35 đến dòng 52)

Có thể tra cứu pin mapping theo board đang sử dụng.

---

## Lưu ý quan trọng

### Camera settings mặc định
Code hiện sử dụng:

```cpp
config.frame_size = FRAMESIZE_XGA;
config.jpeg_quality = 7;
```

Đây là cấu hình đã được kiểm thử ổn định:

- chất lượng ảnh tốt
- không gây tràn bộ nhớ
- hạn chế crash ESP32-CAM

---

### Khi thay đổi chất lượng ảnh
Có thể chỉnh:

- resolution
- jpeg quality

Tuy nhiên cần chú ý:

- bộ nhớ ESP32-CAM khá hạn chế
- ảnh quá lớn có thể gây lỗi capture hoặc reset board

---

### Khuyến nghị
Nên giữ nguyên cấu hình mặc định nếu không thực sự cần thay đổi.

---
