# -*- coding: utf-8 -*-
"""
Chương trình chính Bot Quét Nến M5 FTTUSDT Binance Spot
Phiên bản: 1.1.2 (Chuyển sang Binance WebSocket Streams, chống dứt điểm lỗi IP Ban HTTP 418)
"""

import sys
import time
import asyncio
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

def handle_price_update(current_price: float):
    """Cập nhật giá theo thời gian thực vào web server."""
    bot_status["current_price"] = current_price
    bot_status["last_check_time"] = datetime.now()

def handle_candle_closed(candle: dict, is_qualified: bool):
    """Xử lý sự kiện khi có một cây nến M5 vừa đóng hoàn toàn."""
    open_str = candle["open_time"].strftime("%H:%M:%S")
    close_str = candle["close_time"].strftime("%H:%M:%S")
    chg_sign = "+" if candle["price_change_pct"] >= 0 else ""

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
        bot_status["alerts_sent_count"] = bot_status.get("alerts_sent_count", 0) + 1
        bot_status["last_alert_time"] = datetime.now()
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
    print(f" ⚡ Phương thức kết nối: Binance WebSocket Stream (Real-Time)")
    print("=" * 65)

    if args.test_alert:
        run_test_alert()
        return

    # Khởi động Web Server (phục vụ Health Check & Keep-Alive trên Render.com)
    try:
        start_web_server(config.PORT)
        bot_status["status"] = "Active (WebSocket Stream)"
    except Exception as e:
        logger.warning(f"Không thể khởi động Web Server trên cổng {config.PORT}: {e}")

    # Gửi thông báo khởi động về Telegram
    if config.SEND_STARTUP_NOTIFICATION:
        logger.info("Đang gửi thông báo khởi động lên Telegram...")
        send_startup_alert()

    logger.info("🚀 Bot đang chạy! Kết nối WebSocket Stream để nhận nến M5 theo thời gian thực...")

    scanner = BinanceScanner(
        on_candle_closed=handle_candle_closed,
        on_price_update=handle_price_update
    )

    try:
        asyncio.run(scanner.start_stream())
    except KeyboardInterrupt:
        print("\n")
        logger.info("⏹ Người dùng nhấn Ctrl+C. Đang dừng bot...")
        scanner.running = False
        logger.info("Bot đã dừng an toàn.")

if __name__ == "__main__":
    main()
