# import csv
# import os
# import sys
# from pathlib import Path

# # Add backend directory to sys.path
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# from app.database import engine, SessionLocal, Base
# from app.models import User, Warehouse, Product, Receipt, Delivery, Transfer, Adjustment, MoveHistory

# # Project root directory
# ROOT_DIR = Path(__file__).resolve().parent.parent
# DOCS_DIR = ROOT_DIR / "docs"

# def clean_price(val: str) -> float:
#     if not val:
#         return 0.0
#     val = val.replace("$", "").replace(",", "").strip()
#     try:
#         return float(val)
#     except ValueError:
#         return 0.0

# def clean_int(val: str, default: int = 0) -> int:
#     if not val:
#         return default
#     try:
#         return int(float(val.strip()))
#     except ValueError:
#         return default

# def clean_float(val: str, default: float = 0.0) -> float:
#     if not val:
#         return default
#     try:
#         return float(val.strip())
#     except ValueError:
#         return default

# def seed_database():
#     print("[1/9] Initializing Database Tables in PostgreSQL...")
#     Base.metadata.create_all(bind=engine)
#     print("      Tables created successfully.")

#     db = SessionLocal()

#     try:
#         # 1. SEED USERS
#         users_file = DOCS_DIR / "users.csv"
#         if users_file.exists():
#             print("[2/9] Seeding Users...")
#             existing_user_ids = {u.user_id for u in db.query(User.user_id).all()}
#             users_to_add = []
#             with open(users_file, "r", encoding="utf-8") as f:
#                 for row in csv.DictReader(f):
#                     if row["user_id"] not in existing_user_ids:
#                         users_to_add.append(User(
#                             user_id=row["user_id"],
#                             name=row["name"],
#                             email=row["email"],
#                             password_hash=row["password_hash"],
#                             role=row["role"]
#                         ))
#             if users_to_add:
#                 db.bulk_save_objects(users_to_add)
#                 db.commit()
#             print(f"      Users seeded ({len(users_to_add)} added).")

#         # 2. SEED WAREHOUSES
#         warehouses_file = DOCS_DIR / "warehouses.csv"
#         if warehouses_file.exists():
#             print("[3/9] Seeding Warehouses...")
#             existing_wh_ids = {w.warehouse_id for w in db.query(Warehouse.warehouse_id).all()}
#             wh_to_add = []
#             with open(warehouses_file, "r", encoding="utf-8") as f:
#                 for row in csv.DictReader(f):
#                     if row["warehouse_id"] not in existing_wh_ids:
#                         wh_to_add.append(Warehouse(
#                             warehouse_id=row["warehouse_id"],
#                             warehouse_name=row["warehouse_name"],
#                             city=row["city"],
#                             capacity=clean_int(row.get("capacity"), 10000)
#                         ))
#             if wh_to_add:
#                 db.bulk_save_objects(wh_to_add)
#                 db.commit()
#             print(f"      Warehouses seeded ({len(wh_to_add)} added).")

#         # 3. SEED PRODUCTS
#         products_file = DOCS_DIR / "Grocery_Inventory_and_Sales_Dataset.csv"
#         if products_file.exists():
#             print("[4/9] Seeding Products (Batch mode)...")
#             existing_pids = {p.product_id for p in db.query(Product.product_id).all()}
#             products_to_add = []
#             seen = set()
#             with open(products_file, "r", encoding="utf-8") as f:
#                 for row in csv.DictReader(f):
#                     pid = row.get("Product_ID")
#                     if pid and pid not in existing_pids and pid not in seen:
#                         seen.add(pid)
#                         products_to_add.append(Product(
#                             product_id=pid,
#                             product_name=row.get("Product_Name", "").strip(),
#                             category=row.get("Catagory", "").strip(),
#                             supplier_id=row.get("Supplier_ID", "").strip(),
#                             supplier_name=row.get("Supplier_Name", "").strip(),
#                             stock_quantity=clean_int(row.get("Stock_Quantity")),
#                             reorder_level=clean_int(row.get("Reorder_Level"), 10),
#                             reorder_quantity=clean_int(row.get("Reorder_Quantity"), 50),
#                             unit_price=clean_price(row.get("Unit_Price")),
#                             unit_of_measure=row.get("Unit_of_Measure", "units"),
#                             date_received=row.get("Date_Received", ""),
#                             last_order_date=row.get("Last_Order_Date", ""),
#                             expiration_date=row.get("Expiration_Date", ""),
#                             warehouse_location=row.get("Warehouse_Location", ""),
#                             warehouse_name=row.get("Warehouse_Name", ""),
#                             warehouse_code=row.get("Warehouse_Code", ""),
#                             rack_location=row.get("Rack_Location", ""),
#                             sales_volume=clean_int(row.get("Sales_Volume")),
#                             inventory_turnover_rate=clean_float(row.get("Inventory_Turnover_Rate")),
#                             status=row.get("Status", "Active")
#                         ))
#             if products_to_add:
#                 db.bulk_save_objects(products_to_add)
#                 db.commit()
#             print(f"      Products seeded ({len(products_to_add)} added).")

