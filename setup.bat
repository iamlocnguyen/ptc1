@echo off
chcp 65001 >nul
title [SETUP] PTC1 Automated Environment Setup
cls
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
pause
