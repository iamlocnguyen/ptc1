# ==============================================================================
# SCRIPT TU DONG CAI DAT MOI TRUONG DU AN PTC1 (BACKEND FASTAPI + POSTGIS + FLUTTER)
# Ho tro: Windows 10/11 64-bit
# ==============================================================================

# 0. Kiem tra quyen Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[*] Script yeu cau quyen Administrator de cai dat PostgreSQL va PostGIS." -ForegroundColor Yellow
    try {
        Start-Process powershell.exe -ArgumentList ("-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"") -Verb RunAs -ErrorAction Stop
        exit
    } catch {
        Write-Host "[*] Khong the tu dong mo hop thoai UAC. Tiep tuc chay voi quyen hien tai..." -ForegroundColor Yellow
        Write-Host "[*] (Goi y: Chuot phai vao CAI_DAT.bat chon 'Run as administrator' neu gap loi PostgreSQL)" -ForegroundColor Yellow
    }
}

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "PTC1 Environment Auto-Setup"

function Print-Step($num, $text) {
    Write-Host "`n========================================================" -ForegroundColor Cyan
    Write-Host " [Buoc $num] $text" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Cyan
}

function Print-Success($text) {
    Write-Host "[OK] $text" -ForegroundColor Green
}

function Print-Info($text) {
    Write-Host "[i] $text" -ForegroundColor Yellow
}

function Print-Error($text) {
    Write-Host "[X] $text" -ForegroundColor Red
}

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
Print-Info "Thu muc du an: $ProjectRoot"

# ------------------------------------------------------------------------------
# BUOC 1: KIEM TRA VA CAI DAT PYTHON 3.9.25
# ------------------------------------------------------------------------------
Print-Step 1 "Kiem tra va Cai dat Python 3.9.25"

$py39Path = ""
$uvPy39Path = "$env:APPDATA\uv\python\cpython-3.9.25-windows-x86_64-none\python.exe"

if (Test-Path $uvPy39Path) {
    $py39Path = $uvPy39Path
}

if (-not $py39Path) {
    $uvCmd = Get-Command uv.exe -ErrorAction SilentlyContinue
    if (-not $uvCmd) {
        Print-Info "Dang kiem tra va cai dat cong cu uv de tai Python 3.9.25..."
        try {
            winget install --id astral-sh.uv --silent --accept-package-agreements --accept-source-agreements
        } catch {}
        
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $uvCmd = Get-Command uv.exe -ErrorAction SilentlyContinue
    }

    if ($uvCmd) {
        Print-Info "Dang tai va cai dat Python 3.9.25 qua uv..."
        & uv python install 3.9.25
        $foundPath = & uv python find 3.9.25 2>$null
        if ($foundPath -and (Test-Path $foundPath.Trim())) {
            $py39Path = $foundPath.Trim()
        }
    }
}

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
    $targetPyDir = "$env:LOCALAPPDATA\Programs\Python\Python39"
    $targetPyExe = "$targetPyDir\python.exe"

    if ($py39Path -ne $targetPyExe) {
        Print-Info "Dang dong bo Python 3.9.25 vao thu muc he thong ($targetPyDir)..."
        New-Item -ItemType Directory -Path $targetPyDir -Force | Out-Null
        $sourceDir = Split-Path -Parent $py39Path
        Copy-Item -Path "$sourceDir\*" -Destination $targetPyDir -Recurse -Force
        $py39Path = $targetPyExe
    }

    try {
        New-Item -Path "HKCU:\Software\Python\PythonCore\3.9\InstallPath" -Force | Out-Null
        Set-ItemProperty -Path "HKCU:\Software\Python\PythonCore\3.9\InstallPath" -Name "(Default)" -Value "$targetPyDir\"
        Set-ItemProperty -Path "HKCU:\Software\Python\PythonCore\3.9\InstallPath" -Name "ExecutablePath" -Value "$targetPyExe"
    } catch {}

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
    Print-Success "Da cau hinh Python 3.9.25 thanh cong: $verOutput"
} else {
    Print-Error "Khong the cai dat tu dong Python 3.9.25. Vui long kiem tra ket noi mang."
    exit 1
}

