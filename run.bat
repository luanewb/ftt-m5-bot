@echo off
chcp 65001 > nul
title Bot Quét Nến M5 FTTUSDT - Binance Spot
echo ========================================================
echo   KHỞI ĐỘNG BOT QUÉT NẾN M5 FTTUSDT (BINANCE SPOT)
echo ========================================================
python -m pip install -r requirements.txt > nul 2>&1
python main.py
pause
