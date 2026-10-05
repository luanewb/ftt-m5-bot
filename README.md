# Bot Quét Nến M5 FTTUSDT (Binance Spot) - v1.1.0

Bot tự động giám sát cặp **FTTUSDT** trên thị trường **Binance Spot** ở khung thời gian **M5 (5 phút)**. Khi một cây nến M5 vừa kết thúc (đóng nến) thỏa mãn cả 2 điều kiện:
1. **Giá tăng:** $\ge +3.0\%$ (tính từ giá Mở cửa đến giá Đóng cửa của cây nến).
2. **Khối lượng giao dịch:** $\ge 200,000\text{ FTT}$ (Base asset volume).

Bot sẽ ngay lập tức gửi cảnh báo chi tiết về nhóm Telegram qua Telegram Bot API.

---

## 📁 Cấu Trúc Mã Nguồn

| File | Mô tả |
| :--- | :--- |
| [config.py](file:///d:/app/FTT/config.py) | Quản lý cấu hình, biến môi trường (`os.getenv`), và phiên bản bot (`v1.1.0`). |
| [web_server.py](file:///d:/app/FTT/web_server.py) | Web Server HTTP siêu nhẹ phục vụ Health Check & Uptime Monitor cho Render.com. |
| [telegram_notifier.py](file:///d:/app/FTT/telegram_notifier.py) | Xử lý định dạng HTML và gửi thông báo cảnh báo nến / khởi động tới Telegram. |
| [binance_scanner.py](file:///d:/app/FTT/binance_scanner.py) | Lấy dữ liệu nến từ Binance Spot API, phân tích nến đóng và kiểm tra điều kiện kích hoạt. |
| [main.py](file:///d:/app/FTT/main.py) | Vòng lặp chính quét liên tục, tích hợp Web Server, ghi log nến và nhịp tim. |
| [render.yaml](file:///d:/app/FTT/render.yaml) & [Procfile](file:///d:/app/FTT/Procfile) | File cấu hình tự động triển khai trên Render.com Web Service. |
| [run.bat](file:///d:/app/FTT/run.bat) | File thực thi nhanh 1-click trên hệ điều hành Windows. |
| [requirements.txt](file:///d:/app/FTT/requirements.txt) | Danh sách thư viện Python cần thiết (`requests`). |

---

## ☁️ Hướng Dẫn Triển Khai Lên Render.com Chạy 24/7 (Miễn Phí)

### Bước 1: Tạo Web Service trên Render
1. Đăng nhập vào [Render.com](https://dashboard.render.com/).
2. Nhấn nút **New +** ở góc trên bên phải ➔ Chọn **Web Service**.
3. Chọn kết nối với kho lưu trữ GitHub của bạn: `luanewb/ftt-m5-bot`.
4. Điền các thông tin:
   * **Name:** `ftt-m5-bot` (hoặc tên bạn thích).
   * **Region:** Singapore (hoặc Oregon/Frankfurt).
   * **Branch:** `main` (hoặc `master`).
   * **Runtime:** `Python 3`.
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `python main.py`
   * **Instance Type:** Chọn **Free**.
5. Nhấn **Deploy Web Service**.

### Bước 2: Thiết lập Giữ Bot Chạy 24/7 (Chống Sleep 15 phút)
Gói miễn phí của Render sẽ tạm dừng dịch vụ nếu không có ai truy cập web sau 15 phút. Để bot chạy 24/7 liên tục:
1. Đăng ký tài khoản miễn phí tại [UptimeRobot.com](https://uptimerobot.com/) hoặc [Cron-job.org](https://cron-job.org/).
2. Nhấn **Add New Monitor**:
   * **Monitor Type:** `HTTP(s)`
   * **Friendly Name:** `FTT Bot Render`
   * **URL (or IP):** Điền đường link web service Render của bạn (ví dụ: `https://ftt-m5-bot.onrender.com`).
   * **Monitoring Interval:** Chọn `5 minutes` (mỗi 5 phút).
3. Nhấn **Create Monitor**. Từ giờ UptimeRobot sẽ tự động gửi yêu cầu kiểm tra mỗi 5 phút, giữ cho Bot của bạn hoạt động liên tục 24/7/365 hoàn toàn miễn phí!

---

## 🖥 Chạy Tại Máy Cục Bộ (Local)

* **Cách 1:** Nhấp đúp chuột vào file [run.bat](file:///d:/app/FTT/run.bat).
* **Cách 2:** Chạy lệnh:
  ```bash
  python main.py
  ```
* **Kiểm tra cảnh báo mẫu Telegram:**
  ```bash
  python main.py --test-alert
  ```