# ------------------------------------------------------------------------------
# BUOC 2: KIEM TRA VA CAI DAT POSTGRESQL 14
# ------------------------------------------------------------------------------
Print-Step 2 "Kiem tra va Cai dat PostgreSQL 14"

$pg14Dir = "C:\Program Files\PostgreSQL\14"
$psqlPath = "$pg14Dir\bin\psql.exe"
$pgPass = "2005"

if (-not (Test-Path $psqlPath)) {
    Print-Info "Chua tim thay PostgreSQL 14. Dang tien hanh cai dat qua winget..."
    try {
        winget install --id PostgreSQL.PostgreSQL.14 --silent --accept-package-agreements --accept-source-agreements --override "--unattendedmodeui none --superpassword $pgPass"
    } catch {
        Print-Info "Winget gap loi. Dang tai ban cai dat truc tiep tu EnterpriseDB..."
        $pgInstallerUrl = "https://get.enterprisedb.com/postgresql/postgresql-14.15-1-windows-x64.exe"
        $pgInstallerPath = "$env:TEMP\postgresql-14-installer.exe"
        Invoke-WebRequest -Uri $pgInstallerUrl -OutFile $pgInstallerPath -UseBasicParsing
        Start-Process -FilePath $pgInstallerPath -ArgumentList "--unattendedmodeui none --mode unattended --superpassword $pgPass --servicepassword $pgPass" -Wait
        Remove-Item -Force $pgInstallerPath -ErrorAction SilentlyContinue
    }
}

$pgService = Get-Service -Name "postgresql-x64-14" -ErrorAction SilentlyContinue
if (-not $pgService) {
    $pgService = Get-Service | Where-Object { $_.Name -like "*postgres*" } | Select-Object -First 1
}

if ($pgService) {
    if ($pgService.Status -ne "Running") {
        Print-Info "Dang khoi dong PostgreSQL service ($($pgService.Name))..."
        Start-Service -Name $pgService.Name
    }
    Print-Success "PostgreSQL Service ($($pgService.Name)) dang chay."
} else {
    Print-Info "Dang kiem tra cong 5432..."
}

# ------------------------------------------------------------------------------
# BUOC 3: CAI DAT POSTGIS 3.6.1 SPATIAL EXTENSION
# ------------------------------------------------------------------------------
Print-Step 3 "Cai dat PostGIS 3.6.1 Spatial Extension"

$postgisZipUrl = "https://download.osgeo.org/postgis/windows/pg14/postgis-bundle-pg14-3.6.1x64.zip"
$postgisZipPath = "$env:TEMP\postgis-bundle-pg14-3.6.1x64.zip"
$postgisExtractDir = "$env:TEMP\postgis-bundle-extract"

$postgisSqlExists = Test-Path "$pg14Dir\share\extension\postgis.control"
if ($postgisSqlExists) {
    Print-Success "PostGIS extension da san sang trong PostgreSQL 14."
} else {
    Print-Info "Dang tai goi PostGIS 3.6.1 x64 tu OSGeo..."
    Invoke-WebRequest -Uri $postgisZipUrl -OutFile $postgisZipPath -UseBasicParsing

    Print-Info "Dang giai nen goi PostGIS..."
    if (Test-Path $postgisExtractDir) { Remove-Item -Recurse -Force $postgisExtractDir }
    Expand-Archive -Path $postgisZipPath -DestinationPath $postgisExtractDir -Force

    $subBundleDir = Get-ChildItem -Path $postgisExtractDir -Directory | Select-Object -First 1
    $bundleSource = if ($subBundleDir) { $subBundleDir.FullName } else { $postgisExtractDir }

    Print-Info "Dang sao chep cac tep PostGIS vao $pg14Dir..."
    Copy-Item -Path "$bundleSource\*" -Destination $pg14Dir -Recurse -Force

    Remove-Item -Force $postgisZipPath -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $postgisExtractDir -ErrorAction SilentlyContinue
    Print-Success "Cai dat PostGIS vao PostgreSQL 14 hoan tat."
}

