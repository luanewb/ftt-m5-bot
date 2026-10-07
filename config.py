# -*- coding: utf-8 -*-
"""
Cấu hình cho Bot quét nến M5 FTTUSDT Binance Spot
Phiên bản: 1.1.2 (Chuyển sang Binance WebSocket Streams, chống dứt điểm lỗi IP Ban HTTP 418)
"""

import os

# Phiên bản phần mềm
__version__ = "1.1.2"

# Telegram Bot Cấu hình (ưu tiên đọc từ biến môi trường trên Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8986756914:AAG2dj8r9RuT234iBNM98mUODSsiqY7Ti2w")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-5308046923")

# Binance Cấu hình
SYMBOL = os.getenv("SYMBOL", "FTTUSDT")
INTERVAL = os.getenv("INTERVAL", "5m")
MARKET_TYPE = "SPOT"

# Binance WebSocket Stream (Thời gian thực, không bị giới hạn Rate Limit HTTP 418/429)
BINANCE_WS_URL = os.getenv("BINANCE_WS_URL", f"wss://stream.binance.com:9443/ws/{SYMBOL.lower()}@kline_{INTERVAL}")
BINANCE_WS_FALLBACK_URLS = [
    f"wss://data-stream.binance.vision/ws/{SYMBOL.lower()}@kline_{INTERVAL}",
    f"wss://stream.binance.com:443/ws/{SYMBOL.lower()}@kline_{INTERVAL}"
]

# Binance REST API (Dự phòng)
BINANCE_API_URL = os.getenv("BINANCE_API_URL", "https://api.binance.com/api/v3/klines")
BINANCE_FALLBACK_URLS = [
    "https://api1.binance.com/api/v3/klines",
    "https://api2.binance.com/api/v3/klines",
    "https://api3.binance.com/api/v3/klines",
    "https://data-api.binance.vision/api/v3/klines",
]

# Cấu hình Proxy (nếu cần vượt qua giới hạn IP)
PROXY = os.getenv("HTTPS_PROXY", os.getenv("HTTP_PROXY", "")).strip()

# Điều kiện kích hoạt cảnh báo
PRICE_CHANGE_THRESHOLD = float(os.getenv("PRICE_CHANGE_THRESHOLD", 3.0))       # % tăng tối thiểu
VOLUME_THRESHOLD = float(os.getenv("VOLUME_THRESHOLD", 200000.0))             # Khối lượng FTT tối thiểu

# Tần suất kiểm tra (giây)
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", 5))

# Cấu hình Web Server cho Render (Keep-Alive & Health Check)
PORT = int(os.getenv("PORT", 10000))

# Tùy chọn gửi tin nhắn khi bot khởi động
SEND_STARTUP_NOTIFICATION = os.getenv("SEND_STARTUP_NOTIFICATION", "True").lower() in ("true", "1", "yes")
