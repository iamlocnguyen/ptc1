@echo off
chcp 65001 >nul
title [CAI DAT] Tu Dong Thiet Lap Moi Truong PTC1
cls
echo ==============================================================================
echo              HE THONG CAI DAT TU DONG 1-CLICK CHO DU AN PTC1
echo ==============================================================================
echo.
echo  File nay se tu dong thiet lap toan bo moi truong tren may tinh giong 100%%:
echo    [1] Python 3.9.25 (CPython 64-bit + dang ky he thong toan cuc)
echo    [2] PostgreSQL 14 (cong 5432, mat khau 2005)
echo    [3] PostGIS 3.6.1 Spatial Extension
echo    [4] Khoi tao Database ptc1_db, ptc1_test_db & kich hoat PostGIS
echo    [5] Cau hinh file .env
echo    [6] Tao Virtualenv (.venv) & cai dat toan bo thu vien
echo    [7] Chay kiem thu Pytest xac thuc he thong
echo.
echo ==============================================================================
echo Dang khoi dong voi quyen Administrator...
echo ==============================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"

echo.
echo ==============================================================================
echo Nhan phim bat ky de thoat...
echo ==============================================================================
pause >nul
