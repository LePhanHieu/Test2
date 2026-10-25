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

Lệnh `setup-initial` sẽ yêu cầu nhập họ tên, email và mật khẩu riêng cho một ADMIN, một DOCTOR và một USER. Mật khẩu không hiển thị khi gõ, được lưu dưới dạng hash. Lệnh chỉ khởi tạo trên database trống; lần chạy lại không tạo thêm tài khoản hoặc banner. Hai banner mặc định dùng ảnh có sẵn trong `skin_cancer/webapp/assets/`, logo được giữ nguyên.

`python -m pytest -q` chạy bộ test an toàn trong `tests/`, luôn dùng SQLite tạm. Script `test_all_features_e2e.py` cũ cần cả stack AI/Redis và có ghi dữ liệu, vì vậy chỉ chạy thủ công khi đã chỉ định database kiểm thử riêng.

**Giới hạn hiện tại:** mã xác minh email/OTP vẫn hiển thị trong Terminal; chưa triển khai gửi email tự động. Chưa phù hợp để xử lý thông tin nhận dạng bệnh nhân thật trên môi trường công khai, và các tệp dữ liệu cũ vẫn được theo dõi trong lịch sử Git. Đây là hai công việc sẽ xử lý sau theo yêu cầu.

Sau này có thay đổi models:

```bat
python -m flask --app skin_cancer.webapp.database_app db migrate -m "Mo ta thay doi schema"
python -m flask --app skin_cancer.webapp.database_app db upgrade
```

## 4. Tài khoản khởi tạo

Không có email/mật khẩu mặc định. Chủ dự án tự nhập thông tin cho ADMIN,
DOCTOR và USER khi `setup-initial` chạy lần đầu. Tài khoản thường đăng ký từ
web vẫn áp dụng quy trình xác thực hiện tại qua Terminal cho tới khi nâng cấp.
