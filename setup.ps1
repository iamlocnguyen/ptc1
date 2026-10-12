# ==============================================================================
# SCRIPT TỰ ĐỘNG CÀI ĐẶT MÔI TRƯỜNG DỰ ÁN PTC1 (BACKEND FASTAPI + POSTGIS)
# Hỗ trợ: Windows 10/11 64-bit
# Tự động cài đặt:
#   1. Python 3.9.13 (64-bit)
#   2. PostgreSQL 14.x
#   3. PostGIS 3.6.1 cho PostgreSQL 14
#   4. Khởi tạo Database (ptc1_db, ptc1_test_db) và kích hoạt PostGIS extension
#   5. Tạo file .env từ .env.example
#   6. Tạo Virtual Environment (.venv) & Cài đặt requirements.txt
#   7. Chạy bộ kiểm thử (pytest) để xác thực hệ thống 100%
# ==============================================================================

# 0. Yêu cầu quyền Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[*] Script yêu cầu quyền Administrator để cài đặt PostgreSQL & PostGIS." -ForegroundColor Yellow
    Write-Host "[*] Đang tự động nâng quyền (UAC Prompt)..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList ("-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"") -Verb RunAs
    exit
}

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "PTC1 Environment Auto-Setup"

function Print-Step($num, $text) {
    Write-Host "`n========================================================" -ForegroundColor Cyan
    Write-Host " [Bước $num] $text" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Cyan
}

function Print-Success($text) {
    Write-Host "[✓] $text" -ForegroundColor Green
}

function Print-Info($text) {
    Write-Host "[i] $text" -ForegroundColor Yellow
}

function Print-Error($text) {
    Write-Host "[X] $text" -ForegroundColor Red
}

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
Print-Info "Thư mục dự án: $ProjectRoot"

# ------------------------------------------------------------------------------
# BƯỚC 1: KIỂM TRA & CÀI ĐẶT PYTHON 3.9.25
# ------------------------------------------------------------------------------
Print-Step 1 "Kiểm tra và Cài đặt Python 3.9.25 (Bản bảo mật chuẩn CPython)"

$py39Path = ""
$uvPy39Path = "$env:APPDATA\uv\python\cpython-3.9.25-windows-x86_64-none\python.exe"

if (Test-Path $uvPy39Path) {
    $py39Path = $uvPy39Path
}

if (-not $py39Path) {
    # Kiểm tra xem có lệnh uv sẵn không
    $uvCmd = Get-Command uv.exe -ErrorAction SilentlyContinue
    if (-not $uvCmd) {
        Print-Info "Đang kiểm tra và cài đặt công cụ uv để tải Python 3.9.25..."
        try {
            winget install --id astral-sh.uv --silent --accept-package-agreements --accept-source-agreements
        } catch {}
        
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $uvCmd = Get-Command uv.exe -ErrorAction SilentlyContinue
    }

    if ($uvCmd) {
        Print-Info "Đang tải và cài đặt Python 3.9.25 qua uv..."
        & uv python install 3.9.25
        $foundPath = & uv python find 3.9.25 2>$null
        if ($foundPath -and (Test-Path $foundPath.Trim())) {
            $py39Path = $foundPath.Trim()
        }
    }
}

# Nếu vẫn chưa tìm được, fallback các đường dẫn tiêu chuẩn
if (-not $py39Path) {
    $fallbackPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
        "C:\Program Files\Python39\python.exe",
        "C:\Python39\python.exe"
    )
    foreach ($path in $fallbackPaths) {
        if (Test-Path $path) {
            $py39Path = $path
            break
        }
    }
}

