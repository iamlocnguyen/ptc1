# FastAPI Backend Template (PTC1)

Mẫu template backend chuẩn sử dụng **FastAPI**, **SQLAlchemy 2.0 ORM**, **Pydantic v2**, và **Pytest**.

---

## 🚀 Tính năng nổi bật
- **FastAPI hiện đại**: Sử dụng `lifespan` context manager, cấu trúc modular rõ ràng (`core`, `db`, `models`, `schemas`, `services`, `api`).
- **Tích hợp Swagger UI & ReDoc**:
  - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
  - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Cơ sở dữ liệu với ORM**: SQLAlchemy 2.0 (`Mapped[]`, `mapped_column`) kết nối mặc định với **SQLite** (`app.db`). Có thể chuyển sang PostgreSQL/MySQL bất cứ lúc nào qua biến môi trường `DATABASE_URL`.
- **Cấu hình tập trung**: Quản lý bằng `pydantic-settings`, hỗ trợ nạp tự động từ file `.env`.
- **Kiểm thử độc lập (Testing)**: Bộ test sử dụng `pytest` + `httpx` (`TestClient`), tự động sử dụng SQLite in-memory (`sqlite:///:memory:`) chạy cực nhanh và không làm bẩn database thật.

---

## 📁 Cấu trúc thư mục

```
server/
├── app/
│   ├── main.py                  # Entrypoint: cấu hình FastAPI, CORS, Swagger tags, lifespan
│   ├── core/
│   │   ├── config.py            # Quản lý cài đặt môi trường (Settings)
│   │   └── security.py          # Băm và xác thực mật khẩu (PBKDF2-HMAC-SHA256)
│   ├── db/
│   │   ├── base.py              # DeclarativeBase SQLAlchemy
│   │   └── session.py           # Engine & SessionLocal, get_db dependency
│   ├── models/
│   │   └── user.py              # Model User bảng database (SQLAlchemy)
│   ├── schemas/
│   │   └── user.py              # Pydantic schemas (UserRegister, UserLogin, UserResponse...)
│   ├── services/
│   │   └── user_service.py      # Tầng xử lý nghiệp vụ & truy vấn DB người dùng
│   └── api/
│       └── v1/
│           ├── router.py        # Router tổng hợp v1
│           └── endpoints/
│               └── auth.py      # POST /api/v1/auth/register, POST /api/v1/auth/login
├── tests/
│   ├── conftest.py              # Fixture TestClient + in-memory SQLite DB
│   ├── test_auth.py             # Unit test cho đăng ký & đăng nhập
│   ├── test_main.py             # Unit test cho root endpoint GET /
│   └── test_swagger.py          # Unit test cho Swagger UI & OpenAPI schema
├── requirements.txt             # Danh sách dependencies
└── README.md                    # Tài liệu hướng dẫn
```

---

## 🛠️ Hướng dẫn cài đặt & chạy

### 1. Khởi tạo môi trường ảo Python
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Kích hoạt môi trường (Linux/macOS)
source .venv/bin/activate
```

### 2. Cài đặt thư viện
```bash
pip install -r server/requirements.txt
```

### 3. Chạy Server ở chế độ Development
Từ thư mục gốc dự án:
```bash
uvicorn server.app.main:app --reload --port 8000
```
- Mở trình duyệt truy cập: [http://localhost:8000](http://localhost:8000)
- Trải nghiệm Swagger UI tại: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Chạy kiểm thử (Pytest)
```bash
pytest server/tests -v
```
Toàn bộ test case sẽ được thực thi trên cơ sở dữ liệu in-memory biệt lập.