#         # 4. SEED RECEIPTS
#         receipts_file = DOCS_DIR / "receipts.csv"
#         if receipts_file.exists():
#             print("[5/9] Seeding Receipts...")
#             existing_rids = {r.receipt_id for r in db.query(Receipt.receipt_id).all()}
#             receipts_to_add = []
#             with open(receipts_file, "r", encoding="utf-8") as f:
#                 for row in csv.DictReader(f):
#                     rid = row.get("receipt_id")
#                     if rid and rid not in existing_rids:
#                         receipts_to_add.append(Receipt(
#                             receipt_id=rid,
#                             supplier_id=row.get("supplier_id", ""),
#                             product_id=row.get("product_id", ""),
#                             quantity_received=clean_int(row.get("quantity_received")),
#                             receipt_date=row.get("receipt_date", ""),
#                             status=row.get("status", "Draft")
#                         ))
#             if receipts_to_add:
#                 db.bulk_save_objects(receipts_to_add)
#                 db.commit()
#             print(f"      Receipts seeded ({len(receipts_to_add)} added).")

#         # 5. SEED DELIVERIES
#         deliveries_file = DOCS_DIR / "deliveries.csv"
#         if deliveries_file.exists():
#             print("[6/9] Seeding Deliveries...")
#             existing_dids = {d.delivery_id for d in db.query(Delivery.delivery_id).all()}
#             deliveries_to_add = []
#             with open(deliveries_file, "r", encoding="utf-8") as f:
#                 for row in csv.DictReader(f):
#                     did = row.get("delivery_id")
#                     if did and did not in existing_dids:
#                         deliveries_to_add.append(Delivery(
#                             delivery_id=did,
#                             product_id=row.get("product_id", ""),
#                             quantity_delivered=clean_int(row.get("quantity_delivered")),
#                             delivery_date=row.get("delivery_date", ""),
#                             customer_name=row.get("customer_name", ""),
#                             status=row.get("status", "Draft")
#                         ))
#             if deliveries_to_add:
#                 db.bulk_save_objects(deliveries_to_add)
#                 db.commit()
#             print(f"      Deliveries seeded ({len(deliveries_to_add)} added).")

#         # 6. SEED TRANSFERS
#         transfers_file = DOCS_DIR / "transfers.csv"
#         if transfers_file.exists():
#             print("[7/9] Seeding Internal Transfers...")
#             existing_tids = {t.transfer_id for t in db.query(Transfer.transfer_id).all()}
#             transfers_to_add = []
#             with open(transfers_file, "r", encoding="utf-8") as f:
#                 for row in csv.DictReader(f):
#                     tid = row.get("transfer_id")
#                     if tid and tid not in existing_tids:
#                         transfers_to_add.append(Transfer(
#                             transfer_id=tid,
#                             product_id=row.get("product_id", ""),
#                             from_location=row.get("from_location", ""),
#                             to_location=row.get("to_location", ""),
#                             quantity_transferred=clean_int(row.get("quantity_transferred")),
#                             transfer_date=row.get("transfer_date", ""),
#                             status=row.get("status", "Draft")
#                         ))
#             if transfers_to_add:
#                 db.bulk_save_objects(transfers_to_add)
#                 db.commit()
#             print(f"      Internal Transfers seeded ({len(transfers_to_add)} added).")

#         # 7. SEED ADJUSTMENTS
#         adjustments_file = DOCS_DIR / "adjustments.csv"
#         if adjustments_file.exists():
#             print("[8/9] Seeding Stock Adjustments...")
#             existing_aids = {a.adjustment_id for a in db.query(Adjustment.adjustment_id).all()}
#             adjustments_to_add = []
#             with open(adjustments_file, "r", encoding="utf-8") as f:
#                 for row in csv.DictReader(f):
#                     aid = row.get("adjustment_id")
#                     if aid and aid not in existing_aids:
#                         adjustments_to_add.append(Adjustment(
#                             adjustment_id=aid,
#                             product_id=row.get("product_id", ""),
#                             recorded_quantity=clean_int(row.get("recorded_quantity")),
#                             counted_quantity=clean_int(row.get("counted_quantity")),
#                             adjustment_reason=row.get("adjustment_reason", ""),
#                             adjustment_date=row.get("adjustment_date", "")
#                         ))
#             if adjustments_to_add:
#                 db.bulk_save_objects(adjustments_to_add)
#                 db.commit()
#             print(f"      Stock Adjustments seeded ({len(adjustments_to_add)} added).")

#         # 8. SEED MOVE HISTORY (STOCK LEDGER)
#         moves_file = DOCS_DIR / "move_history.csv"
#         if moves_file.exists():
#             print("[9/9] Seeding Stock Ledger (Move History)...")
#             existing_mids = {m.move_id for m in db.query(MoveHistory.move_id).all()}
#             moves_to_add = []
#             with open(moves_file, "r", encoding="utf-8") as f:
#                 for row in csv.DictReader(f):
#                     mid = row.get("move_id")
#                     if mid and mid not in existing_mids:
#                         moves_to_add.append(MoveHistory(
#                             move_id=mid,
#                             product_id=row.get("product_id", ""),
#                             movement_type=row.get("movement_type", ""),
#                             from_location=row.get("from_location", ""),
#                             to_location=row.get("to_location", ""),
#                             quantity=clean_int(row.get("quantity")),
#                             timestamp=row.get("timestamp", ""),
#                             reference_id=row.get("reference_id", "")
#                         ))
#             if moves_to_add:
#                 db.bulk_save_objects(moves_to_add)
#                 db.commit()
#             print(f"      Move History seeded ({len(moves_to_add)} added).")

#         print("\nSUCCESS: All tables created and seeded into PostgreSQL!")

#     except Exception as e:
#         db.rollback()
#         print(f"Error during seeding: {e}")
#         raise e
#     finally:
#         db.close()

# if __name__ == "__main__":
#     seed_database()