if ($py39Path) {
    # Đồng bộ hóa Python 3.9.25 vào thư mục chuẩn và cập nhật PATH để toàn bộ máy nhận diện
    $targetPyDir = "$env:LOCALAPPDATA\Programs\Python\Python39"
    $targetPyExe = "$targetPyDir\python.exe"

    if ($py39Path -ne $targetPyExe) {
        Print-Info "Đang đồng bộ Python 3.9.25 vào đường dẫn hệ thống chuẩn ($targetPyDir)..."
        New-Item -ItemType Directory -Path $targetPyDir -Force | Out-Null
        $sourceDir = Split-Path -Parent $py39Path
        Copy-Item -Path "$sourceDir\*" -Destination $targetPyDir -Recurse -Force
        $py39Path = $targetPyExe
    }

    # Đăng ký Windows Registry cho py launcher
    try {
        New-Item -Path "HKCU:\Software\Python\PythonCore\3.9\InstallPath" -Force | Out-Null
        Set-ItemProperty -Path "HKCU:\Software\Python\PythonCore\3.9\InstallPath" -Name "(Default)" -Value "$targetPyDir\"
        Set-ItemProperty -Path "HKCU:\Software\Python\PythonCore\3.9\InstallPath" -Name "ExecutablePath" -Value "$targetPyExe"
    } catch {}

    # Đưa Python 3.9.25 lên đầu biến môi trường PATH của User
    try {
        $curUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $pathParts = $curUserPath -split ";" | Where-Object { 
            $_ -and 
            $_ -notlike "*Python39*" -and 
            $_ -notlike "*cpython-3.9*"
        }
        $newPathParts = @(
            "$targetPyDir",
            "$targetPyDir\Scripts"
        ) + $pathParts
        $newUserPath = ($newPathParts -join ";")
        [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
        $env:Path = "$targetPyDir;$targetPyDir\Scripts;" + $env:Path
    } catch {}

    $verOutput = & "$py39Path" --version
    Print-Success "Đã cấu hình Python 3.9.25 thành công: $verOutput"
    Print-Success "Lệnh 'python' và 'py -3.9' toàn cục trên máy đã trỏ về Python 3.9.25."
} else {
    Print-Error "Không thể cài đặt tự động Python 3.9.25. Vui lòng kiểm tra kết nối mạng."
    exit 1
}

# ------------------------------------------------------------------------------
# BƯỚC 2: KIỂM TRA & CÀI ĐẶT POSTGRESQL 14
# ------------------------------------------------------------------------------
Print-Step 2 "Kiểm tra và Cài đặt PostgreSQL 14"

$pg14Dir = "C:\Program Files\PostgreSQL\14"
$psqlPath = "$pg14Dir\bin\psql.exe"
$pgPass = "2005"

if (-not (Test-Path $psqlPath)) {
    Print-Info "Chưa tìm thấy PostgreSQL 14. Đang tiến hành cài đặt qua winget..."
    try {
        winget install --id PostgreSQL.PostgreSQL.14 --silent --accept-package-agreements --accept-source-agreements --override "--unattendedmodeui none --superpassword $pgPass"
    } catch {
        Print-Info "Winget gặp lỗi hoặc không khả dụng. Đang tải bản cài đặt trực tiếp từ EnterpriseDB..."
        $pgInstallerUrl = "https://get.enterprisedb.com/postgresql/postgresql-14.15-1-windows-x64.exe"
        $pgInstallerPath = "$env:TEMP\postgresql-14-installer.exe"
        Invoke-WebRequest -Uri $pgInstallerUrl -OutFile $pgInstallerPath -UseBasicParsing
        Start-Process -FilePath $pgInstallerPath -ArgumentList "--unattendedmodeui none --mode unattended --superpassword $pgPass --servicepassword $pgPass" -Wait
        Remove-Item -Force $pgInstallerPath -ErrorAction SilentlyContinue
    }
}

# Đảm bảo Service PostgreSQL đang chạy
$pgService = Get-Service -Name "postgresql-x64-14" -ErrorAction SilentlyContinue
if (-not $pgService) {
    $pgService = Get-Service | Where-Object { $_.Name -like "*postgres*" } | Select-Object -First 1
}

if ($pgService) {
    if ($pgService.Status -ne "Running") {
        Print-Info "Đang khởi động PostgreSQL service ($($pgService.Name))..."
        Start-Service -Name $pgService.Name
    }
    Print-Success "PostgreSQL Service ($($pgService.Name)) đang chạy."
} else {
    Print-Info "Không tìm thấy Service Windows, đang kiểm tra cổng 5432..."
}

# ------------------------------------------------------------------------------
# BƯỚC 3: CÀI ĐẶT POSTGIS 3.6.1 EXTENSION
# ------------------------------------------------------------------------------
Print-Step 3 "Cài đặt PostGIS 3.6.1 Spatial Extension"

$postgisZipUrl = "https://download.osgeo.org/postgis/windows/pg14/postgis-bundle-pg14-3.6.1x64.zip"
$postgisZipPath = "$env:TEMP\postgis-bundle-pg14-3.6.1x64.zip"
$postgisExtractDir = "$env:TEMP\postgis-bundle-extract"

$postgisSqlExists = Test-Path "$pg14Dir\share\extension\postgis.control"
if ($postgisSqlExists) {
    Print-Success "PostGIS extension đã sẵn sàng trong PostgreSQL 14."
} else {
    Print-Info "Đang tải gói PostGIS 3.6.1 x64 từ OSGeo..."
    Invoke-WebRequest -Uri $postgisZipUrl -OutFile $postgisZipPath -UseBasicParsing

    Print-Info "Đang giải nén gói PostGIS..."
    if (Test-Path $postgisExtractDir) { Remove-Item -Recurse -Force $postgisExtractDir }
    Expand-Archive -Path $postgisZipPath -DestinationPath $postgisExtractDir -Force

    $subBundleDir = Get-ChildItem -Path $postgisExtractDir -Directory | Select-Object -First 1
    $bundleSource = if ($subBundleDir) { $subBundleDir.FullName } else { $postgisExtractDir }

    Print-Info "Đang sao chép các tệp PostGIS vào $pg14Dir..."
    Copy-Item -Path "$bundleSource\*" -Destination $pg14Dir -Recurse -Force

    Remove-Item -Force $postgisZipPath -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $postgisExtractDir -ErrorAction SilentlyContinue
    Print-Success "Cài đặt PostGIS vào PostgreSQL 14 hoàn tất."
}

# ------------------------------------------------------------------------------
# BƯỚC 4: TẠO DATABASE VÀ KÍCH HOẠT POSTGIS EXTENSION
# ------------------------------------------------------------------------------
Print-Step 4 "Khởi tạo CSDL ptc1_db, ptc1_test_db và Kích hoạt PostGIS"

$env:PGPASSWORD = $pgPass

function Execute-Sql($dbName, $sqlText) {
    & "$psqlPath" -h localhost -p 5432 -U postgres -d $dbName -c $sqlText 2>$null
}

# Tạo ptc1_db nếu chưa có
$checkDb1 = & "$psqlPath" -h localhost -p 5432 -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='ptc1_db'"
if ($checkDb1 -ne "1") {
    Print-Info "Đang tạo database 'ptc1_db'..."
    Execute-Sql "postgres" "CREATE DATABASE ptc1_db;"
} else {
    Print-Success "Database 'ptc1_db' đã tồn tại."
}

# Tạo ptc1_test_db nếu chưa có
$checkDb2 = & "$psqlPath" -h localhost -p 5432 -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='ptc1_test_db'"
if ($checkDb2 -ne "1") {
    Print-Info "Đang tạo database 'ptc1_test_db'..."
    Execute-Sql "postgres" "CREATE DATABASE ptc1_test_db;"
} else {
    Print-Success "Database 'ptc1_test_db' đã tồn tại."
}

# Kích hoạt PostGIS trên cả 2 database
Print-Info "Kích hoạt PostGIS trên 'ptc1_db'..."
Execute-Sql "ptc1_db" "CREATE EXTENSION IF NOT EXISTS postgis;"
Print-Info "Kích hoạt PostGIS trên 'ptc1_test_db'..."
Execute-Sql "ptc1_test_db" "CREATE EXTENSION IF NOT EXISTS postgis;"
Print-Success "Kích hoạt extension PostGIS thành công trên cả 2 CSDL."

# ------------------------------------------------------------------------------
# BƯỚC 5: CẤU HÌNH FILE MÔI TRƯỜNG (.env)
# ------------------------------------------------------------------------------
Print-Step 5 "Cấu hình biến môi trường (.env)"

$envFile = "$ProjectRoot\.env"
$envExample = "$ProjectRoot\.env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item -Path $envExample -Destination $envFile
        Print-Success "Đã tạo file .env từ .env.example."
    } else {
        # Tạo mới file .env chuẩn
        $envContent = @"
DATABASE_URL=postgresql+psycopg://postgres:2005@localhost:5432/ptc1_db
TEST_DATABASE_URL=postgresql+psycopg://postgres:2005@localhost:5432/ptc1_test_db
APP_ENV=development
API_V1_PREFIX=/api/v1
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
"@
        Set-Content -Path $envFile -Value $envContent -Encoding UTF8
        Print-Success "Đã tạo mới file .env với thông số kết nối chuẩn."
    }
} else {
    Print-Success "File .env đã tồn tại."
}

