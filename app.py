from flask import Flask, request, jsonify, render_template_string
import sqlite3
import base64
from datetime import datetime
from google import genai
from google.genai.errors import APIError
import threading, time
import requests

# =================== Cấu hình ===================
# LƯU Ý: Đây là API key và Token giả, cần thay thế bằng giá trị thật khi triển khai.
GEMINI_API_KEY = "YOUR_API_KEY"
ADMIN_PASSWORD = "1234" #password trong website
BOT_TOKEN = "YOUR_BOT_TOKEN"

app = Flask(__name__)

# ================= Gemini Client =================
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("Gemini client initialized.")
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    client = None

# ================= SQLite =================
DB_FILE = "waste_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS waste (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac_address TEXT,
            device_name TEXT DEFAULT 'unidentified device', -- Tên mặc định: unidentified device
            category TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_waste(mac, category):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # device_name sẽ nhận giá trị mặc định nếu đây là lần đầu MAC này xuất hiện
    c.execute('INSERT INTO waste (mac_address, category) VALUES (?, ?)', (mac, category))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Lấy thống kê và tên thiết bị
    c.execute('SELECT mac_address, device_name, category, COUNT(*) FROM waste GROUP BY mac_address, device_name, category')
    rows = c.fetchall()
    conn.close()
    
    stats = {}
    names = {}
    for mac, name, cat, count in rows:
        if mac not in stats:
            stats[mac] = {"Recycle":0,"Non-recycle":0,"Organic":0}
        stats[mac][cat] = count
        names[mac] = name  # Luôn cập nhật tên
    return stats, names

