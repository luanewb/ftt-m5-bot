# -*- coding: utf-8 -*-
"""
Web Server siêu nhẹ phục vụ Health Check & Keep-Alive 24/7 cho Render.com
Phiên bản: 1.1.0
"""

import json
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import config

logger = logging.getLogger(__name__)

# Trạng thái toàn cục để hiển thị trên web
bot_status = {
    "start_time": datetime.now(),
    "last_check_time": None,
    "last_closed_candle": None,
    "current_price": 0.0,
    "status": "Starting"
}

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        uptime = str(datetime.now() - bot_status["start_time"]).split(".")[0]
        
        # Nếu yêu cầu JSON (/status hoặc /api)
        if self.path in ("/status", "/json"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            data = {
                "bot": "FTTUSDT M5 Scanner",
                "version": config.__version__,
                "status": bot_status["status"],
                "uptime": uptime,
                "symbol": config.SYMBOL,
                "interval": config.INTERVAL,
                "current_price": bot_status["current_price"],
                "last_closed_candle": bot_status["last_closed_candle"]
            }
            self.wfile.write(json.dumps(data, default=str).encode("utf-8"))
            return

        # Mặc định trả về trang HTML trạng thái
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        last_candle = bot_status.get("last_closed_candle")
        last_candle_html = "Chưa có nến mới đóng"
        if last_candle:
            last_candle_html = (
                f"Thời gian: {last_candle.get('time', 'N/A')}<br>"
                f"Giá Đóng: {last_candle.get('close', 'N/A')}<br>"
                f"Biến động: {last_candle.get('change', 'N/A')}<br>"
                f"Khối lượng: {last_candle.get('volume', 'N/A')}"
            )

        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FTTUSDT M5 Bot - Render Health Check</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #0b0e14;
            color: #e6edf3;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }}
        .card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 30px;
            max-width: 520px;
            width: 90%;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }}
        .badge {{
            display: inline-block;
            background: #238636;
            color: #fff;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        h1 {{
            font-size: 22px;
            margin: 0 0 10px 0;
            color: #58a6ff;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #21262d;
            font-size: 14px;
        }}
        .label {{ color: #8b949e; }}
        .val {{ font-weight: 600; color: #f0f6fc; }}
        .candle-box {{
            background: #0d1117;
            border-radius: 8px;
            padding: 12px;
            margin-top: 15px;
            font-size: 13px;
            border: 1px solid #30363d;
        }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">● ONLINE 24/7</span>
        <h1>🤖 Bot Quét Nến M5 FTTUSDT</h1>
        <p style="color: #8b949e; font-size: 13px; margin-top: 0;">Phiên bản: v{config.__version__} | Binance Spot</p>
        
        <div class="info-row">
            <span class="label">Trạng thái:</span>
            <span class="val" style="color: #3fb950;">{bot_status['status']}</span>
        </div>
        <div class="info-row">
            <span class="label">Thời gian hoạt động (Uptime):</span>
            <span class="val">{uptime}</span>
        </div>
        <div class="info-row">
            <span class="label">Giá hiện tại ({config.SYMBOL}):</span>
            <span class="val">{bot_status['current_price']:.4f} USDT</span>
        </div>
        <div class="info-row">
            <span class="label">Tiêu chí cảnh báo:</span>
            <span class="val">Tăng ≥ {config.PRICE_CHANGE_THRESHOLD}% &amp; Vol ≥ {config.VOLUME_THRESHOLD:,.0f} FTT</span>
        </div>
        
        <div class="candle-box">
            <strong>📊 Nến M5 vừa đóng gần nhất:</strong><br>
            <div style="margin-top: 6px; line-height: 1.6;">{last_candle_html}</div>
        </div>
    </div>
</body>
</html>"""
        self.wfile.write(html_content.encode("utf-8"))

    def log_message(self, format, *args):
        # Tắt bớt log HTTP định kỳ để không làm tràn console
        return

def start_web_server(port: int = None):
    """
    Khởi động web server trên luồng phụ (background thread).
    """
    if port is None:
        port = config.PORT
    
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    logger.info(f"🌐 Web Server (Health Check) đang lắng nghe tại cổng {port}...")
    
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    return httpd
