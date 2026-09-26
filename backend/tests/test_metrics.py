import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_metrics():
    # Hit a few endpoints to generate telemetry
    client.get("/")
    client.get("/api/dashboard/kpis")
    client.get("/api/products")
    
    # Scrape metrics
    res = client.get("/metrics")
    print(f"Status Code: {res.status_code}")
    assert res.status_code == 200
    content = res.text
    print("Metrics sample:")
    print(content[:500])
    
    assert "stocksense_total_products" in content
    assert "stocksense_http_requests_total" in content
    print("Prometheus metrics verification passed!")

if __name__ == "__main__":
    test_metrics()
