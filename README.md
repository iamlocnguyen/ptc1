# PTC1 - Backend Spatial Platform (FastAPI + PostGIS)

Hệ thống Backend FastAPI tích hợp xác thực đa vai trò (User, Seller, Admin), dịch vụ bản đồ địa lý OpenStreetMap Geocoding và truy vấn không gian PostGIS cho quán ăn (Restaurant).

---

## 🚀 Cài Đặt Tự Động (Dành cho máy mới / người khác)

Dự án cung cấp script tự động 1-click cài đặt đầy đủ từ A-Z môi trường chạy trên Windows:
- **Python 3.9.13 (64-bit)**
- **PostgreSQL 14.x** (Cổng 5432, mật khẩu mặc định `2005`)
- **PostGIS 3.6.1 Spatial Extension**
- Khởi tạo Database `ptc1_db` và `ptc1_test_db` kèm PostGIS extension
- Khởi tạo file `.env`, môi trường ảo `.venv` và cài đặt `server/requirements.txt`
- Chạy toàn bộ 36 tests tự động kiểm thử

### Cách chạy:
1. **Cách 1 (Nhanh nhất):** Click đúp vào file `setup.bat` (hoặc chuột phải chọn Run as Administrator).
2. **Cách 2 (Qua PowerShell):** Mở PowerShell với quyền Administrator tại thư mục dự án và chạy:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process
   .\setup.ps1
   ```

---

## 🏃 Khởi Chạy Server

Sau khi cài đặt xong:
```powershell
# Kích hoạt virtualenv
.\.venv\Scripts\Activate.ps1

# Chạy server FastAPI
.\.venv\Scripts\uvicorn server.app.main:app --reload --port 8000
```

- **Swagger UI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Chạy Kiểm Thử (Tests)

```powershell
.\.venv\Scripts\pytest server/tests -v
```
*(Toàn bộ 36 test cases kiểm thử Auth, Map OpenStreetMap, Quán ăn, PostGIS Spatial queries và OpenAPI docs)*

---

## 🗺️ Các Tính Năng & API Chính

1. **Authentication (`/api/v1/auth`):**
   - Đăng ký / Đăng nhập Người dùng thông thường (User).
   - Đăng ký / Đăng nhập Người bán (Seller) với thông tin cửa hàng, số điện thoại, địa chỉ.
   - Đăng nhập Quản trị viên (Admin) mặc định.

2. **OpenStreetMap Geocoding (`/api/v1/map`):**
   - `GET /api/v1/map/search?q=...`: Tìm kiếm địa điểm, trả về toạ độ lat/lon và bounding box.
   - `GET /api/v1/map/reverse?lat=...&lon=...`: Đổi toạ độ sang địa chỉ thực tế.

3. **Quản lý Quán Ăn (`/api/v1/restaurants`):**
   - 1 Seller sở hữu nhiều Quán ăn (1-N).
   - Thêm, sửa, xoá quán ăn (kiểm tra quyền sở hữu của Seller).
   - Danh sách công khai quán ăn, chi tiết từng quán.

4. **Dịch Vụ Không Gian PostGIS (`/api/v1/restaurants`):**
   - `GET /api/v1/restaurants/nearby?lat=...&lon=...&radius_km=5`: Tìm quán ăn lân cận trong bán kính bằng `ST_DWithin`, tính khoảng cách chính xác bằng `ST_Distance` và sắp xếp từ gần đến xa theo mét / km.
   - `GET /api/v1/restaurants/{id}/distance?lat=...&lon=...`: Tính khoảng cách trực tiếp từ toạ độ người dùng đến một quán ăn cụ thể.
