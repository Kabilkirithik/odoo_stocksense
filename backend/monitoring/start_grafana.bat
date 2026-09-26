@echo off
title StockSense Grafana Server
echo ======================================================
echo Starting Grafana Server (Port: 3000)
echo UI: http://localhost:3000 (User: admin / Pass: admin)
echo ======================================================
cd /d "%~dp0grafana"
if exist "bin\grafana-server.exe" (
    cd bin
    grafana-server.exe
) else (
    echo [ERROR] grafana-server.exe not found in backend\monitoring\grafana\bin!
    echo Run: python ../setup_grafana.py
    pause
    exit /b 1
)
pause
