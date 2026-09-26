import os
import urllib.request
import zipfile
import shutil

PROMETHEUS_VERSION = "2.54.1"
PROMETHEUS_URL = f"https://github.com/prometheus/prometheus/releases/download/v{PROMETHEUS_VERSION}/prometheus-{PROMETHEUS_VERSION}.windows-amd64.zip"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROM_DIR = os.path.join(BASE_DIR, "prometheus")
ZIP_FILE = os.path.join(PROM_DIR, "prometheus.zip")
EXE_PATH = os.path.join(PROM_DIR, "prometheus.exe")

def download_and_extract():
    if os.path.exists(EXE_PATH):
        print(f"[OK] Prometheus executable already present at: {EXE_PATH}")
        return

    print(f"Downloading Prometheus v{PROMETHEUS_VERSION} for Windows...")
    urllib.request.urlretrieve(PROMETHEUS_URL, ZIP_FILE)
    print("Download complete. Extracting archive...")

    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        for member in zip_ref.namelist():
            filename = os.path.basename(member)
            if filename in ("prometheus.exe", "promtool.exe"):
                source = zip_ref.open(member)
                target = open(os.path.join(PROM_DIR, filename), "wb")
                with source, target:
                    shutil.copyfileobj(source, target)

    if os.path.exists(ZIP_FILE):
        os.remove(ZIP_FILE)

    print(f"[SUCCESS] prometheus.exe installed in: {PROM_DIR}")

if __name__ == "__main__":
    download_and_extract()
