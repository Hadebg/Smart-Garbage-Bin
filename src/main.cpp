
// DỰ ÁN PHÂN LOẠI RÁC SỬ DỤNG ESP32-CAM VÀ GEMINI API (QUA FLASK SERVER)

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// ==========================================================
// THÔNG TIN CẦN CẬP NHẬT
// ==========================================================
// 1. Cấu hình Wi-Fi
const char* ssid = "YOUR_WIFI"; // ĐÃ CẬP NHẬT
const char* password = "YOUR_PASSWORD"; // ĐÃ CẬP NHẬT

// 2. Cấu hình Server Flask (Địa chỉ IP của máy tính chạy Flask)
// VÍ DỤ: "192.168.1.10" (Phải thay thế bằng IP thực tế của máy tính bạn)
const char* serverHost = "YOUR_FLASK_SERVER_IP"; // ĐÃ CẬP NHẬT
const int serverPort = 5000;
const char* serverPath = "/analyze-image";

const char* serverHost2 = "YOUR_MAIN_ESP32_IP"; // ĐÃ CẬP NHẬT
const char* bin1 = "/bin1";
const char* bin2 = "/bin2";
const char* bin3 = "/bin3";
const char* bin4 = "/bin4";

// 3. Cấu hình Chân Nút Nhấn (Button)
// GPIO 13 thường là chân phù hợp trên board AI Thinker để kết nối nút nhấn.
const int BUTTON_PIN = 13; 
bool isProcessing = false;

// ==========================================================

// Cấu hình Pin Camera Tùy Chỉnh (THAY THẾ camera_pins.h)
#define PWDN_GPIO_NUM  32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM  0
#define SIOD_GPIO_NUM  26
#define SIOC_GPIO_NUM  27

#define Y9_GPIO_NUM    35
#define Y8_GPIO_NUM    34
#define Y7_GPIO_NUM    39
#define Y6_GPIO_NUM    36
#define Y5_GPIO_NUM    21
#define Y4_GPIO_NUM    19
#define Y3_GPIO_NUM    18
#define Y2_GPIO_NUM    5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM  23
#define PCLK_GPIO_NUM  22
#define FLASH_LED_GPIO 4
// END PIN DEFINITIONS

// Biến trạng thái nút nhấn và chống rung (debounce)
bool isButtonPressed = false;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50; // 50ms

// Bảng tra cứu Base64 (Standard RFC 4648)
const char base64_chars[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

// Hàm Base64 Encode Tùy chỉnh (Tích hợp - Đã tối ưu hóa bộ nhớ)
// Sử dụng cấp phát bộ đệm một lần (malloc) để tránh phân mảnh heap.
String base64_encode(const uint8_t* data, size_t input_length) {
    // 1. Tính toán kích thước Base64 (lớn hơn khoảng 33%)
    size_t output_length = 4 * ((input_length + 2) / 3);
    
    // 2. Cấp phát bộ nhớ cho Base64 string (+1 cho null terminator)
    char* encoded_buf = (char*) malloc(output_length + 1);
    if (encoded_buf == NULL) {
        Serial.println("Base64 Cấp phát bộ nhớ thất bại!");
        return ""; 
    }

    int i = 0;
    int j = 0;
    uint8_t char_array_3[3];
    uint8_t char_array_4[4];
    size_t k = 0; // Index cho buffer đầu ra

    const uint8_t* ptr = data;
    
    // Vòng lặp chính
    while (input_length--) {
        char_array_3[i++] = *(ptr++);
        if (i == 3) {
            char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
            char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
            char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
            char_array_4[3] = char_array_3[2] & 0x3f;

            for (i = 0; (i < 4); i++)
                encoded_buf[k++] = base64_chars[char_array_4[i]];
            i = 0;
        }
    }

    // Xử lý phần còn lại (padding)
    if (i) {
        for (j = i; j < 3; j++)
            char_array_3[j] = '\0';

        char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
        char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
        char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
        char_array_4[3] = char_array_3[2] & 0x3f;

        for (j = 0; (j < i + 1); j++)
            encoded_buf[k++] = base64_chars[char_array_4[j]];

        while ((i++ < 3))
            encoded_buf[k++] = '=';
    }
    
    // 3. Kết thúc chuỗi (Null terminator)
    encoded_buf[output_length] = '\0';

    // 4. Tạo String từ buffer và giải phóng bộ nhớ đã cấp phát
    String encoded_string(encoded_buf);
    free(encoded_buf);

    return encoded_string;
}
void sendToServer(const String& binType) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = "http://" + String(serverHost2) + "/" + binType;
    Serial.println("Đang gửi: " + url);

    http.begin(url);
    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      Serial.printf("Phản hồi [%d]: %s\n", httpResponseCode, http.getString().c_str());
    } else {
      Serial.printf("Lỗi khi gửi: %d\n", httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi chưa kết nối!");
  }
}
// Cấu hình Camera
void initCamera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    
    // Sử dụng tên biến mới để tránh cảnh báo (deprecation warnings)
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    
    // Kích thước VGA (640x480) để cân bằng chất lượng và tài nguyên bộ nhớ
    config.frame_size = FRAMESIZE_XGA; 
    config.jpeg_quality = 7; 
    config.grab_mode = CAMERA_GRAB_LATEST;
    // Frame buffer được cấp phát trong PSRAM
    config.fb_count = 2;
    
    // Camera Init
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Khởi tạo Camera thất bại với lỗi 0x%x", err);
        return;
    }
    sensor_t *s = esp_camera_sensor_get();

    if (s) {
        // 1. Cấu hình VFLIP (Lật ảnh theo chiều dọc)
        // Giá trị: 1 (true) để bật, 0 (false) để tắt
        s->set_vflip(s, 1);
        Serial.println("Cấu hình VFLIP thành TRUE (Lật dọc) thành công.");

        // Tùy chọn: Bạn có thể bật HFLIP (Lật ảnh theo chiều ngang) nếu cần
        // s->set_hmirror(s, 1);
        // Serial.println("Cấu hình HMIRROR thành TRUE (Lật ngang) thành công.");
    } else {
        Serial.println("Không thể lấy đối tượng sensor.");
}
}