def get_mac_stats(mac):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT category, COUNT(*) FROM waste 
        WHERE mac_address = ? 
        GROUP BY category
    ''', (mac,))
    rows = c.fetchall()
    conn.close()
    
    stats = {"Recycle": 0, "Non-recycle": 0, "Organic": 0}
    for cat, count in rows:
        if cat in stats:
            stats[cat] = count
    return stats

def get_device_name(mac):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Lấy tên bất kỳ từ một record của MAC đó
    c.execute('SELECT device_name FROM waste WHERE mac_address=? LIMIT 1', (mac,))
    row = c.fetchone()
    conn.close()
    # Trả về tên hiện tại hoặc mặc định
    return row[0] if row else 'unidentified device'  


# ================= Routes =================
@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    if client is None:
        return jsonify({"status":"error","message":"Gemini Client not initialized."}),500

    data = request.get_json()
    base64_image = data.get('image_data')
    mac_address = data.get('mac_address','Unknown')
    print("Awaiting for analyzing.")

    prompt_instruction = "You are a waste classification expert, currently you are looking on the top of a handmade garbage bin. Identify the single main object in the image and classify it as 'Plastic', 'Recyclable paper', 'Recyclable can', or 'Organic'. Reply ONLY with one of these words."
    prompt_text = data.get('prompt', prompt_instruction)

    if not base64_image:
        return jsonify({"status":"error","message":"Missing image_data"}),400

    try:
        image_bytes = base64.b64decode(base64_image)
        image_part = genai.types.Part.from_bytes(data=image_bytes,mime_type='image/jpeg')
        response = client.models.generate_content(model='gemini-2.5-flash', contents=[prompt_text,image_part])
        gemini_analysis = response.text.strip()
        print(gemini_analysis)
        if gemini_analysis == "Plastic":
            save_waste(mac_address, "Non-recycle")
        elif gemini_analysis == 'Recyclable paper' or gemini_analysis == 'Recyclable can':
            save_waste(mac_address, "Recycle")
        else:
            save_waste(mac_address, "Organic")
        return app.response_class(response=gemini_analysis,status=200,mimetype='text/plain')

    except APIError as e:
        return jsonify({"status":"error","message":f"Gemini API failed: {str(e)}"}),500
    except Exception as e:
        return jsonify({"status":"error","message":f"Server error: {str(e)}"}),500

@app.route('/get-data')
def get_data():
    stats, names = get_stats()

    # Tổng tất cả device cho chart
    total_recycle = sum(counts["Recycle"] for counts in stats.values())
    total_non = sum(counts["Non-recycle"] for counts in stats.values())
    total_organic = sum(counts["Organic"] for counts in stats.values())

    # Ranking list cho bảng
    ranking_list = []
    for mac, counts in stats.items():
        total = counts["Recycle"] + counts["Non-recycle"] + counts["Organic"]
        ranking_list.append((mac, names[mac], counts, total))
    ranking_list.sort(key=lambda x:x[3], reverse=True)
    top_device = ranking_list[0][1] if ranking_list else "No Device"
    top_total = ranking_list[0][3] if ranking_list else 0

    macs = [x[0] for x in ranking_list]
    recycle_counts = [x[2]["Recycle"] for x in ranking_list]
    non_counts = [x[2]["Non-recycle"] for x in ranking_list]
    organic_counts = [x[2]["Organic"] for x in ranking_list]
    device_names = [x[1] for x in ranking_list]

    return jsonify({
        "macs": macs,
        "names": device_names,
        "recycle": recycle_counts,
        "non": non_counts,
        "organic": organic_counts,
        "totals_chart": [total_recycle, total_non, total_organic],
        "top_device": top_device,
        "top_total": top_total
    })

@app.route('/update-name', methods=['POST'])
def update_name():
    data = request.get_json()
    mac = data.get('mac')
    name = data.get('name')
    
    if not mac: 
        return jsonify({"status":"error", "message": "MAC required"}),400
        
    # CHỈ UPDATE TÊN NẾU 'name' KHÔNG RỖNG
    if not name or name.strip() == '':
        return jsonify({"status":"warning", "message": "Name is empty, no change made."}), 200
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Cập nhật tất cả các record của MAC đó với tên mới
    c.execute('UPDATE waste SET device_name=? WHERE mac_address=?', (name.strip(), mac))
    conn.commit()
    conn.close()
    return jsonify({"status":"ok"})

@app.route('/update-counts', methods=['POST'])
def update_counts():
    data = request.get_json()
    mac = data.get('mac')
    
    # Lấy giá trị mới từ POST. Nếu input trống thì là chuỗi rỗng
    new_recycle = data.get('recycle')
    new_non = data.get('non')
    new_organic = data.get('organic')
    
    if not mac:
        return jsonify({"status":"error", "message": "MAC required"}),400

    # Lấy số liệu hiện tại và tên hiện tại của MAC này
    current_stats = get_mac_stats(mac)
    current_name = get_device_name(mac)

    # Hàm xác định số lượng cuối cùng (dùng giá trị mới nếu có, nếu không thì dùng giá trị cũ)
    def get_final_count(new_val, current_key):
        # Kiểm tra nếu giá trị mới KHÔNG RỖNG
        if new_val is not None and str(new_val).strip() != '':
            try:
                # Dùng giá trị mới nếu nó là một số hợp lệ
                return int(new_val)
            except ValueError:
                # Nếu không phải số, dùng giá trị cũ
                return current_stats[current_key]
        else:
            # Dùng giá trị cũ nếu input rỗng
            return current_stats[current_key]

    final_recycle = get_final_count(new_recycle, 'Recycle')
    final_non = get_final_count(new_non, 'Non-recycle')
    final_organic = get_final_count(new_organic, 'Organic')
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        # BƯỚC 1: XÓA TẤT CẢ CÁC SỰ KIỆN CŨ CỦA MAC NÀY
        c.execute('DELETE FROM waste WHERE mac_address=?', (mac,))
        
        # BƯỚC 2: CHÈN LẠI SỐ LƯỢNG SỰ KIỆN MỚI DỰA TRÊN CÁC SỐ LƯỢNG FINAL VÀ TÊN CŨ (current_name)
        
        # Chèn các sự kiện Recycle
        for _ in range(final_recycle):
            # CHÈN KÈM TÊN CŨ
            c.execute('INSERT INTO waste (mac_address, category, device_name) VALUES (?, ?, ?)', (mac, 'Recycle', current_name))
            
        # Chèn các sự kiện Non-recycle
        for _ in range(final_non):
            c.execute('INSERT INTO waste (mac_address, category, device_name) VALUES (?, ?, ?)', (mac, 'Non-recycle', current_name))
            
        # Chèn các sự kiện Organic
        for _ in range(final_organic):
            c.execute('INSERT INTO waste (mac_address, category, device_name) VALUES (?, ?, ?)', (mac, 'Organic', current_name))
            
        conn.commit()
        return jsonify({"status":"ok", "message": "Counts updated successfully."})
        
    except Exception as e:
        conn.rollback()
        print(f"Database error in update_counts: {e}")
        return jsonify({"status":"error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route("/submit-waste", methods=["POST"])
def submit_waste():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "No JSON payload"}), 400

    mac = data.get("mac_address")
    category = data.get("category")

    if not mac or not category:
        return jsonify({"ok": False, "error": "Missing mac_address or category"}), 400

    category = category.lower()
    if category == "recycle":
        save_waste(mac, "Recycle")
    elif category == "non-recycle":
        save_waste(mac, "Non-recycle")
    elif category == "organic":
        save_waste(mac, "Organic")
    else:
        return jsonify({"ok": False, "error": "Invalid category"}), 400

    print(f"[INFO] Received from {mac}: {category}")
    return jsonify({"ok": True, "mac_address": mac, "category": category})


# ================= Telegram Bot =================
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(chat_id, text):
    try:
        requests.post(
            TELEGRAM_API_URL,
            data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
        )
    except Exception as e:
        print(f"Telegram send error: {e}")

def telegram_polling():
    OFFSET = None
    while True:
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": OFFSET, "timeout": 30}
            ).json()

            for result in resp.get("result", []):
                OFFSET = result["update_id"] + 1
                message = result.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")

                if text.startswith("/ranking") and chat_id:
                    parts = text.split(" ", 1)
                    if len(parts) < 2:
                        send_telegram_message(chat_id, "⚠️ Please provide *DEVICE NAME*.\nExample: `/ranking 12A4`")
                        continue

                    device_name_query = parts[1].strip()

                    stats, names = get_stats()
                    ranking_list = []
                    for mac, counts in stats.items():
                        total = counts["Recycle"] + counts["Non-recycle"] + counts["Organic"]
                        ranking_list.append((mac, names[mac], counts, total))
                    ranking_list.sort(key=lambda x: x[3], reverse=True)

                    found = False
                    for i, item in enumerate(ranking_list):
                        if item[1].lower() == device_name_query.lower():
                            msg = (
                                f"🏷️ *Device:* {item[1]}\n"
                                f"🏆 *Rank:* {i + 1}\n\n"
                                f"♻️ *Recycle:* {item[2]['Recycle']}\n"
                                f"🚯 *Non-Recycle:* {item[2]['Non-recycle']}\n"
                                f"🍃 *Organic:* {item[2]['Organic']}\n"
                                f"📊 *Total:* {item[3]}"
                            )
                            send_telegram_message(chat_id, msg)
                            found = True
                            break

                    if not found:
                        send_telegram_message(chat_id, f"❌ Device *'{device_name_query}'* not found in ranking.")
        except Exception as e:
            print(f"Telegram polling error: {e}")
            time.sleep(5)

threading.Thread(target=telegram_polling, daemon=True).start()


# ================= Dashboard =================
@app.route('/')
def index():
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Smart Waste Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
/* ===================== Body & Fonts ===================== */
body {
    font-family: 'Poppins', sans-serif;
    background: radial-gradient(circle at top left, #121212, #1a1a1a);
    color: #f8f8f8;
    margin: 0;
    padding: 0;
    font-size: 16px; /* Base font size */
}

/* ===================== Header ===================== */
h1 {
    text-align: center;
    padding: 25px;
    color: #00ff9d;
    text-shadow: 0 0 15px #00ff9d, 0 0 25px #00ff9d;
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
    from { text-shadow: 0 0 10px #00ff9d; }
    to { text-shadow: 0 0 25px #00ffaa, 0 0 40px #00ff9d; }
}

/* ===================== Container ===================== */
.container {
    width: 95%;
    max-width: 1200px;
    margin: auto;
    padding: 20px;
}

/* ===================== Tabs ===================== */
.tab-container {
    display: flex;
    width: 100%;
    margin: 25px 0;
    height: 60px;
    box-shadow: 0 0 20px rgba(0, 255, 157, 0.3);
    border-radius: 12px;
    overflow: hidden;
}
.tab {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    cursor: pointer;
    transition: all 0.3s ease;
    color: #f8f8f8;
}
.tab:hover { filter: brightness(1.2); }
.tab.active {
    background: linear-gradient(90deg,#00ff9d,#007f6b);
    color: #000;
}
.tab-content {
    display: block;
    opacity: 0;
    transform: translateX(50px);
    transition: all 0.5s ease;
    max-height: 0;
    overflow: hidden;
}
.tab-content.active {
    opacity: 1;
    transform: translateX(0);
    max-height: 2000px;
}

/* ===================== Chart (Đã sửa lỗi bo góc) ===================== */
.chart-container {
    width: 100%;
    background: #2b2b2b;
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 0 15px #000;
    margin-bottom: 30px;
    overflow: hidden; /* <--- FIX: Đảm bảo canvas bị cắt theo bo góc của container */
}
.chart-container canvas {
    width: 100% !important;
    height: auto !important;
    border-radius: 10px; /* Thêm bo góc cho canvas */
}

/* ===================== Top Device Box ===================== */
.ranking-box {
    width: 100%;
    max-width: 100%;
    background: linear-gradient(90deg,#00ff9d,#007f6b);
    color: #000;
    padding: 15px 20px;
    border-radius: 15px; 
    text-align: center;
    font-weight: 600;
    font-size: 1.2rem;
    box-shadow: 0 0 20px rgba(0,255,157,0.5);
    margin-bottom: 25px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    word-wrap: break-word;
}
.ranking-box:hover {
    transform: scale(1.03);
    box-shadow: 0 0 30px rgba(0,255,157,0.8);
}

/* ===================== Ranking Table ===================== */
.ranking-table {
    width: 100%;
    overflow-x: auto; /* scroll ngang trên mobile */
}

.ranking-table table {
    width: 100%;
    min-width: 700px;
    table-layout: fixed;
    border-collapse: collapse;
    margin-top: 15px;
    background: #202020;
    border-radius: 15px; 
    overflow: hidden; 
    box-shadow: 0 0 10px #111;
}

.ranking-table th, .ranking-table td {
    text-align: center;
    padding: 12px;
    border-bottom: 1px solid #333;
    word-break: break-word;
}

.ranking-table th {
    background-color: #00ff9d;
    color: #000;
    font-weight: bold;
}

.ranking-table tr:nth-child(even) {
    background-color: #2c2c2c;
}
.ranking-table tr:hover {
    background-color: #333;
    transition:0.3s;
}

/* Top 3 Styles */
.top1 { background: linear-gradient(90deg,#ffd700,#ffea00); color: #000; font-weight: bold; box-shadow: 0 0 15px #ffd700; }
.top2 { background: linear-gradient(90deg,#c0c0c0,#e0e0e0); color: #000; font-weight: bold; box-shadow: 0 0 10px #c0c0c0; }
.top3 { background: linear-gradient(90deg,#cd7f32,#e6a565); color: #000; font-weight: bold; box-shadow: 0 0 8px #cd7f32; }

/* ===================== Settings Form (Bo góc 10px) ===================== */
#setting-form input, 
#setting-form button {
    padding: 8px 12px;
    margin: 6px;
    border-radius: 10px; /* Tăng từ 6px lên 10px để góc bo tròn rõ hơn */
    border: none;
    outline: none;
}
#setting-form button {
    background: #00ff9d;
    color: #000;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.3s;
}
#setting-form button:hover {
    background-color: #00d481;
}
#setting-form input[type=password] {
    width: 200px;
}
#settings-fields {
    opacity: 0;
    transform: translateY(-20px);
    transition: all 0.5s ease;
    max-height: 0;
    overflow: hidden;
}
#settings-fields.show {
    opacity: 1;
    transform: translateY(0);
    max-height: 500px;
    /* Dùng flexbox để căn giữa các input */
    display: flex; 
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    padding: 10px 0;
}
#message-box, #settings-message {
    color: #00ff9d;
    text-align: center;
    font-weight: 600;
}

/* ===================== Responsive (Cải tiến) ===================== */

/* Tablet/Desktop 1024px */
@media(max-width: 1024px) {
    body { font-size: 15px; } /* Giảm nhẹ font cơ sở */
    .chart-container { padding: 15px; }
    h1 { font-size: 1.8rem; }
    .ranking-box { font-size: 1rem; padding: 10px; }
    th, td { font-size: 0.95rem; padding: 10px; }
}

/* Mobile/Tablet 768px */
@media(max-width: 768px) {
    body { font-size: 14px; } /* Giảm font cơ sở cho tablet/mobile */
    h1 { font-size: 1.5rem; }
    .tab { font-size: 1.1rem; height: 50px; }
    .ranking-box { font-size: 0.95rem; padding: 8px 10px; }
    th, td { font-size: 0.85rem; padding: 8px; }
    .chart-container { padding: 10px; }
    #wasteChart { height: 250px !important; }
}

/* Small Mobile 480px (Đảm bảo form Settings scale tốt) */
@media(max-width: 480px) {
    body { font-size: 13px; } /* Giảm font cơ sở cho điện thoại nhỏ */
    h1 { font-size: 1.2rem; padding: 15px; }

    /* Khối nhập mật khẩu: xếp chồng và full width */
    #password-section {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    #setting-form input[type=password],
    #setting-form button#check-password {
        width: 95%; /* Gần full width */
        margin: 5px 0;
    }

    /* Khối settings field: xếp chồng và full width */
    #settings-fields {
        flex-direction: column;
    }
    #settings-fields input,
    #settings-fields button {
        width: 95%; /* Các input khác full width */
        box-sizing: border-box; /* Tính cả padding và border vào width */
        margin: 5px auto;
    }

    .ranking-box { font-size: 0.9rem; padding: 6px 8px; }
    th, td { font-size: 0.75rem; padding: 6px; }
    #wasteChart { height: 200px !important; }
}
</style>

</head>
<body>
<h1>♻️ Smart Garbage Bin Dashboard</h1>
<div class="container">

<div class="tab-container">
  <div id="tab-statistics" class="tab active" data-tab="tab-stats">📊 Statistics</div>
  <div id="tab-settings-btn" class="tab" data-tab="tab-settings">⚙️ Settings</div>
</div>


<div id="tab-stats" class="tab-content active">
<div class="chart-container"><canvas id="wasteChart"></canvas></div>
<div class="ranking-box" id="top-device-box">
  🔝 Top Device: No Device 🏆 Total Items: 0
</div>
<div class="ranking-table">
<h2>📊 Device Ranking</h2>
<table>
<tr><th>Rank</th><th>Device Name</th><th>MAC</th><th>Recycle</th><th>Non-Recycle</th><th>Organic</th><th>Total</th></tr>
<tbody id="ranking-tbody">
</tbody>
</table>
</div>
<div id="message-box"></div>
</div>


<div id="tab-settings" class="tab-content">
<h2 style="color:#00ff9d;text-align:center;">⚙️ Settings</h2>
<form id="setting-form" style="text-align:center;">
  <div id="password-section">
    <input type="password" id="admin-password" placeholder="Enter Password"/>
    <button type="button" id="check-password">Submit</button>
  </div>
  <div id="settings-fields">
    <input type="text" id="mac-input" placeholder="MAC Address (Required)"/>
    

<input type="text" id="name-input" placeholder="Device Name (Optional)"/> 
    <input type="number" id="recycle-input" placeholder="Recycle Count"/>
    <input type="number" id="non-input" placeholder="Non-Recycle Count"/>
    <input type="number" id="organic-input" placeholder="Organic Count"/>
    <button type="button" id="save-settings">Save</button>
  </div>
  <div id="settings-message" style="color:#00ff9d;margin-top:10px;"></div>
</form>
</div>

</div>

<script>
// Tab switch
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const settingsFields = document.getElementById('settings-fields');
    
    // Nếu Settings đang mở và chuyển đi tab khác → khoá
    if(settingsFields.classList.contains('show') && tab.id !== 'tab-settings-btn'){
        lockSetting('🔒 Locked');
    }

    // Switch tab bình thường
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    const newTabContent = document.getElementById(tab.dataset.tab);
    newTabContent.classList.add('active');
  });
});

let failedAttempts = 0;
let lockUntil = null;
let settingTimeout = null;

// Hàm khoá form setting
function lockSetting(message='🔒 Locked'){
    document.getElementById('settings-fields').classList.remove('show');
    document.getElementById('password-section').style.display = 'flex'; // Trả về display:flex sau khi unlock
    document.getElementById('admin-password').value = '';
    document.getElementById('settings-message').innerText = message;
    clearTimeout(settingTimeout);
}

// Password submit
document.getElementById('check-password').onclick=()=>{
    const pw = document.getElementById('admin-password').value;

    const now = new Date().getTime();
    if(lockUntil && now < lockUntil){
        const remain = Math.ceil((lockUntil - now)/1000);
        document.getElementById('settings-message').innerText = `🔒 Locked. Wait ${remain}s`;
        return;
    }

if(pw==='{{ADMIN_PASSWORD}}'){
    failedAttempts = 0;
    document.getElementById('password-section').style.display = 'none';
    const fields = document.getElementById('settings-fields');
    fields.classList.add('show'); // thêm class show để chạy animation
    document.getElementById('settings-message').innerText='⏳ You have 3 minutes to edit';

    // Set timeout 3 phút để auto lock
    settingTimeout = setTimeout(()=>{
        lockSetting('⏰ 3 minutes elapsed. Locked.');
        fields.classList.remove('show');
    }, 3*60*1000);

    // Countdown hiển thị
    let countdown = 3*60;
    const interval = setInterval(()=>{
        if(!fields.classList.contains('show')){
            clearInterval(interval);
            return;
        }
        const min = Math.floor(countdown/60);
        const sec = countdown % 60;
        document.getElementById('settings-message').innerText = `⏳ Time left: ${min}:${sec<10?'0'+sec:sec}`;
        countdown--;
        if(countdown<0) clearInterval(interval);
    },1000);

    }else{
        failedAttempts++;
        if(failedAttempts>=3){
            lockUntil = new Date().getTime() + 10*60*1000; // khóa 10 phút
            failedAttempts = 0;
            let remain = 10*60;
            lockSetting(`❌ Too many failed attempts. Locked 10 min. ${Math.floor(remain/60)}:${remain%60}`);
            const interval = setInterval(()=>{
                remain--;
                if(remain<=0){
                    clearInterval(interval);
                    document.getElementById('settings-message').innerText='🔒 Locked';
                }else{
                    document.getElementById('settings-message').innerText=`❌ Too many failed attempts. Locked 10 min. ${Math.floor(remain/60)}:${remain%60}`;
                }
            },1000);
        }else{
            document.getElementById('settings-message').innerText=`❌ Wrong password. Attempt ${failedAttempts}/3`;
        }
    }
};

// Save Settings
document.getElementById('save-settings').onclick=async()=>{
  const mac=document.getElementById('mac-input').value.trim();
  // Lấy giá trị, nếu rỗng thì là chuỗi rỗng
  const name=document.getElementById('name-input').value.trim(); 
  const recycle=document.getElementById('recycle-input').value.trim();
  const non=document.getElementById('non-input').value.trim();
  const organic=document.getElementById('organic-input').value.trim();
  
  if(!mac){alert('MAC required');return;}
  document.getElementById('settings-message').innerText='Saving...';
  
  try{
    let allOk = true;
    
    // 1. Update name: CHỈ GỌC API NẾU 'name' KHÔNG RỖNG
    if(name){
      const nameRes = await fetch('/update-name',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({mac,name})
      });
      if(!nameRes.ok) allOk = false;
    }
    
    // 2. Update counts: Gửi đi các giá trị (kể cả chuỗi rỗng) để logic Python xử lý giữ lại giá trị cũ
    const countsRes = await fetch('/update-counts',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({mac,recycle,non,organic})
    });
    
    if(countsRes.status === 500) allOk = false;

    if(allOk){
        document.getElementById('settings-message').innerText='Saved!';
    } else {
        document.getElementById('settings-message').innerText='❌ Saved with some errors or warnings.';
    }

    // Xóa input sau khi lưu thành công (giữ lại MAC để tiện chỉnh sửa tiếp)
    // document.getElementById('mac-input').value='';
    document.getElementById('name-input').value='';
    document.getElementById('recycle-input').value='';
    document.getElementById('non-input').value='';
    document.getElementById('organic-input').value='';
    
    updateChartData();

  }catch(e){
    console.error(e);
    document.getElementById('settings-message').innerText='❌ Error saving data!';
  }
};


// Chart

const ctx=document.getElementById('wasteChart').getContext('2d');
const wasteChart=new Chart(ctx,{
    type:'bar',
    data:{
        labels:["Recycle","Non-Recycle","Organic"],
        datasets:[{
            data:[0,0,0],
            backgroundColor:['#00ff9d','#ff6b6b','#ffd166'],
            // 👇 SỬA ĐỔI QUAN TRỌNG: Chỉ định bo góc cho cả topLeft và topRight
            borderRadius:{
                topLeft: 6,
                topRight: 6,
                bottomLeft: 0,
                bottomRight: 0
            },
            borderSkipped: false // Giữ lại để đảm bảo không bỏ qua cạnh nào
        }]
    },
    options:{
        responsive:true,
        maintainAspectRatio:false, // ⚠ quan trọng để canvas co giãn
        plugins:{
            title:{
                display:true,
                text:'♻️ Total Waste Items: 0',
                color:'#00ff9d',
                font:{size:20, weight:'bold'}
            },
            legend:{display:false}
        },
        scales:{
            y:{
                beginAtZero:true,
                grid:{color:'#444',borderColor:'#888',lineWidth:1},
                ticks:{color:'#ffd166',font:{size:14,weight:'bold'}}
            },
            x:{
                ticks:{color:'#ffd166',font:{size:16,weight:'bold'}},
                grid:{drawTicks:false,color:'#333'}
            }
        }
    }
});


async function updateChartData(){
  try{
    const res = await fetch('/get-data');
    const data = await res.json();

    const totalRecycle = data.recycle.reduce((a,b)=>a+b,0);
    const totalNon = data.non.reduce((a,b)=>a+b,0);
    const totalOrganic = data.organic.reduce((a,b)=>a+b,0);
    const totalAll = totalRecycle + totalNon + totalOrganic;

    // Update chart data
    wasteChart.data.datasets[0].data = [totalRecycle, totalNon, totalOrganic];

    // Update chart title
    wasteChart.options.plugins.title.text = `♻️ Total Waste Items: ${totalAll}`;
    wasteChart.update();

    // Update top device box
    document.getElementById('top-device-box').innerHTML = `🔝 Top Device: ${data.top_device} <br> 🏆 Total Items: ${data.top_total}`;
    
    // Update ranking table
    const tbody = document.getElementById('ranking-tbody');
    tbody.innerHTML='';
    for(let i=0;i<data.macs.length;i++){
      const total = data.recycle[i] + data.non[i] + data.organic[i];
      let rowClass = '';
      let rankEmoji = `🏅 ${i+1}`;
      // Hiệu ứng đặc biệt cho top 3
      if(i===0){
        rowClass = 'top1';
        rankEmoji = '🥇 1';
      } else if(i===1){
        rowClass = 'top2';
        rankEmoji = '🥈 2';
      } else if(i===2){
        rowClass = 'top3';
        rankEmoji = '🥉 3';
      }
      tbody.innerHTML+=`<tr class="${rowClass}"><td>${rankEmoji}</td><td>${data.names[i]}</td><td>${data.macs[i]}</td><td>${data.recycle[i]}</td><td>${data.non[i]}</td><td>${data.organic[i]}</td><td>${total}</td></tr>`;
    }

  }catch(e){console.error(e);}
}

updateChartData();
setInterval(updateChartData, 10000);

// Khi tab mất focus, cũng khoá ngay
window.addEventListener('blur', () => {
    const settingsFields = document.getElementById('settings-fields');
    if(settingsFields.classList.contains('show')){
        lockSetting('🔒 Locked');
    }
});


</script>

</body>
</html>
    """
    return render_template_string(html_template, ADMIN_PASSWORD=ADMIN_PASSWORD)

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000)
