import os
import urllib.request
import zipfile
import shutil

GRAFANA_VERSION = "11.2.0"
GRAFANA_URL = f"https://dl.grafana.com/oss/release/grafana-{GRAFANA_VERSION}.windows-amd64.zip"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAFANA_DIR = os.path.join(BASE_DIR, "grafana")
ZIP_FILE = os.path.join(GRAFANA_DIR, "grafana.zip")
SERVER_EXE = os.path.join(GRAFANA_DIR, "bin", "grafana-server.exe")

def download_and_extract():
    if os.path.exists(SERVER_EXE):
        print(f"[OK] Grafana server already present at: {SERVER_EXE}")
        return

    print(f"Downloading Grafana v{GRAFANA_VERSION} for Windows...")
    urllib.request.urlretrieve(GRAFANA_URL, ZIP_FILE)
    print("Download complete. Extracting archive...")

    temp_extract = os.path.join(GRAFANA_DIR, "temp_extract")
    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        zip_ref.extractall(temp_extract)

    # Move extracted contents (grafana-v11.2.0/...) directly into GRAFANA_DIR
    extracted_root = os.path.join(temp_extract, os.listdir(temp_extract)[0])
    for item in os.listdir(extracted_root):
        src = os.path.join(extracted_root, item)
        dst = os.path.join(GRAFANA_DIR, item)
        if os.path.exists(dst):
            if os.path.isdir(dst):
                # merge / skip existing folders like dashboards
                for sub_item in os.listdir(src):
                    sub_src = os.path.join(src, sub_item)
                    sub_dst = os.path.join(dst, sub_item)
                    if not os.path.exists(sub_dst):
                        shutil.move(sub_src, sub_dst)
                continue
            else:
                os.remove(dst)
        shutil.move(src, dst)

    shutil.rmtree(temp_extract, ignore_errors=True)
    if os.path.exists(ZIP_FILE):
        os.remove(ZIP_FILE)

    print(f"[SUCCESS] Grafana installed in: {GRAFANA_DIR}")

if __name__ == "__main__":
    download_and_extract()