// Kết nối Wi-Fi
void connectWiFi() {
    Serial.print("Đang kết nối WiFi...");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    Serial.println("Kết nối WiFi thành công.");
    Serial.print("Địa chỉ IP ESP32: ");
    Serial.println(WiFi.localIP());
    Serial.print("Địa chỉ IP Server Flask: ");
    Serial.println(serverHost);
    Serial.println("Sẵn sàng chụp ảnh!");
    pinMode(FLASH_LED_GPIO, OUTPUT);
}
String base64_image = "";
String json_payload = "";
// Chụp ảnh, encode và gửi đến server Flask
void captureAndSend() {
    if (isProcessing) return;
    isProcessing = true; // khóa nút
    Serial.println("--- Nút được nhấn! Bắt đầu chụp ảnh...");
    Serial.println("Chờ camera ổn định...");
    for (int i = 0; i < 2; i++) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
        // Khung hình đã được lấy thành công, ta giải phóng nó ngay lập tức
        esp_camera_fb_return(fb);
        Serial.printf("Khung hình dummy %d đã được chụp và loại bỏ.\n", i + 1);
    }
    // Đợi một chút (tùy chọn)
    vTaskDelay(50 / portTICK_PERIOD_MS); 
}
Serial.println("Camera đã sẵn sàng.");
    // Lấy frame buffer (được cấp phát trong PSRAM)
    analogWrite(FLASH_LED_GPIO, 120);
    delay(500);
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("Chụp ảnh thất bại (Không đủ bộ nhớ hoặc lỗi phần cứng)!");
        return;
    }

    Serial.printf("Ảnh chụp thành công! Kích thước: %u bytes.\n", fb->len);

    // 1. Base64 Encode
    base64_image = "";
    base64_image = base64_encode(fb->buf, fb->len);
    
    // Kểm tra lỗi bộ nhớ trong Base64 Encode
    if (base64_image.length() == 0 && fb->len > 0) {
        Serial.println("Base64 Encoding THẤT BẠI (Lỗi cấp phát bộ nhớ)!");
        // Giải phóng Frame Buffer trước khi thoát
        esp_camera_fb_return(fb); 
        return;
    }

    // 2. Xây dựng JSON Payload
    String macAddress = WiFi.macAddress();  // Lấy MAC
    json_payload = "";
    json_payload = "{\"mac_address\": \"" + macAddress + "\", \"image_data\": \"";
    json_payload += base64_image;
    json_payload += "\"}";
    
    // 3. Gửi POST Request
    HTTPClient http;
    String serverUrl = "http://" + String(serverHost) + ":" + String(serverPort) + String(serverPath);
    
    Serial.println("Đang gửi request đến server: " + serverUrl);
    
    http.begin(serverUrl);
    // THÊM: Tăng thời gian chờ (timeout) lên 15 giây để đọc toàn bộ phản hồi từ server
    http.setTimeout(20000); 
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(json_payload);

    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.printf("Mã phản hồi HTTP: %d\n", httpResponseCode);
        Serial.println("--- KẾT QUẢ PHÂN TÍCH TỪ GEMINI ---");
        Serial.println(response);
        Serial.println("-------------------------------------");
        if (response == "Organic") {
            sendToServer("bin1");
        } else if (response == "Plastic") {
            sendToServer("bin2");
        } else if (response == "Recyclable can") {
            sendToServer("bin3");
        } else if (response == "Recyclable paper"){
            sendToServer("bin4");
        }
    } else {
        Serial.printf("Gửi thất bại! Mã lỗi HTTP: %d\n", httpResponseCode);
        Serial.printf("Lỗi: %s\n", http.errorToString(httpResponseCode).c_str());
    }

    http.end();
    
    // 4. Giải phóng bộ đệm ảnh (TRẢ LẠI cho camera driver để sử dụng lại)
    esp_camera_fb_return(fb);
    Serial.println("--- Đã giải phóng bộ nhớ. Đang chờ nút nhấn mới.");
    json_payload = "";
    base64_image = "";
    analogWrite(FLASH_LED_GPIO, 0);
    isProcessing = false; 
}


void setup() {
    Serial.begin(115200);
    Serial.setDebugOutput(true);
    Serial.println();
    
    // Khởi tạo camera
    initCamera();
    pinMode(FLASH_LED_GPIO, OUTPUT);
    // Cấu hình chân nút nhấn
    // INPUT_PULLUP: kéo lên nguồn 3.3V
    pinMode(BUTTON_PIN, INPUT_PULLUP); 
    
    // Kết nối Wi-Fi
    connectWiFi();
}

void loop() {
    // Đọc trạng thái nút nhấn (LOW khi nhấn)
    int reading = digitalRead(BUTTON_PIN);

    // Chống rung nút nhấn (Debounce)
    if (reading == LOW && !isButtonPressed && !isProcessing) {
        // Nếu nút đang được nhấn và ổn định -> Thực hiện chức năng
        if ((millis() - lastDebounceTime) > debounceDelay) {
            isButtonPressed = true;
            lastDebounceTime = millis();
            captureAndSend();
        }
    } else if (reading == HIGH) {
        // Reset trạng thái khi nút được nhả
        isButtonPressed = false;
        lastDebounceTime = millis();
    }
    
    // Đợi một chút
    delay(10); 
}

