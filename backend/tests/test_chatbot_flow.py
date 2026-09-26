import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

from sqlalchemy.pool import StaticPool

# Use in-memory SQLite database for isolated test execution with shared static pool
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("[TEST] Running StockSense AI Chatbot Confirmation Flow Tests")
    print("=" * 60)

    # 1. Test Status & Tools Endpoints
    res_status = client.get("/api/chat/status")
    print("1. Status Endpoint:", res_status.status_code, res_status.json())
    assert res_status.status_code == 200
    assert res_status.json()["prompt_loaded"] is True

    res_tools = client.get("/api/chat/tools")
    print("2. Tools Endpoint Count:", res_tools.json()["count"])
    assert res_tools.status_code == 200
    assert res_tools.json()["count"] >= 10

    # 2. Test Read Query (Immediate Execution - No Confirmation Needed)
    res_query = client.post("/api/chat", json={"message": "What is the status of our inventory?"})
    print("\n3. Status Query Response:", res_query.status_code)
    data_query = res_query.json()
    print("Reply:", data_query["reply"][:120], "...")
    assert data_query["pending_action"] is None, "Read queries must not trigger confirmation"
    assert len(data_query["reply"]) > 0, "Chatbot should return a meaningful reply"

    # 3. Test Predictive Query (Immediate Execution - No Confirmation Needed)
    res_pred = client.post("/api/chat", json={"message": "What might be the status of inventory?"})
    print("\n4. Predictive Query Response:", res_pred.status_code)
    data_pred = res_pred.json()
    print("Reply:", data_pred["reply"][:120], "...")
    assert data_pred["pending_action"] is None, "Predictive queries must not trigger confirmation"

    # 4. Test Action Intent: "Create product 'Wireless Mouse' in inventory"
    # Should GATE the action and return pending_action WITHOUT executing yet
    res_action = client.post("/api/chat", json={"message": "Create product \"Wireless Mouse\" in the inventory"})
    print("\n5. Action Request (Confirmation Gating):", res_action.status_code)
    data_action = res_action.json()
    print("Reply:", data_action["reply"])
    print("Pending Action:", data_action["pending_action"])
    assert data_action["pending_action"] is not None, "Mutating action must require confirmation!"
    assert data_action["pending_action"]["tool"] == "create_product"
    assert len(data_action["actions_performed"]) == 0, "Action must NOT be executed prior to confirmation"

    pending_act = data_action["pending_action"]

    # 5. Test Confirmation: Sending confirmed_action
    res_confirm = client.post("/api/chat", json={
        "message": "Yes, proceed with creation",
        "confirmed_action": pending_act
    })
    print("\n6. Action Confirmation Execution:", res_confirm.status_code)
    data_confirm = res_confirm.json()
    print("Reply:", data_confirm["reply"])
    print("Actions Performed:", data_confirm["actions_performed"])
    assert len(data_confirm["actions_performed"]) == 1
    assert data_confirm["actions_performed"][0]["result"]["success"] is True
    assert data_confirm["pending_action"] is None

    # 6. Verify that product now exists in database!
    db = TestingSessionLocal()
    from app.models import Product
    prod = db.query(Product).filter(Product.product_name == "Wireless Mouse").first()
    assert prod is not None, "Product should now be persisted in the DB"
    print(f"\n[OK] Persisted Product in DB: SKU={prod.product_id}, Name={prod.product_name}, Stock={prod.stock_quantity}")
    db.close()

    print("\n[SUCCESS] ALL CHATBOT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
