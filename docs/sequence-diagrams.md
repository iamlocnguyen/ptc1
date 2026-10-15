# Sơ đồ Tuần tự Hệ thống (Sequence Diagrams) - PTC1

Tài liệu này mô tả chi tiết các luồng xử lý tuần tự (Sequence Diagrams) giữa **Tác nhân (Actors)** và **Các thành phần phần mềm (Components)** trong hệ thống PTC1, bám sát **100% mã nguồn thực tế hiện có** tại `server/app/`.

---

## 1. Định nghĩa Tác nhân (Actors) & Thành phần tham gia (Participants)

### 1.1. Các Tác nhân (Actors)
- 👤 **Khách hàng (User):** Người dùng dịch vụ, thực hiện đăng ký, đăng nhập tài khoản, tra cứu quán ăn.
- 🏪 **Người bán (Seller):** Chủ cửa hàng/quán ăn, thực hiện đăng ký gian hàng và quản lý danh sách quán ăn của mình.
- 🌐 **Khách vãng lai (Guest):** Người dùng chưa đăng nhập, được phép duyệt tìm kiếm quán ăn và tra cứu vị trí địa lý.
- 🗺️ **Hệ thống bản đồ ngoài (OpenStreetMap Nominatim):** Dịch vụ bên thứ ba cung cấp dữ liệu bản đồ và tọa độ địa lý.

### 1.2. Các Thành phần Hệ thống (System Participants)
- 🚪 **FastAPI APIRouter:** Tầng Controller tiếp nhận HTTP Request, xác thực schema Pydantic và điều phối.
- ⚙️ **Service Layer (`UserService`, `RestaurantService`, `MapService`):** Tầng xử lý logic nghiệp vụ.
- 🔐 **Security Utils (`server.app.core.security`):** Băm và xác thực mật khẩu bằng thuật toán chuẩn PBKDF2-HMAC-SHA256 (100.000 vòng lặp).
- 🗄️ **Database Layer (PostgreSQL 14 & PostGIS Engine):** Lưu trữ dữ liệu quan hệ và thực thi các truy vấn không gian (`ST_DWithin`, `ST_Distance`).

---

## 2. Luồng 1: Xác thực Tài khoản (Đăng ký & Đăng nhập)

Áp dụng cho module: `server/app/api/v1/endpoints/auth_user.py` & `server/app/services/user_service.py`.

![Sơ đồ Tuần tự Xác thực Tài khoản](seq-auth.png)

<details>
<summary><b>Xem mã nguồn Mermaid</b></summary>

```mermaid
sequenceDiagram
    autonumber
    actor User as Khách hàng (User)
    participant API as FastAPI Router (auth_user.py)
    participant Svc as UserService (user_service.py)
    participant Sec as Security Utils (PBKDF2 SHA256)
    participant DB as PostgreSQL (users table)

    User->>API: POST /api/v1/auth/user/register {email, password, full_name}
    activate API
    API->>Svc: register(db, payload)
    activate Svc
    Svc->>DB: select(User).where(User.email == email)
    DB-->>Svc: None (chưa tồn tại)
    Svc->>Sec: hash_password(password)
    Sec-->>Svc: hashed_password (salt + 100k rounds)
    Svc->>DB: INSERT INTO users ... (db.add + db.commit)
    DB-->>Svc: id, email, created_at
    Svc-->>API: User instance
    deactivate Svc
    API-->>User: HTTP 201 Created (UserResponse)
    deactivate API

    Note over User, DB: Luồng Đăng nhập (Login)
    User->>API: POST /api/v1/auth/user/login {email, password}
    activate API
    API->>Svc: authenticate(db, email, password)
    activate Svc
    Svc->>DB: select(User).where(User.email == email)
    DB-->>Svc: User record
    Svc->>Sec: verify_password(password, hashed_password)
    Sec-->>Svc: True (khớp mật khẩu)
    Svc-->>API: User (is_active = True)
    deactivate Svc
    API-->>User: HTTP 200 OK (RoleLoginResponse role='user')
    deactivate API
```
</details>

