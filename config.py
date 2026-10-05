# -*- coding: utf-8 -*-
"""
Cấu hình cho Bot quét nến M5 FTTUSDT Binance Spot
Phiên bản: 1.1.0 (Hỗ trợ Render.com & Chạy 24/7)
"""

import os

# Phiên bản phần mềm
__version__ = "1.1.0"

# Telegram Bot Cấu hình (ưu tiên đọc từ biến môi trường trên Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8986756914:AAG2dj8r9RuT234iBNM98mUODSsiqY7Ti2w")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-5308046923")

# Binance Cấu hình
SYMBOL = os.getenv("SYMBOL", "FTTUSDT")
INTERVAL = os.getenv("INTERVAL", "5m")
MARKET_TYPE = "SPOT"
BINANCE_API_URL = "https://api.binance.com/api/v3/klines"

# Điều kiện kích hoạt cảnh báo
PRICE_CHANGE_THRESHOLD = float(os.getenv("PRICE_CHANGE_THRESHOLD", 3.0))       # % tăng tối thiểu
VOLUME_THRESHOLD = float(os.getenv("VOLUME_THRESHOLD", 200000.0))             # Khối lượng FTT tối thiểu

# Tần suất kiểm tra (giây)
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", 5))

# Cấu hình Web Server cho Render (Keep-Alive & Health Check)
PORT = int(os.getenv("PORT", 10000))

# Tùy chọn gửi tin nhắn khi bot khởi động
SEND_STARTUP_NOTIFICATION = os.getenv("SEND_STARTUP_NOTIFICATION", "True").lower() in ("true", "1", "yes")
