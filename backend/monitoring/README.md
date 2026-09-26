# StockSense Standalone Monitoring (No Docker Required)

This folder contains the complete, native Windows setup for running **Prometheus** and **Grafana** without Docker.

---

## Folder Structure

```
backend/monitoring/
├── prometheus/
│   ├── prometheus.yml          # Scraper config pointing to localhost:8000
│   └── prometheus.exe          # Downloaded standalone executable
├── grafana/
│   ├── bin/grafana-server.exe  # Standalone Grafana binary
│   └── dashboards/
│       └── stocksense_dashboard.json # Pre-built dashboard
├── setup_prometheus.py         # One-click downloader for Prometheus
├── setup_grafana.py            # One-click downloader for Grafana
├── start_prometheus.bat        # Double-click launcher for Prometheus
└── start_grafana.bat           # Double-click launcher for Grafana
```

---

## 🚀 Running Monitoring in 3 Steps

### Step 1: Start FastAPI Backend
Ensure your FastAPI server is running:
```powershell
cd backend
uv run uvicorn app.main:app --reload --port 8000
```
Verify telemetry is live: `http://localhost:8000/metrics`

### Step 2: Start Prometheus (Port 9090)
Double-click `start_prometheus.bat` or run:
```powershell
cd backend\monitoring\prometheus
.\prometheus.exe --config.file=prometheus.yml
```
Prometheus Web UI: `http://localhost:9090` (Targets: `http://localhost:9090/targets`)

### Step 3: Start Grafana (Port 3000)
Double-click `start_grafana.bat` or run:
```powershell
cd backend\monitoring\grafana\bin
.\grafana-server.exe
```
1. Open `http://localhost:3000` (Default Login: `admin` / `admin`).
2. Go to **Connections &rarr; Data Sources &rarr; Add data source &rarr; Prometheus**.
   - Set URL: `http://localhost:9090`
   - Click **Save & Test**.
3. Go to **Dashboards &rarr; New &rarr; Import**.
   - Upload or paste `backend/monitoring/grafana/dashboards/stocksense_dashboard.json`.
   - Select the Prometheus datasource and click **Import**.
4. You now have full real-time telemetry on API latency, error rates, low stock alerts, catalog count, and pending orders!
