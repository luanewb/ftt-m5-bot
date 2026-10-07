# -*- coding: utf-8 -*-
"""
Module gửi thông báo qua Telegram Bot
Phiên bản: 1.1.2
"""

import logging
import requests
from datetime import datetime
import config

logger = logging.getLogger(__name__)

def send_telegram_message(text: str) -> bool:
    """
    Gửi tin nhắn văn bản (HTML) về nhóm Telegram qua Telegram Bot API.
    """
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_json = response.json()
        if response.status_code == 200 and res_json.get("ok"):
            return True
        else:
            logger.error(f"Lỗi gửi Telegram: HTTP {response.status_code} - {res_json.get('description', '')}")
            return False
    except Exception as e:
        logger.error(f"Ngoại lệ khi gửi Telegram: {e}")
        return False

def format_candle_alert(candle: dict) -> str:
    """
    Định dạng tin nhắn cảnh báo khi cây nến M5 đạt tiêu chuẩn.
    """
    open_time_str = candle["open_time"].strftime("%H:%M:%S")
    close_time_str = candle["close_time"].strftime("%H:%M:%S")
    date_str = candle["close_time"].strftime("%d/%m/%Y")
    
    msg = (
        f"🚨 <b>[BINANCE SPOT - M5 ALERT]</b> 🚨\n\n"
        f"💎 <b>Cặp tiền:</b> <code>{config.SYMBOL}</code>\n"
        f"📊 <b>Khung nến:</b> <code>{config.INTERVAL}</code> (Vừa đóng nến)\n"
        f"📈 <b>Mức tăng:</b> <b>+{candle['price_change_pct']:.2f}%</b> (≥ {config.PRICE_CHANGE_THRESHOLD}%)\n"
        f"📦 <b>Khối lượng FTT:</b> <b>{candle['volume']:,.2f} FTT</b> (≥ {config.VOLUME_THRESHOLD:,.0f})\n"
        f"💵 <b>Giá trị USDT:</b> ~{candle['quote_volume']:,.2f} USDT\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>Giá Mở (Open):</b> <code>{candle['open']:.4f}</code>\n"
        f"💰 <b>Giá Đóng (Close):</b> <code>{candle['close']:.4f}</code>\n"
        f"🔺 <b>Đỉnh (High):</b> <code>{candle['high']:.4f}</code>\n"
        f"🔻 <b>Đáy (Low):</b> <code>{candle['low']:.4f}</code>\n"
        f"⏰ <b>Thời gian nến:</b> {open_time_str} ➔ {close_time_str} ({date_str})\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <a href=\"https://www.binance.com/vi/trade/{config.SYMBOL[:3]}_{config.SYMBOL[3:]}?type=spot\">Xem biểu đồ Binance Spot</a>"
    )
    return msg

def send_candle_alert(candle: dict) -> bool:
    """
    Gửi cảnh báo nến hoàn chỉnh về Telegram.
    """
    message = format_candle_alert(candle)
    return send_telegram_message(message)

def send_startup_alert() -> bool:
    """
    Gửi thông báo khi bot bắt đầu hoạt động.
    """
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg = (
        f"🤖 <b>Bot Quét Nến M5 FTTUSDT (v{config.__version__})</b>\n\n"
        f"✅ <b>Trạng thái:</b> Đang chạy và theo dõi\n"
        f"🎯 <b>Cặp tiền:</b> {config.SYMBOL} (Binance Spot)\n"
        f"⏱ <b>Khung giờ:</b> {config.INTERVAL}\n"
        f"📋 <b>Điều kiện kích hoạt:</b>\n"
        f"  • Nến tăng: ≥ +{config.PRICE_CHANGE_THRESHOLD}%\n"
        f"  • Khối lượng: ≥ {config.VOLUME_THRESHOLD:,.0f} FTT\n"
        f"  • Thời điểm: Ngay khi đóng nến M5\n"
        f"🕒 <b>Khởi chạy lúc:</b> {now_str}"
    )
    return send_telegram_message(msg)
