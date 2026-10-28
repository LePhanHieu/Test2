# DermaScan AI — Task 0: Baseline và cách ly kiểm thử

**Nhánh:** `chore/test-isolation-audit`

**Commit nguồn:** `aa48e60797b6aa19004e9b1ddb4fb26b9cbdcbd8`
**Phạm vi:** Task 0; không đổi source sản phẩm, schema, checkpoint, dữ liệu, API hoặc UI.

## 1. Baseline

| Kiểm tra | Kết quả |
|---|---|
| `pytest tests/ -q -p no:cacheprovider` | 69 passed (26,16 giây trong worktree) |
| Coverage | 46% trên 4.114 statements (lượt khảo sát trước Task 0) |
| Ruff lint | 114 findings (khảo sát trước Task 0) |
| Ruff format | 44 file chưa thống nhất (khảo sát trước Task 0) |
| Bandit | 16 findings: 12 low, 4 medium, 0 high (khảo sát trước Task 0) |

**Sau khi thêm fixture Task 0:** `73 passed in 28.44s`; coverage `47%` trên cùng 4.114 statements được tính. Mức tăng 1 điểm phần trăm phản ánh test mới chạm `result_cache.py` (từ 24% lên 48%), không phải hiệu quả kiểm thử AI thật.

Coverage không đại diện cho toàn bộ mô hình AI. Ruff/Bandit findings không mặc định là lỗi hoặc lỗ hổng. `pytest.ini` cố ý đặt `testpaths = tests`, không chạy script legacy `test_all_features_e2e.py` có thể ghi database thật.

## 2. Test isolation contract

- `tests/conftest.py::isolated_storage` là fixture **opt-in**: thiết lập SQLite database, cache, upload, report, Flask instance dưới `tmp_path`; reset bộ nhớ cache và vô hiệu kết nối Redis của cache module; vô hiệu API key OpenAI trong test.
- Dùng `isolated_storage["redirect_ai_worker_root"](worker_webapp)` **trước** khi thực thi `_run_analysis`, vì Grad-CAM trong `tasks.py` dựa trên `webapp.PROJECT_ROOT` chứ không phải Flask config.
- `tests/conftest.py::offline_runtime` chặn kết nối trực tiếp `socket.connect`/`socket.create_connection` và `mail.send`. Tests với dịch vụ ngoài cần bật đồng thời hai fixture và mock thêm các transport riêng theo từng SDK.
- Các fixture này không tự động tác động bộ test cũ. Chúng **không phải sandbox tuyệt đối**: subprocess hoặc thư viện network khác có thể cần guard bổ sung.
- Không import/chạy model AI thật trước khi mock checkpoint/worker và kiểm tra mọi output path. Không dùng ảnh/bệnh án thật và không chạy E2E legacy trên DB ứng dụng.

## 3. Kiểm chứng mới

`tests/test_isolated_runtime.py` kiểm tra: cache SQLite nằm trong `tmp_path`; Flask instance/database/upload/report nằm trong `tmp_path`; socket/email bị chặn; helper có thể chuyển Grad-CAM worker root vào `tmp_path`. Test Grad-CAM dùng object mô phỏng, **chưa chứng minh worker thật đã an toàn**.

## 4. Rủi ro chưa sửa trong Task 0

| Thành phần | Phát hiện | Xử lý sau |
|---|---|---|
| `services/result_cache.py` | Default cache ở `instance/cache.db` | Fixture patch trong test; sản phẩm giữ nguyên |
| `tasks.py` | Grad-CAM theo `webapp.PROJECT_ROOT` | Test AI phải redirect root; nghiên cứu injection sau |
| `app.py` | Import có thể tải PyTorch checkpoint, fallback daemon thread | Mock trước import, test recovery giai đoạn sau |
| `routes/cases.py` | Hai F821 (`today`, `current_app`) | Task 2 với regression tests |
| `routes/analysis_status.py` | COMPLETED + cache miss có thể trả PROCESSING | Test failure/recovery Task 4 |
| Tracked `instance/*.db`, `instance/uploads/*` | Có dữ liệu/runtime files trong Git | Audit privacy; không xóa hoặc rewrite history |

## 5. Lệnh chạy

```bash
python -m pytest tests/test_isolated_runtime.py -q -p no:cacheprovider
python -m pytest tests/ -q -p no:cacheprovider
python -m pytest tests/ --cov=skin_cancer.webapp --cov-report=term-missing:skip-covered
ruff check skin_cancer/webapp --no-cache --statistics
ruff format --check skin_cancer/webapp
bandit -r skin_cancer/webapp -q
```

## 6. Gate

Kiểm chứng đã chạy: `tests/test_isolated_runtime.py` 4 passed, toàn bộ suite 73 passed, Ruff `E4,E7,E9,F,I` trên hai file test mới đạt. Test mới được chạy RED trước khi triển khai fixture rồi GREEN sau đó. Worktree có thể sinh `.coverage` và thư mục chứng chỉ test không theo dõi bởi Git; không đưa chúng vào commit.

Sau Task 0, kiểm tra `git diff --check`, `git status --short` và báo cáo tất cả kết quả/giới hạn. **Không bắt đầu Task 1, xóa file, sửa source sản phẩm, merge hoặc push** khi chưa có chỉ đạo tiếp theo.
