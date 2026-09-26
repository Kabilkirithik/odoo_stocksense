import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User, Warehouse, Product, Receipt, Delivery, Transfer, Adjustment, MoveHistory

def check_database():
    db = SessionLocal()
    tables = [
        ("users", User),
        ("warehouses", Warehouse),
        ("products", Product),
        ("receipts", Receipt),
        ("deliveries", Delivery),
        ("transfers", Transfer),
        ("adjustments", Adjustment),
        ("move_history", MoveHistory)
    ]

    print("=======================================================")
    print(f"{'TABLE NAME':<20} | {'ROW COUNT':<12} | {'STATUS'}")
    print("=======================================================")
    
    total_records = 0
    for name, model in tables:
        count = db.query(model).count()
        total_records += count
        status = "OK" if count > 0 else "EMPTY"
        print(f"{name:<20} | {count:<12} | {status}")

    print("=======================================================")
    print(f"Total Records Across Database: {total_records}")
    print("=======================================================")

    u = db.query(User).first()
    p = db.query(Product).first()
    r = db.query(Receipt).first()
    d = db.query(Delivery).first()
    m = db.query(MoveHistory).first()

    print("\n--- SAMPLE DATA VERIFICATION ---")
    if u:
        print(f"User:        {u.user_id} - {u.email} ({u.role})")
    if p:
        print(f"Product:     {p.product_id} - {p.product_name} [{p.category}] (Stock: {p.stock_quantity} {p.unit_of_measure})")
    if r:
        print(f"Receipt:     {r.receipt_id} -> Product: {r.product_id} (Qty: {r.quantity_received}, Status: {r.status})")
    if d:
        print(f"Delivery:    {d.delivery_id} -> Customer: {d.customer_name} (Qty: {d.quantity_delivered}, Status: {d.status})")
    if m:
        print(f"Move Ledger: {m.move_id} -> Type: {m.movement_type} (From: {m.from_location} To: {m.to_location})")

    db.close()

if __name__ == "__main__":
    check_database()