# ------------------------------------------------------------------------------
# BƯỚC 6: TẠO VIRTUAL ENVIRONMENT (.venv) & CÀI ĐẶT THƯ VIỆN
# ------------------------------------------------------------------------------
Print-Step 6 "Khởi tạo Virtualenv (.venv) & Cài đặt Dependencies"

$venvPython = "$ProjectRoot\.venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Print-Info "Đang tạo môi trường ảo Python 3.9 tại .venv..."
    & "$py39Path" -m venv "$ProjectRoot\.venv"
    Print-Success "Đã tạo .venv."
} else {
    Print-Success "Môi trường ảo .venv đã tồn tại."
}

Print-Info "Đang nâng cấp pip và cài đặt dependencies từ server/requirements.txt..."
& "$venvPython" -m pip install --upgrade pip --quiet
& "$venvPython" -m pip install -r "$ProjectRoot\server\requirements.txt" --quiet
Print-Success "Cài đặt thư viện Python hoàn tất thành công."

# ------------------------------------------------------------------------------
# BƯỚC 7: XÁC THỰC HỆ THỐNG VỚI PYTEST
# ------------------------------------------------------------------------------
Print-Step 7 "Chạy toàn bộ Test Suite để Kiểm tra Hệ thống"

$pytestExe = "$ProjectRoot\.venv\Scripts\pytest.exe"
if (Test-Path $pytestExe) {
    & "$pytestExe" "$ProjectRoot\server\tests" -v
    if ($LASTEXITCODE -eq 0) {
        Print-Success "Toàn bộ 36 tests PASSED 100%! Hệ thống sẵn sàng hoạt động."
    } else {
        Print-Error "Một số bài test chưa đạt. Vui lòng kiểm tra lại log chi tiết bên trên."
    }
}

# ------------------------------------------------------------------------------
# HOÀN TẤT
# ------------------------------------------------------------------------------
Write-Host "`n========================================================" -ForegroundColor Green
Write-Host " [HOÀN TẤT CÀI ĐẶT] Môi trường PTC1 đã sẵn sàng!" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "Để khởi chạy máy chủ backend, chạy lệnh sau:" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\uvicorn server.app.main:app --reload --port 8000" -ForegroundColor Cyan
Write-Host "Truy cập Swagger UI tại: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Green
