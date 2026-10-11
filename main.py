import os
import time
import threading
import requests
from flask import Flask

# ==================== CẤU HÌNH WEB SERVER DÀNH CHO RENDER ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "OKX Telegram Bot is Running Live 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
# =============================================================================

# ==================== CẤU HÌNH THÔNG TIN BOT ====================
TELEGRAM_BOT_TOKEN = "8558975073:AAE_oSrhlG-z72Xr5uW8f-XkYF0xe40A0hE"
TELEGRAM_CHAT_ID = "8861795362"

PERCENT_THRESHOLD = 2.0 
TIME_WINDOW_SECONDS = 300 
CHECK_INTERVAL_SECONDS = 60 

OKX_API_URL = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
price_cache = {}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        if not response.ok:
            print(f"Lỗi Telegram: {response.text}")
    except Exception as e:
        print(f"Lỗi gửi tin nhắn Telegram: {e}")

# --- TÍNH NĂNG LẮNG NGHE TIN NHẮN "HEY" TỪ BẠN ---
def listen_telegram_messages():
    offset = None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    while True:
        try:
            params = {"timeout": 20, "offset": offset}
            response = requests.get(url, params=params, timeout=25)
            data = response.json()
            
            if data.get("ok"):
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message", {})
                    text = message.get("text", "").strip().lower()
                    
                    # Nếu nhận được chữ "hey"
                    if text == "hey":
                        reply = "🟢 *Tôi vẫn ở đây và đang hoạt động bình thường!*"
                        send_telegram(reply)
        except Exception as e:
            print(f"Lỗi khi nhận tin nhắn: {e}")
        time.sleep(1)

# --- TÍNH NĂNG THEO DÕI BIẾN ĐỘNG GIÁ OKX ---
def check_market():
    try:
        response = requests.get(OKX_API_URL, timeout=10)
        data = response.json()
        
        if data.get("code") == "0":
            tickers = data.get("data", [])
            current_time = time.time()
            
            for item in tickers:
                inst_id = item.get("instId")
                if not inst_id.endswith("-USDT"):
                    continue
                
                last_price = float(item.get("last"))
                
                if inst_id not in price_cache:
                    price_cache[inst_id] = {"price": last_price, "time": current_time}
                else:
                    old_data = price_cache[inst_id]
                    old_price = old_data["price"]
                    old_time = old_data["time"]
                    
                    if current_time - old_time >= TIME_WINDOW_SECONDS:
                        if old_price > 0:
                            change = ((last_price - old_price) / old_price) * 100
                            if change >= PERCENT_THRESHOLD:
                                msg = (
                                    f"🚀 *CẢNH BÁO TĂNG GIÁ (5 phút)*\n\n"
                                    f"🔹 Coin: *{inst_id}*\n"
                                    f"📈 Tăng: `+{change:.2f}%`\n"
                                    f"💵 Giá hiện tại: `{last_price}`\n"
                                    f"📉 Giá 5 phút trước: `{old_price}`"
                                )
                                send_telegram(msg)
                                print(f"[{time.strftime('%H:%M:%S')}] Đã gửi báo động: {inst_id} (+{change:.2f}%)")
                        
                        price_cache[inst_id] = {"price": last_price, "time": current_time}
                        
    except Exception as e:
        print(f"Lỗi truy vấn API OKX: {e}")

def bot_loop():
    print("=== BOT THEO DÕI OKX ĐÃ BẮT ĐẦU CHẠY ===")
    send_telegram("🤖 *Bot theo dõi biến động giá OKX (5 phút) đã khởi chạy thành công!*")
    while True:
        check_market()
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    # 1. Luồng chạy theo dõi giá OKX
    t_market = threading.Thread(target=bot_loop)
    t_market.daemon = True
    t_market.start()
    
    # 2. Luồng lắng nghe câu lệnh "hey"
    t_listen = threading.Thread(target=listen_telegram_messages)
    t_listen.daemon = True
    t_listen.start()
    
    # 3. Khởi chạy Web Server cho Render
    run_flask()