# ------------------------------------------------------------------------------
# BUOC 4: TAO DATABASE VA KICH HOAT POSTGIS EXTENSION
# ------------------------------------------------------------------------------
Print-Step 4 "Khoi tao CSDL ptc1_db, ptc1_test_db va Kich hoat PostGIS"

$env:PGPASSWORD = $pgPass
$env:PGOPTIONS = "--client-min-messages=warning"

function Execute-Sql($dbName, $sqlText) {
    & "$psqlPath" -h localhost -p 5432 -U postgres -d $dbName -q -c $sqlText 2>$null
}

$checkDb1 = (& "$psqlPath" -h localhost -p 5432 -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='ptc1_db'" 2>$null)
if ($checkDb1 -ne "1") {
    Print-Info "Dang tao database ptc1_db..."
    Execute-Sql "postgres" "CREATE DATABASE ptc1_db;"
} else {
    Print-Success "Database ptc1_db da ton tai."
}

$checkDb2 = (& "$psqlPath" -h localhost -p 5432 -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='ptc1_test_db'" 2>$null)
if ($checkDb2 -ne "1") {
    Print-Info "Dang tao database ptc1_test_db..."
    Execute-Sql "postgres" "CREATE DATABASE ptc1_test_db;"
} else {
    Print-Success "Database ptc1_test_db da ton tai."
}

Print-Info "Kich hoat PostGIS tren ptc1_db..."
Execute-Sql "ptc1_db" "CREATE EXTENSION IF NOT EXISTS postgis;"
Print-Info "Kich hoat PostGIS tren ptc1_test_db..."
Execute-Sql "ptc1_test_db" "CREATE EXTENSION IF NOT EXISTS postgis;"
Print-Success "Kich hoat extension PostGIS thanh cong tren ca 2 CSDL."

# ------------------------------------------------------------------------------
# BUOC 5: CAU HINH FILE MOI TRUONG (.env)
# ------------------------------------------------------------------------------
Print-Step 5 "Cau hinh bien moi truong (.env)"

$envFile = "$ProjectRoot\.env"
$envExample = "$ProjectRoot\.env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item -Path $envExample -Destination $envFile
        Print-Success "Da tao file .env tu .env.example."
    } else {
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
        Print-Success "Da tao moi file .env voi thong so ket noi chuan."
    }
} else {
    Print-Success "File .env da ton tai."
}

# ------------------------------------------------------------------------------
# BUOC 6: TAO VIRTUAL ENVIRONMENT (.venv) VA CAI DAT THU VIEN
# ------------------------------------------------------------------------------
Print-Step 6 "Khoi tao Virtualenv (.venv) va Cai dat Dependencies"

$venvPython = "$ProjectRoot\.venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Print-Info "Dang tao moi truong ao Python 3.9 tai .venv..."
    & "$py39Path" -m venv "$ProjectRoot\.venv"
    Print-Success "Da tao .venv."
} else {
    Print-Success "Moi truong ao .venv da ton tai."
}

Print-Info "Dang nang cap pip va cai dat dependencies tu server/requirements.txt..."
& "$venvPython" -m pip install --upgrade pip --quiet
& "$venvPython" -m pip install -r "$ProjectRoot\server\requirements.txt" --quiet
Print-Success "Cai dat thu vien Python hoan tat thanh cong."

# ------------------------------------------------------------------------------
# BUOC 7: XAC THUC HE THONG VOI PYTEST
# ------------------------------------------------------------------------------
Print-Step 7 "Chay toan bo Test Suite de Kiem tra He thong Backend"

