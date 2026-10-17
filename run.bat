@echo off
chcp 65001 > nul
title Raspberry Pi 30FPS AI Face Greeter
cd /d "%~dp0"
echo ========================================================
echo  Starting Raspberry Pi Face Greeter Application...
echo ========================================================
"C:\Users\woong\AppData\Local\Programs\Python\Python311\python.exe" -u app.py
pause
