# -*- coding: utf-8 -*-
"""
Chương trình chính Bot Quét Nến M5 FTTUSDT Binance Spot
Phiên bản: 1.1.1 (Khắc phục lỗi HTTP 451 & Tối ưu Render Singapore 24/7)
"""

import sys
import time
import argparse
import logging
from datetime import datetime

# Thiết lập UTF-8 cho console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config
from binance_scanner import BinanceScanner
from telegram_notifier import send_candle_alert, send_startup_alert, send_telegram_message
from web_server import start_web_server, bot_status

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("FTT_Bot")

def run_test_alert():
    """Gửi một tin nhắn cảnh báo mẫu để kiểm tra kết nối và định dạng Telegram."""
    logger.info("Đang gửi tin nhắn cảnh báo mẫu về Telegram...")
    fake_candle = {
        "open_time": datetime.now(),
        "close_time": datetime.now(),
        "open": 0.2550,
        "high": 0.2650,
        "low": 0.2540,
        "close": 0.2635,
        "volume": 245150.80,
        "quote_volume": 63800.50,
        "trades_count": 890,
        "price_change_pct": 3.33
    }
    success = send_candle_alert(fake_candle)
    if success:
        logger.info("✅ Gửi cảnh báo mẫu thành công! Hãy kiểm tra nhóm Telegram của bạn.")
    else:
        logger.error("❌ Gửi cảnh báo mẫu thất bại! Vui lòng kiểm tra lại token và chat_id.")

def main():
    parser = argparse.ArgumentParser(description=f"Bot Quét Nến M5 {config.SYMBOL} Binance Spot v{config.__version__}")
    parser.add_argument("--test-alert", action="store_true", help="Gửi một cảnh báo mẫu đến Telegram để kiểm tra")
    args = parser.parse_args()

    print("=" * 65)
    print(f"   BOT QUÉT NẾN M5 {config.SYMBOL} - BINANCE SPOT (v{config.__version__})")
    print("=" * 65)
    print(f" 📌 Cặp giao dịch:    {config.SYMBOL}")
    print(f" ⏱ Khung thời gian:  {config.INTERVAL}")
    print(f" 📈 Ngưỡng tăng giá:   >= +{config.PRICE_CHANGE_THRESHOLD}%")
    print(f" 📦 Ngưỡng khối lượng: >= {config.VOLUME_THRESHOLD:,.0f} FTT")
    print(f" 💬 Telegram Chat ID:  {config.TELEGRAM_CHAT_ID}")
    print(f" 🌐 Cổng Web Server:   {config.PORT} (Render Health Check)")
    print(f" ⏰ Chu kỳ kiểm tra:  mỗi {config.CHECK_INTERVAL_SECONDS} giây")
    print("=" * 65)

    if args.test_alert:
        run_test_alert()
        return

    # Khởi động Web Server (phục vụ Health Check & Keep-Alive trên Render.com)
    try:
        start_web_server(config.PORT)
        bot_status["status"] = "Active (Scanning)"
    except Exception as e:
        logger.warning(f"Không thể khởi động Web Server trên cổng {config.PORT}: {e}")

    # Khởi tạo Scanner
    scanner = BinanceScanner()
    
    # Đánh dấu các nến cũ để không báo nến trong quá khứ
    scanner.mark_existing_candles_as_processed()

    # Lấy giá khởi điểm
    try:
        init_klines = scanner.fetch_klines(limit=1)
        if init_klines:
            bot_status["current_price"] = float(init_klines[-1][4])
    except Exception:
        pass

    # Gửi thông báo khởi động về Telegram
    if config.SEND_STARTUP_NOTIFICATION:
        logger.info("Đang gửi thông báo khởi động lên Telegram...")
        send_startup_alert()

    logger.info("🚀 Bot đang chạy! Chờ đợi các cây nến M5 tiếp theo đóng nến...")
    last_heartbeat_time = 0

    try:
        while True:
            try:
                candle, is_qualified = scanner.check_new_closed_candle()
                
                if candle:
                    # Có cây nến M5 vừa mới đóng
                    open_str = candle["open_time"].strftime("%H:%M:%S")
                    close_str = candle["close_time"].strftime("%H:%M:%S")
                    chg_sign = "+" if candle["price_change_pct"] >= 0 else ""
                    
                    # Cập nhật thông tin nến đóng gần nhất vào bộ nhớ web
                    bot_status["last_closed_candle"] = {
                        "time": f"{open_str} - {close_str}",
                        "close": f"{candle['close']:.4f}",
                        "change": f"{chg_sign}{candle['price_change_pct']:.2f}%",
                        "volume": f"{candle['volume']:,.2f} FTT"
                    }
                    bot_status["current_price"] = candle["close"]

                    log_candle_info = (
                        f"📊 [NẾN M5 VỪA ĐÓNG {open_str} -> {close_str}] "
                        f"Open: {candle['open']:.4f} | Close: {candle['close']:.4f} | "
                        f"Tăng: {chg_sign}{candle['price_change_pct']:.2f}% | "
                        f"Vol: {candle['volume']:,.2f} FTT (~${candle['quote_volume']:,.2f} USDT)"
                    )
                    
                    if is_qualified:
                        logger.warning("🚨 " + "=" * 55)
                        logger.warning(f"🚨 TÍN HIỆU ĐẠT TIÊU CHUẨN: Tăng {chg_sign}{candle['price_change_pct']:.2f}% | Vol {candle['volume']:,.2f} FTT")
                        logger.warning("🚨 " + "=" * 55)
                        logger.info(log_candle_info)
                        logger.info("Đang gửi cảnh báo đến Telegram...")
                        sent = send_candle_alert(candle)
                        if sent:
                            logger.info("✅ Đã gửi cảnh báo Telegram thành công!")
                        else:
                            logger.error("❌ Gửi cảnh báo Telegram thất bại!")
                    else:
                        logger.info(log_candle_info + " -> [Chưa đạt điều kiện]")
                
                # In thông tin nhịp tim (heartbeat) định kỳ mỗi 60 giây để biết bot vẫn sống
                now = time.time()
                if now - last_heartbeat_time >= 60:
                    last_heartbeat_time = now
                    current_klines = scanner.fetch_klines(limit=1)
                    if current_klines and len(current_klines) > 0:
                        cur_price = float(current_klines[-1][4])
                        bot_status["current_price"] = cur_price
                        logger.info(f"💓 [Đang quét] {config.SYMBOL} Giá hiện tại: {cur_price:.4f} | Đang theo dõi nến M5 tiếp theo...")
                
            except requests.RequestException as net_err:
                logger.warning(f"Mất kết nối mạng tạm thời: {net_err}. Thử lại sau {config.CHECK_INTERVAL_SECONDS}s...")
            except Exception as loop_err:
                logger.error(f"Lỗi trong vòng lặp: {loop_err}", exc_info=True)

            time.sleep(config.CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n")
        logger.info("⏹ Người dùng nhấn Ctrl+C. Đang dừng bot...")
        logger.info("Bot đã dừng an toàn.")

if __name__ == "__main__":
    main()
