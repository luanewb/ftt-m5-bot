# -*- coding: utf-8 -*-
"""
Module quét và phân tích nến M5 từ Binance Spot qua WebSocket Stream thời gian thực
Phiên bản: 1.1.3
"""

import time
import json
import logging
import asyncio
import websockets
from datetime import datetime
from typing import Dict, Optional, Callable
import config

logger = logging.getLogger(__name__)

class BinanceScanner:
    def __init__(
        self,
        on_candle_closed: Optional[Callable[[Dict, bool], None]] = None,
        on_price_update: Optional[Callable[[float], None]] = None
    ):
        self.symbol = config.SYMBOL
        self.interval = config.INTERVAL
        self.price_threshold = config.PRICE_CHANGE_THRESHOLD
        self.volume_threshold = config.VOLUME_THRESHOLD
        
        # Callbacks
        self.on_candle_closed = on_candle_closed
        self.on_price_update = on_price_update
        
        # Danh sách WebSocket URLs (chính và fallback)
        self.ws_urls = [config.BINANCE_WS_URL]
        for url in getattr(config, "BINANCE_WS_FALLBACK_URLS", []):
            if url not in self.ws_urls:
                self.ws_urls.append(url)
                
        # Bộ đệm lưu open_time (ms) các cây nến đã xử lý
        self.processed_candles = set()
        self.running = True
        self.current_price = 0.0
        self.is_connected = False

    def parse_ws_kline(self, k: dict) -> Dict:
        """
        Chuyển đổi dữ liệu kline từ Binance WebSocket thành dictionary.
        """
        open_time_ms = int(k["t"])
        close_time_ms = int(k["T"])
        open_price = float(k["o"])
        high_price = float(k["h"])
        low_price = float(k["l"])
        close_price = float(k["c"])
        volume = float(k["v"])
        quote_volume = float(k["q"])
        trades_count = int(k["n"])
        is_closed = bool(k.get("x", False))

        if open_price > 0:
            price_change_pct = ((close_price - open_price) / open_price) * 100.0
        else:
            price_change_pct = 0.0

        return {
            "open_time_ms": open_time_ms,
            "close_time_ms": close_time_ms,
            "open_time": datetime.fromtimestamp(open_time_ms / 1000.0),
            "close_time": datetime.fromtimestamp(close_time_ms / 1000.0),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
            "quote_volume": quote_volume,
            "trades_count": trades_count,
            "price_change_pct": price_change_pct,
            "is_closed": is_closed
        }

    async def _heartbeat_loop(self):
        """In log nhịp tim định kỳ mỗi 60 giây để xác nhận kết nối vẫn hoạt động tốt."""
        while self.running:
            await asyncio.sleep(60)
            status_text = "🟢 Đang kết nối" if self.is_connected else "🟡 Đang thử lại"
            price_text = f"{self.current_price:.4f}" if self.current_price > 0 else "Đang cập nhật"
            logger.info(f"💓 [WebSocket Stream] {self.symbol} Giá: {price_text} | Trạng thái: {status_text} | Đang theo dõi nến {self.interval}...")

    async def start_stream(self):
        """
        Vòng lặp chính kết nối tới Binance WebSocket Stream và tự động reconnect.
        """
        logger.info(f"Đang chuẩn bị kết nối tới Binance WebSocket Stream cho {self.symbol} ({self.interval})...")
        
        # Khởi động nhịp tim định kỳ
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        url_index = 0
        backoff_seconds = 2

        try:
            while self.running:
                url = self.ws_urls[url_index % len(self.ws_urls)]
                logger.info(f"🔌 Đang kết nối tới Binance WebSocket Stream: {url} ...")
                try:
                    # websockets tự động xử lý ping/pong với ping_interval=20, ping_timeout=15
                    async with websockets.connect(
                        url,
                        ping_interval=20,
                        ping_timeout=15,
                        close_timeout=10,
                        user_agent_header=f"FTT-M5-Scanner/{config.__version__}"
                    ) as ws:
                        self.is_connected = True
                        backoff_seconds = 2  # Reset backoff khi kết nối thành công
                        logger.info(f"✅ Đã kết nối thành công tới Binance WebSocket Stream ({url})!")

                        async for message in ws:
                            if not self.running:
                                break
                            try:
                                data = json.loads(message)
                                kline_data = data.get("k")
                                if not kline_data:
                                    continue

                                candle = self.parse_ws_kline(kline_data)
                                self.current_price = candle["close"]

                                # Gọi callback cập nhật giá tức thì
                                if self.on_price_update:
                                    self.on_price_update(candle["close"])

                                # Khi cây nến đóng hoàn toàn (k["x"] == True)
                                if candle["is_closed"]:
                                    candle_id = candle["open_time_ms"]
                                    if candle_id not in self.processed_candles:
                                        self.processed_candles.add(candle_id)
                                        if len(self.processed_candles) > 1000:
                                            self.processed_candles = set(sorted(list(self.processed_candles))[-500:])

                                        # Kiểm tra điều kiện nến tăng và khối lượng
                                        is_qualified = (
                                            candle["price_change_pct"] >= self.price_threshold and
                                            candle["volume"] >= self.volume_threshold
                                        )

                                        if self.on_candle_closed:
                                            self.on_candle_closed(candle, is_qualified)

                            except json.JSONDecodeError:
                                continue
                            except Exception as msg_err:
                                logger.error(f"Lỗi khi xử lý gói tin WebSocket: {msg_err}", exc_info=True)

                except (websockets.exceptions.ConnectionClosed, websockets.exceptions.WebSocketException) as ws_err:
                    self.is_connected = False
                    logger.warning(f"⚠️ Mất kết nối WebSocket ({ws_err}). Tự động thử lại sau {backoff_seconds}s...")
                except Exception as e:
                    self.is_connected = False
                    logger.error(f"❌ Lỗi kết nối WebSocket: {e}. Đổi URL dự phòng và thử lại sau {backoff_seconds}s...")
                    url_index += 1

                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 1.5, 30)

        finally:
            heartbeat_task.cancel()
