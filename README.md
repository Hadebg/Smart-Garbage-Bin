# Smart Garbage Bin using ESP32, ESP32-CAM and AI Classification

### Note (to English users): Almost all files and instructions are written in Vietnamese. We kindly ask for your understanding and suggest using translation software for your convenience.

## Mục lục
- [Giới thiệu](#giới-thiệu)

- [Cấu trúc hệ thống](#cấu-trúc-hệ-thống)

- [Cấu trúc repository](#cấu-trúc-repository)

- [Phần cứng sử dụng](#phần-cứng-sử-dụng)

- [Cách thức hoạt động](#cách-thức-hoạt-động)

- [Các thành phần chính](#các-thành-phần-chính)

- [Hướng dẫn chi tiết](#hướng-dẫn-chi-tiết)

- [Lưu ý quan trọng](#lưu-ý-quan-trọng)

---

## Giới thiệu

Đây là dự án **Nghiên cứu khoa học 2025 cấp cụm Long Biên - Gia Lâm** với đề tài: **Thiết bị phân loại rác thải tại trường học ứng dụng trí tuệ nhân tạo trong nhận dạng hình ảnh**.

Dự án được thực hiện bởi **2 học sinh trường THPT Nguyễn Gia Thiều** và đạt **giải Ba** trong cuộc thi lần này.

Hệ thống bao gồm:

- **ESP32-CAM** dùng để chụp ảnh rác
- **Python Flask Server** xử lý AI classification
- **ESP32 Main Controller** điều khiển động cơ, encoder và servo

Các chức năng chính:

- Chụp ảnh rác
- Phân loại rác bằng AI
- Xoay thùng rác đến đúng vị trí
- Mở / đóng cửa xả rác tự động
- Dashboard thống kê realtime
- Telegram bot tra cứu xếp hạng

Tài liệu tham khảo:

- [Infographic](https://github.com/Hadebg/Smart-Garbage-Bin/tree/a091debcf8df6acf01d826d737942f995bafb458/Infographic)

- [Bản báo cáo 11 trang NCKH](https://github.com/Hadebg/Smart-Garbage-Bin/blob/a091debcf8df6acf01d826d737942f995bafb458/B%C3%A1o%20c%C3%A1o%2011%20trang%20NCKH%20.docx)

- [Sơ đồ thuật toán](https://github.com/Hadebg/Smart-Garbage-Bin/blob/a091debcf8df6acf01d826d737942f995bafb458/Vi%20%C4%91i%E1%BB%81u%20khi%E1%BB%83n%20ESP32.png)

- [Hình ảnh thực tế các website và application](https://github.com/Hadebg/Smart-Garbage-Bin/tree/a091debcf8df6acf01d826d737942f995bafb458/Website%20Sample)

---

## Cấu trúc hệ thống

```text
ESP32-CAM
   ↓
Capture Image
   ↓
Python Flask Server
   ↓
Gemini AI / Custom AI Model
   ↓
Classification Result
   ↓
ESP32 Main Controller
   ↓
Motor + Encoder + Servo
   ↓
Correct Trash Bin
```

Ngoài ra:

```text
Flask Server
   ├── SQLite Database
   ├── Dashboard Realtime
   └── Telegram Bot
```

---

## Cấu trúc repository

Repository được chia thành nhiều branch riêng biệt:

```text
main
├── Tổng quan project

MAIN-ESP32-CODE
├── ESP32 Main Controller code

ESP32-CAM-CODE
├── ESP32-CAM code

MAIN-PYTHON-FLASK-SERVER-CODE
├── Python Flask Server code
```

---

## Phần cứng sử dụng

### ESP32 Main
- ESP32
- 1 DC motor encoder
- 2 Servo MG996
- 1 Proximity Sensor
- H-Bridge driver

### ESP32-CAM
- ESP32-CAM AI Thinker
- OV2640 Camera
- Push Button

### Server
- Laptop / PC / mini PC chạy Python Flask

---

## Cách thức hoạt động

### 1. Capture
Người dùng nhấn nút trên ESP32-CAM để chụp ảnh rác.

---

### 2. Classification
ESP32-CAM gửi ảnh đến Flask server.

Flask server:
- nhận ảnh
- gửi tới Gemini AI hoặc custom AI model
- nhận kết quả phân loại

Ví dụ:
- Organic
- Plastic
- Recyclable can
- Recyclable paper

---

### 3. Control
ESP32-CAM gửi request đến ESP32 Main Controller.

ESP32 Main:
- xoay thùng bằng encoder
- căn vị trí bằng cảm biến tiệm cận
- mở cửa xả rác bằng servo
- đóng lại

---

### 4. Statistics
Flask server lưu dữ liệu:

- số lượng rác
- loại rác
- thiết bị

vào SQLite database.

Dashboard và Telegram bot sử dụng dữ liệu này để hiển thị thống kê realtime.

---

## Các thành phần chính

### ESP32 Main Controller
Chịu trách nhiệm:
- điều khiển motor
- encoder positioning
- servo dumping
- manual webserver control

Branch:

```text
MAIN-ESP32-CODE
```

---

### ESP32-CAM
Chịu trách nhiệm:
- camera capture
- gửi ảnh tới server
- nhận classification result
- gửi tín hiệu điều khiển

Branch:

```text
ESP32-CAM-CODE
```

---

### Python Flask Server
Chịu trách nhiệm:
- AI classification
- database
- dashboard
- Telegram bot

Branch:

```text
MAIN-PYTHON-FLASK-SERVER-CODE
```

---

## Hướng dẫn chi tiết

Xem hướng dẫn cài đặt và cấu hình chi tiết tại:

- [ESP32 Main Controller](https://github.com/Hadebg/Smart-Garbage-Bin/blob/e256c4547b7debbceed379ceea7fa40a59c9900f/README.md)

- [ESP32-CAM](https://github.com/Hadebg/Smart-Garbage-Bin/blob/51f6d4306187767a3f7efdde39b7d75cbdfce307/README.md)

- [Python Flask Server](https://github.com/Hadebg/Smart-Garbage-Bin/blob/236798e9ce98298952b7e73ba94b1e58c9a8fae3/README.md)

---

## Lưu ý quan trọng

- Tất cả thiết bị phải cùng mạng Wi-Fi:
  - ESP32-CAM
  - ESP32 Main
  - Flask Server

- Wi-Fi nên bật trước khi cấp nguồn cho ESP32

- Khuyến nghị dùng nguồn riêng cho:
  - Servo
  - Motor

để tránh sụt áp làm reset ESP32.

- Đây là bản sử dụng Gemini AI để phân tích hình ảnh và ESP32-CAM cần phải sử dụng nút để chụp ảnh, có thể tối ưu bằng việc train AI riêng để tự động phân loại ngay khi thả rác
