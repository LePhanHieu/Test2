## 1. Cài đặt – chạy tại thư mục gốc sau giải nén

Khuyến nghị Python 3.11 hoặc 3.12. Môi trường kiểm thử thực tế: Python 3.12.14.

Windows CMD:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements-test.txt
python -m pip install -r requirements.txt
python -m pip install -r requirements-database.txt
copy .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Dán chuỗi vừa sinh vào `SECRET_KEY` trong `.env`. Cấu hình cho database mới:

```dotenv
SECRET_KEY=<chuỗi ngẫu nhiên vừa sinh>
ALLOW_DEMO_SEED=false
SESSION_COOKIE_SECURE=false
```

Linux/macOS: thay lệnh activate bằng `source .venv/bin/activate` và copy bằng `cp .env.example .env`.

## 2. Kiểm tra

```bat
python -m flask --app skin_cancer.webapp.database_app db upgrade
python -m flask --app skin_cancer.webapp.database_app db current
python -m flask --app skin_cancer.webapp.database_app db check
python -m flask --app skin_cancer.webapp.database_app setup-initial
python -m pytest -q
```

Database mặc định mới: `instance/dermascan_live.db`, tách biệt với database demo cũ `instance/dermascan.db` (không bị xóa hoặc chỉnh sửa). Có thể đặt `DATABASE_URL` thành URL SQLite tuyệt đối trong `.env`, ví dụ `sqlite:////absolute/path/to/instance/dermascan_live.db`. Thư mục cha của đường dẫn tùy chọn phải tồn tại. Nếu `.env` đang trỏ tới database cũ thì cần đổi lại trước khi chạy.

`run_app.bat` tự chạy `setup-initial --local-starter-accounts` và tạo ba tài khoản cố định (ADMIN `admin@dermascan.local`, DOCTOR `doctor@dermascan.local`, USER `patient@dermascan.local`) trên SQLite mới còn trống. Mật khẩu khởi tạo dùng chung `123456123456`, được lưu dưới dạng hash và **chỉ dành cho máy phát triển**. Lệnh `setup-initial` không có tùy chọn vẫn cho phép nhập tài khoản thủ công. Lần chạy lại không ghi đè tài khoản/banner đã tạo. Hai banner và logo vẫn dùng ảnh có sẵn trong `skin_cancer/webapp/assets/`.

`python -m pytest -q` chạy bộ test an toàn trong `tests/`, luôn dùng SQLite tạm. Script `test_all_features_e2e.py` cũ cần cả stack AI/Redis và có ghi dữ liệu, vì vậy chỉ chạy thủ công khi đã chỉ định database kiểm thử riêng.

### OTP email dành riêng cho DOCTOR đã được duyệt

- DOCTOR mới đăng ký chỉ cần ADMIN phê duyệt **một lần**. Trước khi duyệt, tài khoản bị khóa. Sau khi duyệt, mỗi lần đăng nhập phải nhập email, mật khẩu và OTP 6 chữ số được gửi qua SMTP đến email đăng ký.
- OTP hết hạn sau **5 phút**, dùng một lần. Có thể gửi lại OTP; mỗi mã mới làm vô hiệu mã trước. Trong lần xác minh OTP đầu tiên, `email_verified` được đánh dấu true. Những lần đăng nhập sau vẫn bắt buộc OTP.
- Riêng `doctor@dermascan.local` là tài khoản phát triển mẫu, được miễn OTP email. ADMIN/USER giữ cách đăng nhập cũ; 2FA riêng của ADMIN vẫn lấy OTP trong Terminal.
- SMTP được lấy từ `.env`: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`/`MAIL_USE_SSL`, `MAIL_USERNAME`, `MAIL_PASSWORD` (Gmail App Password nếu dùng Gmail), `MAIL_DEFAULT_SENDER`. Không ghi mật khẩu SMTP vào Git. Nếu gửi mail thất bại, DOCTOR **không được đăng nhập** và API trả 503.
- Các ca kiểm thử dùng giả lập SMTP; chưa xác nhận gửi được tới hộp thư thật của bạn. Hãy kiểm tra bằng email DOCTOR riêng trước khi dùng thực tế.

**Giới hạn hiện tại:** một số luồng xác minh email khác (USER) và 2FA ADMIN vẫn in mã trong Terminal. Database, ảnh bệnh nhân và báo cáo cũ còn được theo dõi trong lịch sử Git; không dùng dữ liệu bệnh nhân nhận dạng thật trên môi trường công khai cho tới khi xử lý bảo mật/lưu trữ.

Sau này có thay đổi models:

```bat
python -m flask --app skin_cancer.webapp.database_app db migrate -m "Mo ta thay doi schema"
python -m flask --app skin_cancer.webapp.database_app db upgrade
```

## 4. Tài khoản khởi tạo

Ba tài khoản phát triển mẫu được tạo tự động bằng `run_app.bat` như mô tả ở mục 2.
Thay ngay mật khẩu mẫu trước khi triển khai hoặc sử dụng cho dữ liệu nhạy cảm.