### Diễn giải chi tiết:
1. **Đăng ký:**
   - Client gửi `email`, `password`, `full_name`.
   - `UserService` kiểm tra sự tồn tại của `email` trong bảng `users`. Nếu đã tồn tại -> Trả về `400 Bad Request`.
   - Nếu hợp lệ -> Gọi `security.hash_password` sinh chuỗi muối ngẫu nhiên và băm qua PBKDF2-HMAC-SHA256.
   - Thêm bản ghi vào DB, `commit`, và trả về `UserResponse` (HTTP 201).
2. **Đăng nhập:**
   - Client gửi `email` và `password`.
   - `UserService` tìm user trong DB -> Kiểm tra chuỗi băm bằng `verify_password`. Nếu sai -> Trả về `401 Unauthorized`.
   - Kiểm tra `is_active` -> Trả về `RoleLoginResponse` với thông tin User và `role: "user"`.

---

## 3. Luồng 2: Seller Tạo mới Quán ăn & Tự động sinh tọa độ PostGIS

Áp dụng cho module: `server/app/api/v1/endpoints/restaurants.py` & `server/app/services/restaurant_service.py`.

![Sơ đồ Tuần tự Seller Tạo Quán ăn](seq-restaurant-create.png)

<details>
<summary><b>Xem mã nguồn Mermaid</b></summary>

```mermaid
sequenceDiagram
    autonumber
    actor Seller as Người bán (Seller)
    participant API as Router (restaurants.py)
    participant Svc as RestaurantService (restaurant_service.py)
    participant DB as PostgreSQL + PostGIS (restaurants table)

    Seller->>API: POST /api/v1/sellers/{id}/restaurants {name, address, lat, lon, phone}
    activate API
    API->>Svc: create_restaurant(db, seller_id, payload)
    activate Svc
    Svc->>DB: db.get(Seller, seller_id)
    DB-->>Svc: Seller record (xác thực chủ quán hợp lệ)
    Svc->>DB: INSERT INTO restaurants (seller_id, name, latitude, longitude...)
    activate DB
    Note right of DB: PostGIS tự động tính toán cột computed:<br/>location = ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
    DB-->>Svc: db.commit() + db.refresh() -> Restaurant (id, location)
    deactivate DB
    Svc-->>API: Restaurant entity
    deactivate Svc
    API-->>Seller: HTTP 201 Created (RestaurantResponse)
    deactivate API
```
</details>

### Diễn giải chi tiết:
1. Người bán gửi thông tin quán kèm tọa độ WGS84 (`latitude`, `longitude`).
2. Router kiểm tra ràng buộc kiểu dữ liệu qua Pydantic schema `RestaurantCreate`.
3. `RestaurantService` kiểm tra `seller_id` có tồn tại trong bảng `sellers` không. Nếu không có -> Trả về `404 Not Found`.
4. Khi insert vào bảng `restaurants`, engine PostgreSQL + PostGIS tự động kích hoạt biểu thức tính toán lưu trữ:
   $$location = \text{ST\_SetSRID}(\text{ST\_MakePoint}(longitude, latitude), 4326)::\text{geography}$$
5. Quán ăn được tạo thành công với khóa ngoại gắn liền với Seller, trả về HTTP 201 Created.

---

## 4. Luồng 3: Tìm kiếm Quán ăn Gần đây bằng GPS (Spatial Radius Search)

Áp dụng cho module: `server/app/api/v1/endpoints/restaurants.py` (Endpoint `GET /api/v1/restaurants/nearby`).

![Sơ đồ Tuần tự Tìm Quán Gần Đây](seq-spatial-search.png)

<details>
<summary><b>Xem mã nguồn Mermaid</b></summary>

