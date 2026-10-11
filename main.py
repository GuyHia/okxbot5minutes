import time
import requests

# ==================== ĐÃ CẤU HÌNH THÔNG TIN CỦA BẠN ====================
TELEGRAM_BOT_TOKEN = "8558975073:AAE_oSrhlG-z72Xr5uW8f-XkYF0xe40A0hE"
TELEGRAM_CHAT_ID = "8861795362"

# Ngưỡng phần trăm tăng giá để báo động (ví dụ: 2.0 = tăng >= 2%)
PERCENT_THRESHOLD = 2.0 

# Khung thời gian theo dõi (300 giây = 5 phút)
TIME_WINDOW_SECONDS = 300 

# Thời gian nghỉ giữa các lần quét thị trường (60 giây quét 1 lần)
CHECK_INTERVAL_SECONDS = 60 
# =======================================================================

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
        print(f"Lỗi kết nối Telegram: {e}")

def check_market():
    try:
        response = requests.get(OKX_API_URL, timeout=10)
        data = response.json()
        
        if data.get("code") == "0":
            tickers = data.get("data", [])
            current_time = time.time()
            
            for item in tickers:
                inst_id = item.get("instId")
                
                # Chỉ lọc các cặp giao dịch đuôi -USDT (Futures)
                if not inst_id.endswith("-USDT"):
                    continue
                
                last_price = float(item.get("last"))
                
                if inst_id not in price_cache:
                    # Lưu giá mốc ban đầu
                    price_cache[inst_id] = {"price": last_price, "time": current_time}
                else:
                    old_data = price_cache[inst_id]
                    old_price = old_data["price"]
                    old_time = old_data["time"]
                    
                    # Khi đã trôi qua đủ thời gian (5 phút)
                    if current_time - old_time >= TIME_WINDOW_SECONDS:
                        if old_price > 0:
                            change = ((last_price - old_price) / old_price) * 100
                            
                            # Nếu mức tăng vượt ngưỡng cài đặt (ví dụ >= 2%)
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
                        
                        # Cập nhật mốc giá mới cho chu kỳ 5 phút kế tiếp
                        price_cache[inst_id] = {"price": last_price, "time": current_time}
                        
    except Exception as e:
        print(f"Lỗi truy vấn API OKX: {e}")

if __name__ == "__main__":
    print("=== BOT THEO DÕI OKX ĐÃ BẮT ĐẦU CHẠY ===")
    send_telegram("🤖 *Bot theo dõi biến động giá OKX (5 phút) đã hoạt động!*")
    
    while True:
        check_market()
        time.sleep(CHECK_INTERVAL_SECONDS)
