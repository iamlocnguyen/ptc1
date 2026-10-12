@echo off
chcp 65001 >nul
title PTC1 Auto Setup
echo ========================================================
echo       KHOI CHAY CAI DAT TU DONG HE THONG PTC1
echo ========================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '%~dp0setup.ps1'"
pause