```mermaid
sequenceDiagram
    autonumber
    actor Guest as Khách vãng lai / User
    participant API as Router (restaurants.py)
    participant Svc as RestaurantService (restaurant_service.py)
    participant DB as PostgreSQL (PostGIS Engine)

    Guest->>API: GET /api/v1/restaurants/nearby?lat=10.77&lon=106.69&radius_meters=3000
    activate API
    API->>Svc: find_nearby(db, lat=10.77, lon=106.69, radius=3000)
    activate Svc
    Svc->>DB: SELECT *, ST_Distance(location, user_point) FROM restaurants<br/>WHERE ST_DWithin(location, user_point, 3000)<br/>ORDER BY distance ASC
    activate DB
    Note right of DB: Sử dụng Spatial GiST Index trên cột location<br/>Độ phức tạp O(log N)
    DB-->>Svc: Danh sách quán trong bán kính + khoảng cách mét (Float)
    deactivate DB
    Svc-->>API: List[NearbyRestaurantResponse] (gồm distance_meters & distance_km)
    deactivate Svc
    API-->>Guest: HTTP 200 OK (Danh sách quán lân cận đã sắp xếp từ gần đến xa)
    deactivate API
```
</details>

### Diễn giải chi tiết:
1. Khách hàng hoặc khách vãng lai gửi tọa độ hiện tại (`latitude`, `longitude`) kèm bán kính tìm kiếm (mặc định 5000 mét, tối đa 50000 mét).
2. Service khởi tạo điểm vị trí người dùng dưới dạng `Geography POINT(SRID 4326)`.
3. Câu lệnh SQL sử dụng hàm không gian `ST_DWithin` kết hợp **Spatial GiST Index** trên cột `location` để quét nhanh các quán trong bán kính mà không cần quét toàn bộ bảng (table scan).
4. Hàm `ST_Distance` tính toán chính xác khoảng cách trắc địa đường cong mặt cầu (WGS84 ellipsoid).
5. Trả về danh sách quán đã sắp xếp theo khoảng cách tăng dần kèm cả số mét (`distance_meters`) và km (`distance_km`).

---

## 5. Luồng 4: Tra cứu Tọa độ Địa lý qua OpenStreetMap Nominatim

Áp dụng cho module: `server/app/api/v1/endpoints/map.py` & `server/app/services/map_service.py`.

![Sơ đồ Tuần tự Tra cứu Địa điểm Bản đồ](seq-map-geocoding.png)

<details>
<summary><b>Xem mã nguồn Mermaid</b></summary>

```mermaid
sequenceDiagram
    autonumber
    actor Client as Khách hàng / Chủ quán
    participant API as Map Router (map.py)
    participant Svc as MapService (map_service.py)
    participant OSM as OpenStreetMap Nominatim API

    Client->>API: GET /api/v1/map/search?q=Chợ Bến Thành&limit=5
    activate API
    API->>Svc: search_places(query="Chợ Bến Thành", limit=5)
    activate Svc
    Svc->>OSM: HTTP GET /search?q=Chợ Bến Thành&format=jsonv2&countrycodes=vn
    activate OSM
    OSM-->>Svc: Raw JSON list (place_id, display_name, lat, lon, type)
    deactivate OSM
    Svc->>Svc: Chuẩn hóa dữ liệu sang PlaceItem (display_name, lat, lon, type)
    Svc-->>API: MapSearchResponse(total=5, results=[...])
    deactivate Svc
    API-->>Client: HTTP 200 OK (Danh sách địa điểm & tọa độ GPS)
    deactivate API
```
</details>

### Diễn giải chi tiết:
1. Client nhập tên địa điểm hoặc đường phố cần tìm.
2. `MapService` thiết lập `User-Agent` hợp lệ theo quy định sử dụng của OpenStreetMap Nominatim.
3. Gửi truy vấn HTTP GET tới endpoint tìm kiếm của Nominatim với giới hạn quốc gia Việt Nam (`countrycodes=vn`).
4. Chuẩn hóa dữ liệu trả về thành cấu trúc DTO sạch gồm: `display_name`, `latitude`, `longitude`, `type`.
5. Trả về kết quả phục vụ hiển thị gợi ý tìm kiếm hoặc tự động điền tọa độ khi chủ quán tạo quán ăn mới.
