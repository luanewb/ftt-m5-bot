# Bot Quét Nến M5 FTTUSDT (Binance Spot) - v1.1.3

Bot tự động giám sát cặp **FTTUSDT** trên thị trường **Binance Spot** ở khung thời gian **M5 (5 phút)** qua kết nối trực tiếp **Binance WebSocket Stream** thời gian thực (Zero Rate-Limit, chống lỗi cấm IP HTTP 418). Khi một cây nến M5 vừa kết thúc (đóng nến) thỏa mãn cả 2 điều kiện:
1. **Giá tăng:** $\ge +3.0\%$ (tính từ giá Mở cửa đến giá Đóng cửa của cây nến).
2. **Khối lượng giao dịch:** $\ge 200,000\text{ FTT}$ (Base asset volume).

Bot sẽ ngay lập tức gửi cảnh báo chi tiết về nhóm Telegram qua Telegram Bot API.

---

## 📁 Cấu Trúc Mã Nguồn

| File | Mô tả |
| :--- | :--- |
| [config.py](file:///d:/app/FTT/config.py) | Quản lý cấu hình, biến môi trường (`os.getenv`), URL WebSocket Stream và phiên bản bot (`v1.1.3`). |
| [web_server.py](file:///d:/app/FTT/web_server.py) | Web Server HTTP siêu nhẹ hỗ trợ HEAD/GET phục vụ Health Check & UptimeRobot Keep-Alive 24/7. |
| [telegram_notifier.py](file:///d:/app/FTT/telegram_notifier.py) | Xử lý định dạng HTML và gửi thông báo cảnh báo nến / khởi động tới Telegram. |
| [binance_scanner.py](file:///d:/app/FTT/binance_scanner.py) | Kết nối thời gian thực Binance WebSocket Stream, phát hiện nến đóng và kiểm tra điều kiện kích hoạt. |
| [main.py](file:///d:/app/FTT/main.py) | Vòng lặp chính xử lý luồng WebSocket thời gian thực, tích hợp Web Server, ghi log nến và nhịp tim. |
| [render.yaml](file:///d:/app/FTT/render.yaml) & [Procfile](file:///d:/app/FTT/Procfile) | File cấu hình tự động triển khai trên Render.com Web Service (Region: Singapore). |
| [run.bat](file:///d:/app/FTT/run.bat) | File thực thi nhanh 1-click trên hệ điều hành Windows. |
| [requirements.txt](file:///d:/app/FTT/requirements.txt) | Danh sách thư viện Python cần thiết (`requests`, `websockets`). |

---

## ☁️ Hướng Dẫn Triển Khai Lên Render.com Chạy 24/7 (Miễn Phí)

> ⚠️ **LƯU Ý CỰC KỲ QUAN TRỌNG VỀ REGION:**
> Binance **chặn toàn bộ IP đến từ Hoa Kỳ** (gây lỗi `HTTP 451 - Service unavailable from a restricted location`).
> Do đó, bắt buộc phải chọn **Region: Singapore** (hoặc Frankfurt), **tuyệt đối KHÔNG chọn Oregon hay Ohio (Mỹ)**!

### Cách 1: Triển khai tự động qua Blueprint (Khuyên dùng)
1. Đăng nhập vào [Render.com](https://dashboard.render.com/).
2. Nhấn **New +** ➔ Chọn **Blueprint**.
3. Chọn repo `luanewb/ftt-m5-bot`. Render sẽ tự động đọc file `render.yaml` (đã cấu hình sẵn `region: singapore`) và khởi chạy hoàn toàn tự động.

### Cách 2: Tạo Web Service thủ công
1. Đăng nhập vào [Render.com](https://dashboard.render.com/).
2. Nhấn nút **New +** ở góc trên bên phải ➔ Chọn **Web Service**.
3. Chọn kết nối với kho lưu trữ GitHub của bạn: `luanewb/ftt-m5-bot`.
4. Điền các thông tin:
   * **Name:** `ftt-m5-bot` (hoặc tên bạn thích).
   * **Region:** **Singapore** *(Bắt buộc chọn Singapore để tránh lỗi HTTP 451)*.
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
