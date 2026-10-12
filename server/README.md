# FastAPI Backend Template (PTC1)

Mẫu template backend chuẩn sử dụng **FastAPI**, **SQLAlchemy 2.0 ORM** (kết nối thuần **PostgreSQL 14** qua driver `psycopg`), **Pydantic v2**, và **Pytest**.

---

## 🚀 Tính năng nổi bật
- **FastAPI hiện đại**: Sử dụng `lifespan` context manager, cấu trúc modular rõ ràng (`core`, `db`, `models`, `schemas`, `services`, `api`).
- **Tích hợp Swagger UI & ReDoc**:
  - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
  - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Cơ sở dữ liệu thuần PostgreSQL**:
  - Kết nối trực tiếp PostgreSQL (cổng 5432) qua driver `psycopg` (Psycopg 3) với Connection Pool tự động.
  - Phân chia **mỗi vai trò tài khoản 1 bảng riêng biệt**: `users`, `sellers`, `admins` (khách vãng lai `guest` không cần lưu trữ thông tin).
  - Tự động tạo bảng và seed tài khoản Admin mặc định (`admin@example.com` / `admin123`) khi khởi động.
- **Cấu hình tập trung**: Quản lý bằng `pydantic-settings`, hỗ trợ nạp tự động từ file `.env`.
- **Kiểm thử độc lập trên PostgreSQL (Testing)**:
  - Bộ test sử dụng `pytest` kết nối trực tiếp database `ptc1_test_db` trên PostgreSQL thật.
  - Sử dụng cơ chế **Savepoint Rollback** (`join_transaction_mode="create_savepoint"`) giúp test chạy siêu tốc (~1s cho 14 test cases) và hoàn toàn không làm bẩn dữ liệu thật trong `ptc1_db`.

---

## 📁 Cấu trúc thư mục

```
server/
├── app/
│   ├── main.py                  # Entrypoint: cấu hình FastAPI, CORS, Swagger tags, lifespan DB seed
│   ├── core/
│   │   ├── config.py            # Quản lý cài đặt môi trường (Settings, PostgreSQL URL)
│   │   └── security.py          # Băm và xác thực mật khẩu (PBKDF2-HMAC-SHA256)
│   ├── db/
│   │   ├── base.py              # DeclarativeBase SQLAlchemy
│   │   └── session.py           # Engine thuần PostgreSQL, SessionLocal, get_db dependency
│   ├── models/
│   │   ├── base.py              # AccountMixin (các trường dùng chung cho tài khoản)
│   │   ├── user.py              # Model User (bảng users)
│   │   ├── seller.py            # Model Seller (bảng sellers, quan hệ 1-N restaurants)
│   │   ├── admin.py             # Model Admin (bảng admins, role_level)
│   │   └── restaurant.py        # Model Restaurant (bảng restaurants, toạ độ lat/lon)
│   ├── schemas/
│   │   ├── common.py            # Schemas chung (LoginRequest, RoleLoginResponse)
│   │   ├── user.py              # Schemas cho User (UserRegister, UserLogin, UserResponse)
│   │   ├── seller.py            # Schemas cho Seller (SellerRegister, SellerLogin, SellerResponse)
│   │   ├── admin.py             # Schemas cho Admin (AdminLogin, AdminResponse)
│   │   ├── map.py               # Schemas cho OpenStreetMap Geocoding
│   │   └── restaurant.py        # Schemas cho Restaurant (Create, Update, Response)
│   ├── services/
│   │   ├── user_service.py      # Xử lý đăng ký & xác thực User
│   │   ├── seller_service.py    # Xử lý đăng ký & xác thực Seller
│   │   ├── admin_service.py     # Xử lý xác thực Admin & seeder mặc định
│   │   ├── map_service.py       # Tích hợp OpenStreetMap Nominatim API
│   │   └── restaurant_service.py # Nghiệp vụ CRUD Quán ăn & Không gian PostGIS
│   └── api/
│       └── v1/
│           ├── router.py        # Router tổng hợp v1
│           └── endpoints/
│               ├── auth_user.py   # POST /api/v1/auth/user/register, /login
│               ├── auth_seller.py # POST /api/v1/auth/seller/register, /login
│               ├── auth_admin.py  # POST /api/v1/auth/admin/login
│               ├── map.py         # GET /api/v1/map/search, /reverse
│               └── restaurants.py # Quản lý quán ăn Seller & PostGIS (/nearby, /distance)
├── tests/
│   ├── conftest.py              # Fixture TestClient + PostgreSQL ptc1_test_db với savepoint rollback
│   ├── test_auth.py             # 10 Unit tests cho 3 role (User, Seller, Admin)
│   ├── test_map.py              # 9 Unit tests cho OpenStreetMap Geocoding
│   ├── test_restaurant.py       # 9 Unit tests cho Quán ăn (CRUD, 1-N, ownership, validation)
│   ├── test_restaurant_spatial.py # 4 Unit tests cho PostGIS (bán kính ST_DWithin, khoảng cách ST_Distance)
│   ├── test_main.py             # Unit test cho root endpoint GET /
│   └── test_swagger.py          # Unit test cho Swagger UI & OpenAPI schema
├── requirements.txt             # Danh sách dependencies (FastAPI, SQLAlchemy, Psycopg 3, GeoAlchemy2...)
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
```

### 2. Cài đặt thư viện
```bash
pip install -r server/requirements.txt
```

### 3. Cấu hình file .env
Tạo file `.env` từ `.env.example`:
```env
DATABASE_URL="postgresql+psycopg://postgres:2005@localhost:5432/ptc1_db"
TEST_DATABASE_URL="postgresql+psycopg://postgres:2005@localhost:5432/ptc1_test_db"
```

### 4. Chạy Server ở chế độ Development
Từ thư mục gốc dự án:
```bash
uvicorn server.app.main:app --reload --port 8000
```
- Swagger UI tại: [http://localhost:8000/docs](http://localhost:8000/docs)
- Tài khoản Admin mặc định có sẵn: `admin@example.com` / `admin123`.

### 5. Chạy kiểm thử (Pytest)
```bash
pytest server/tests -v
```
Toàn bộ 14 test cases sẽ được thực thi trực tiếp trên database `ptc1_test_db` của PostgreSQL với transaction rollback tự động.
