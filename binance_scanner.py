# -*- coding: utf-8 -*-
"""
Module quét và phân tích nến M5 từ Binance Spot API
Phiên bản: 1.1.1 (Hỗ trợ Fallback Endpoints, HTTP 451 Warning, Proxy)
"""

import time
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import config

logger = logging.getLogger(__name__)

class BinanceScanner:
    def __init__(self):
        self.symbol = config.SYMBOL
        self.interval = config.INTERVAL
        self.api_url = config.BINANCE_API_URL
        self.price_threshold = config.PRICE_CHANGE_THRESHOLD
        self.volume_threshold = config.VOLUME_THRESHOLD
        
        # Danh sách endpoint bao gồm URL chính và các fallback URLs
        self.endpoints = [self.api_url]
        for url in getattr(config, "BINANCE_FALLBACK_URLS", []):
            if url not in self.endpoints:
                self.endpoints.append(url)
        self.current_endpoint_idx = 0

        # Tập hợp lưu open_time (ms) của các cây nến đã được xử lý để tránh trùng lặp
        self.processed_candles = set()
        
        # Session requests tái sử dụng kết nối
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"FTT-M5-Scanner/{config.__version__}"
        })
        if getattr(config, "PROXY", None):
            self.session.proxies = {
                "http": config.PROXY,
                "https": config.PROXY
            }
            logger.info(f"Đã kích hoạt Proxy cho kết nối Binance: {config.PROXY}")

    def fetch_klines(self, limit: int = 5) -> Optional[List[list]]:
        """
        Lấy danh sách các cây nến gần nhất từ Binance Spot API.
        Tự động luân chuyển fallback endpoint nếu gặp lỗi.
        """
        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "limit": limit
        }
        num_endpoints = len(self.endpoints)
        for attempt in range(num_endpoints):
            idx = (self.current_endpoint_idx + attempt) % num_endpoints
            url = self.endpoints[idx]
            try:
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    self.current_endpoint_idx = idx
                    return response.json()
                elif response.status_code == 451:
                    logger.error(
                        f"[LỖI ĐỊA LÝ HTTP 451] IP máy chủ ({url}) bị Binance chặn truy cập vì nằm trong khu vực hạn chế (Mỹ/Oregon). "
                        f"Khắc phục: Đổi Region sang 'singapore' trong render.yaml hoặc thiết lập PROXY."
                    )
                else:
                    logger.error(f"Lỗi API Binance ({url}): HTTP {response.status_code} - {response.text}")
            except requests.RequestException as e:
                logger.error(f"Lỗi kết nối API Binance ({url}): {e}")

        return None

    def parse_kline(self, kline_raw: list) -> Dict:
        """
        Chuyển đổi dữ liệu nến dạng mảng của Binance thành dictionary dễ đọc.
        Kline structure:
        0: Open time (ms)
        1: Open price
        2: High price
        3: Low price
        4: Close price
        5: Volume (Base asset - FTT)
        6: Close time (ms)
        7: Quote asset volume (USDT)
        8: Number of trades
        9: Taker buy base asset volume
        10: Taker buy quote asset volume
        11: Ignore
        """
        open_time_ms = int(kline_raw[0])
        close_time_ms = int(kline_raw[6])
        open_price = float(kline_raw[1])
        high_price = float(kline_raw[2])
        low_price = float(kline_raw[3])
        close_price = float(kline_raw[4])
        volume = float(kline_raw[5])
        quote_volume = float(kline_raw[7])
        trades_count = int(kline_raw[8])

        # Tính % thay đổi giá của cây nến: ((Close - Open) / Open) * 100
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
            "price_change_pct": price_change_pct
        }

    def check_new_closed_candle(self) -> Tuple[Optional[Dict], bool]:
        """
        Kiểm tra cây nến vừa đóng nến gần nhất.
        Trả về:
            (candle_dict, is_qualified)
            - candle_dict: thông tin nến vừa đóng nếu là nến mới chưa xử lý, None nếu không có nến mới.
            - is_qualified: True nếu nến tăng >= 3% và volume >= 200,000 FTT.
        """
        klines = self.fetch_klines(limit=5)
        if not klines or len(klines) < 2:
            return None, False

        current_time_ms = int(time.time() * 1000)

        # Cây nến áp chót (klines[-2]) chắc chắn là nến đã đóng hoàn toàn
        # Nhưng để an toàn ta duyệt tất cả các nến có close_time_ms < current_time_ms
        closed_candidate = None
        for raw in reversed(klines):
            close_time_ms = int(raw[6])
            if close_time_ms < current_time_ms:
                closed_candidate = raw
                break

        if not closed_candidate:
            return None, False

        candle = self.parse_kline(closed_candidate)
        candle_id = candle["open_time_ms"]

        # Nếu nến này đã được xử lý trước đó, bỏ qua
        if candle_id in self.processed_candles:
            return None, False

        # Đánh dấu đã xử lý
        self.processed_candles.add(candle_id)
        
        # Giữ kích thước cache vừa phải (1000 nến gần nhất)
        if len(self.processed_candles) > 1000:
            self.processed_candles = set(sorted(list(self.processed_candles))[-500:])

        # Kiểm tra điều kiện: Nến tăng >= 3% VÀ khối lượng >= 200,000 FTT
        is_qualified = (
            candle["price_change_pct"] >= self.price_threshold and 
            candle["volume"] >= self.volume_threshold
        )

        return candle, is_qualified

    def mark_existing_candles_as_processed(self):
        """
        Đánh dấu các nến trong quá khứ đã được xử lý lúc khởi động
        để không gửi lại cảnh báo của các nến cũ trước thời điểm chạy bot.
        """
        klines = self.fetch_klines(limit=5)
        if klines:
            current_time_ms = int(time.time() * 1000)
            for raw in klines:
                close_time_ms = int(raw[6])
                if close_time_ms < current_time_ms:
                    self.processed_candles.add(int(raw[0]))
            logger.info(f"Đã khởi tạo bộ đệm nến. Bỏ qua {len(self.processed_candles)} nến cũ trước thời điểm chạy.")