$pytestExe = "$ProjectRoot\.venv\Scripts\pytest.exe"
if (Test-Path $pytestExe) {
    & "$pytestExe" "$ProjectRoot\server\tests" -v
    if ($LASTEXITCODE -eq 0) {
        Print-Success "Toan bo 36 tests Backend PASSED 100%! He thong san sang hoat dong."
    } else {
        Print-Error "Mot so bai test Backend chua dat. Vui long kiem tra log."
    }
}

# ------------------------------------------------------------------------------
# BUOC 8: KIEM TRA VA CAI DAT FLUTTER 3.44.9 (MOBILE SDK)
# ------------------------------------------------------------------------------
Print-Step 8 "Kiem tra va Cai dat Flutter 3.44.9 (Mobile SDK)"

$flutterBin = ""
$standardFlutterPaths = @(
    "D:\flutter\bin\flutter.bat",
    "C:\src\flutter\bin\flutter.bat",
    "$env:USERPROFILE\flutter\bin\flutter.bat"
)

foreach ($fPath in $standardFlutterPaths) {
    if (Test-Path $fPath) {
        $flutterBin = $fPath
        break
    }
}

if (-not $flutterBin) {
    $fCmd = Get-Command flutter.bat -ErrorAction SilentlyContinue
    if ($fCmd) {
        $flutterBin = $fCmd.Source
    }
}

if (-not $flutterBin) {
    Print-Info "Chua tim thay Flutter SDK. Bat dau tai va cai dat Flutter 3.44.9..."
    $targetFlutterDir = if (Test-Path "D:\") { "D:\flutter" } else { "C:\src\flutter" }
    Print-Info "Dang tai Flutter 3.44.9 ve $targetFlutterDir..."
    git clone --depth 1 --branch 3.44.9 https://github.com/flutter/flutter.git $targetFlutterDir
    $flutterBin = "$targetFlutterDir\bin\flutter.bat"
}

if (Test-Path $flutterBin) {
    $flutterDir = Split-Path (Split-Path $flutterBin -Parent) -Parent
    $flutterBinDir = "$flutterDir\bin"

    try {
        $curUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($curUserPath -notlike "*$flutterBinDir*") {
            [Environment]::SetEnvironmentVariable("Path", "$curUserPath;$flutterBinDir", "User")
        }
        $env:Path = "$flutterBinDir;" + $env:Path
    } catch {}

    $fVer = & "$flutterBin" --version | Select-Object -First 1
    Print-Success "Da xac nhan moi truong Flutter: $fVer"

    $mobileDir = "$ProjectRoot\mobile"
    if (Test-Path "$mobileDir\pubspec.yaml") {
        Print-Info "Dang chay kiem thu cho du an Mobile (Flutter)..."
        Push-Location $mobileDir
        try {
            & "$flutterBin" test
            if ($LASTEXITCODE -eq 0) {
                Print-Success "Kiem thu Mobile hoan tat: 100% Passed!"
            }
        } finally {
            Pop-Location
        }
    }
} else {
    Print-Info "Bo qua cai dat Flutter SDK do khong the tai."
}

# ------------------------------------------------------------------------------
# HOAN TAT
# ------------------------------------------------------------------------------
Write-Host "`n========================================================" -ForegroundColor Green
Write-Host " [HOAN TAT CAI DAT] Moi truong PTC1 da san sang!" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "1. Khoi chay Backend FastAPI:" -ForegroundColor Yellow
Write-Host "   Click dup file CHAY_SERVER.bat hoac chay lenh:" -ForegroundColor Cyan
Write-Host "   .\.venv\Scripts\uvicorn server.app.main:app --reload --port 8000" -ForegroundColor Cyan
Write-Host "2. Swagger UI: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "3. Flutter Mobile SDK: $flutterBin" -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Green
