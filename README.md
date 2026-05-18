# Python Flask Server (Main Server)

## Mục lục
- [Giới thiệu](#giới-thiệu)

- [Cách thức hoạt động](#cách-thức-hoạt-động)

- [Cài đặt](#cài-đặt)

- [Chạy server](#chạy-server)

- [Sử dụng Dashboard](#sử-dụng-dashboard)

- [Telegram Bot](#telegram-bot)

- [Reset Database](#reset-database)

- [Lưu ý quan trọng](#lưu-ý-quan-trọng)

---

## Giới thiệu

Đây là code Python Flask server chính cho dự án **Smart Garbage Bin**.

Server có nhiệm vụ:

- Nhận ảnh từ ESP32-CAM
- Gửi ảnh tới Gemini AI để phân loại rác
- Nhận kết quả từ Gemini và trả về cho ESP32-CAM
- Lưu dữ liệu thống kê vào database SQLite
- Hiển thị dashboard theo thời gian thực
- Hỗ trợ Telegram Bot để tra cứu bảng xếp hạng và thống kê

---

## Cách thức hoạt động

### 1. Nhận ảnh từ ESP32-CAM
ESP32-CAM chụp ảnh vật thể và gửi ảnh đến Flask server.

### 2. Phân loại bằng Gemini AI
Server gửi ảnh đến Gemini AI với prompt được thiết lập sẵn.

Gemini sẽ phân loại rác thành:

- Recycle
- Non-recycle
- Organic

### 3. Trả kết quả và lưu dữ liệu
Sau khi xử lý:

- Kết quả được gửi về ESP32-CAM
- Dữ liệu được lưu vào SQLite database

Mỗi thiết bị được nhận diện riêng bằng **địa chỉ MAC**.

### 4. Dashboard realtime
Website dashboard sẽ tự động cập nhật dữ liệu liên tục.

**Không cần refresh hoặc nhấn F5 thủ công.**

### 5. Telegram Bot
Người dùng có thể tra cứu thiết bị bằng Telegram.

Lệnh sử dụng:

```bash
/ranking <tên_thiết_bị>
```

Ví dụ:

```bash
/ranking 12A4
```

Bot sẽ trả về:

- Xếp hạng
- Tổng số rác đã phân loại
- Số lượng từng loại rác

---

## Cài đặt

### Yêu cầu

- Máy tính hoặc server chạy Python
- Cùng mạng Wi-Fi với các thiết bị ESP32

---

### Cấu hình API Key

Thay đổi các biến sau trong file Python:

```python
GEMINI_API_KEY = "YOUR_API_KEY"
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_PASSWORD = "1234"
```

Trong đó:

- **GEMINI_API_KEY**: lấy tại  
[Google AI Studio](https://aistudio.google.com/welcome)

- **BOT_TOKEN**: tham khảo cách lấy tại  
[Telegram Bot Token Guide](https://help.superchat.com/en/articles/14901-how-do-i-get-the-telegram-token-or-bot-id)

Có thể thay đổi:

```python
ADMIN_PASSWORD
```

để đặt mật khẩu riêng.

---

## Chạy server

Di chuyển terminal đến thư mục chứa project:

```bash
cd your_folder
```

Chạy:

```bash
python app.py
```

Sau khi chạy thành công, Flask sẽ hiển thị địa chỉ IP, ví dụ:

```bash
http://192.168.1.10:5000
```

Sử dụng địa chỉ IP này để:

- Truy cập dashboard
- Gán vào code ESP32-CAM

---

## Sử dụng Dashboard

### Thiết lập lần đầu

1. Thực hiện phân loại rác lần đầu để hệ thống ghi nhận địa chỉ MAC
2. Mở website dashboard
3. Vào tab **Settings**
4. Nhập mật khẩu admin
5. Đổi tên thiết bị theo địa chỉ MAC tương ứng

---

### Bảo mật Settings

Tab Settings có cơ chế bảo mật:

- Chỉ cho phép chỉnh sửa trong tối đa **3 phút**
- Hết 3 phút sẽ tự khóa
- Chuyển tab hoặc rời khỏi trang sẽ tự khóa
- Nhập sai mật khẩu quá 3 lần sẽ bị khóa tạm thời

---

## Telegram Bot

Telegram bot có thể sử dụng ở bất cứ đâu.

**Không cần cùng Wi-Fi với server.**

Cú pháp:

```bash
/ranking <tên_thiết_bị>
```

Ví dụ:

```bash
/ranking Class12A
```

Bot trả về:

- Xếp hạng
- Tổng số rác
- Recycle count
- Non-recycle count
- Organic count

---

## Reset Database

Project có file:

```bash
reset.py
```

Chức năng:

- Xóa toàn bộ dữ liệu trong `waste_data.db`

Chỉ sử dụng khi muốn reset hoàn toàn:

- Bảng xếp hạng
- Thống kê
- Lịch sử phân loại rác

Cách sử dụng:
- Di chuyển terminal đến thư mục chứa project:

```bash
cd your_folder
```

- Chạy:

```bash
python reset.py
```

---

## Lưu ý quan trọng

- Flask server và ESP32 phải cùng mạng Wi-Fi
- Telegram bot có thể dùng ở mọi nơi
- Nên đổi mật khẩu mặc định trước khi sử dụng
- Cần chạy thiết bị ít nhất 1 lần trước khi đổi tên trong dashboard
- Yêu cầu máy phải có Python, cài Python [tại đây](https://www.python.org/downloads/).
- Trong trường hợp chương trình Python báo lỗi thiếu thư viện, hãy cài các thư viện cần thiết bằng lệnh sau trong terminal:

```bash
pip install flask google-genai requests
```

---
