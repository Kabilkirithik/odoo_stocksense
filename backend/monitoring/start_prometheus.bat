@echo off
title StockSense Prometheus Server
echo ======================================================
echo Starting Prometheus Server (Port: 9090)
echo Scrape Target: http://localhost:8000/metrics
echo UI: http://localhost:9090
echo ======================================================
cd /d "%~dp0prometheus"
if not exist "prometheus.exe" (
    echo [ERROR] prometheus.exe not found!
    echo Run: python ../setup_prometheus.py
    pause
    exit /b 1
)
prometheus.exe --config.file=prometheus.yml
pause
