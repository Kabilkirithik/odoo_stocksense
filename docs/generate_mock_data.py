import csv
import random
import hashlib

random.seed(42)

# 1. Load products from existing CSV
products = []
with open('docs/Grocery_Inventory_and_Sales_Dataset.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        products.append(r)

print(f"Loaded {len(products)} products")

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

# 1. USERS CSV
users_data = [
    {'user_id': 'USR-001', 'name': 'nivi', 'email': 'nivi@stocksense.com', 'password_hash': hash_pw('nivi@123'), 'role': 'Admin'},
    {'user_id': 'USR-002', 'name': 'Manager', 'email': 'manager@stocksense.com', 'password_hash': hash_pw('Manager@123'), 'role': 'Inventory Manager'},
    {'user_id': 'USR-003', 'name': 'Staff1', 'email': 'staff1@stocksense.com', 'password_hash': hash_pw('Staff@123'), 'role': 'Warehouse Staff'},
    {'user_id': 'USR-004', 'name': 'Staff2', 'email': 'staff2@stocksense.com', 'password_hash': hash_pw('Staff@123'), 'role': 'Warehouse Staff'},
]
with open('docs/users.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['user_id', 'name', 'email', 'password_hash', 'role'])
    w.writeheader()
    w.writerows(users_data)

# 2. WAREHOUSES MASTER CSV
warehouses_data = [
    {'warehouse_id': 'WH-001', 'warehouse_name': 'Main Central Warehouse', 'city': 'Chicago', 'capacity': 50000},
    {'warehouse_id': 'WH-002', 'warehouse_name': 'East Distribution Center', 'city': 'New York', 'capacity': 35000},
    {'warehouse_id': 'WH-003', 'warehouse_name': 'North Cold Storage Hub', 'city': 'Minneapolis', 'capacity': 20000},
]
with open('docs/warehouses.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['warehouse_id', 'warehouse_name', 'city', 'capacity'])
    w.writeheader()
    w.writerows(warehouses_data)

# 3. RECEIPTS CSV (Incoming)
receipts_data = []
for i in range(1, 151):
    p = products[(i * 7) % len(products)]
    qty = int(p.get('Reorder_Quantity') or random.randint(20, 100))
    dt = p.get('Date_Received') or f"{random.randint(1,9)}/{random.randint(1,28)}/2026"
    status = 'Done' if i <= 130 else ('Waiting' if i <= 142 else 'Draft')
    receipts_data.append({
        'receipt_id': f'REC-{2026000 + i}',
        'supplier_id': p.get('Supplier_ID', f'SUP-{1000+i}'),
        'product_id': p.get('Product_ID'),
        'quantity_received': qty,
        'receipt_date': dt,
        'status': status
    })
with open('docs/receipts.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['receipt_id', 'supplier_id', 'product_id', 'quantity_received', 'receipt_date', 'status'])
    w.writeheader()
    w.writerows(receipts_data)

# 4. DELIVERIES CSV (Outgoing)
customers = ['Metro Supermarkets', 'Green Grocers Inc', 'Urban Fresh Market', 'Daily Needs Mart', 'QuickBite Logistics', 'Apex Retailers']
deliveries_data = []
for i in range(1, 151):
    p = products[(i * 11) % len(products)]
    qty = random.randint(5, 40)
    dt = p.get('Last_Order_Date') or f"{random.randint(1,9)}/{random.randint(1,28)}/2026"
    status = 'Done' if i <= 125 else ('Ready' if i <= 140 else 'Waiting')
    deliveries_data.append({
        'delivery_id': f'DEL-{2026000 + i}',
        'product_id': p.get('Product_ID'),
        'quantity_delivered': qty,
        'delivery_date': dt,
        'customer_name': customers[i % len(customers)],
        'status': status
    })
with open('docs/deliveries.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['delivery_id', 'product_id', 'quantity_delivered', 'delivery_date', 'customer_name', 'status'])
    w.writeheader()
    w.writerows(deliveries_data)

# 5. INTERNAL TRANSFERS CSV
locations = ['Main Store', 'Rack-A1', 'Rack-A2', 'Rack-B1', 'Rack-B2', 'Rack-C1', 'Cold-Room-1', 'Production Floor', 'Dispatch Bay']
transfers_data = []
for i in range(1, 81):
    p = products[(i * 13) % len(products)]
    from_loc = locations[i % len(locations)]
    to_loc = locations[(i + 2) % len(locations)]
    qty = random.randint(5, 30)
    dt = f"{random.randint(3,9)}/{random.randint(1,28)}/2026"
    status = 'Done' if i <= 65 else ('Ready' if i <= 75 else 'Draft')
    transfers_data.append({
        'transfer_id': f'TRF-{2026000 + i}',
        'product_id': p.get('Product_ID'),
        'from_location': from_loc,
        'to_location': to_loc,
        'quantity_transferred': qty,
        'transfer_date': dt,
        'status': status
    })
with open('docs/transfers.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['transfer_id', 'product_id', 'from_location', 'to_location', 'quantity_transferred', 'transfer_date', 'status'])
    w.writeheader()
    w.writerows(transfers_data)

# 6. STOCK ADJUSTMENTS CSV
reasons = ['Damaged goods during transit', 'Physical count discrepancy', 'Routine cycle count correction', 'Expired batch write-off', 'Found unaccounted inventory']
adjustments_data = []
for i in range(1, 51):
    p = products[(i * 17) % len(products)]
    recorded = int(p.get('Stock_Quantity') or 30)
    delta = random.choice([-5, -3, -2, -1, 1, 2, 4])
    counted = max(0, recorded + delta)
    dt = f"{random.randint(4,9)}/{random.randint(1,28)}/2026"
    adjustments_data.append({
        'adjustment_id': f'ADJ-{2026000 + i}',
        'product_id': p.get('Product_ID'),
        'recorded_quantity': recorded,
        'counted_quantity': counted,
        'adjustment_reason': reasons[i % len(reasons)],
        'adjustment_date': dt
    })
with open('docs/adjustments.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['adjustment_id', 'product_id', 'recorded_quantity', 'counted_quantity', 'adjustment_reason', 'adjustment_date'])
    w.writeheader()
    w.writerows(adjustments_data)

# 7. MOVE HISTORY (STOCK LEDGER) CSV
moves_data = []
move_counter = 1

for r in receipts_data:
    if r['status'] == 'Done':
        moves_data.append({
            'move_id': f'MOV-{2026000 + move_counter}',
            'product_id': r['product_id'],
            'movement_type': 'Receipt',
            'from_location': 'Vendors / Supplier',
            'to_location': 'Main Warehouse / Stock',
            'quantity': r['quantity_received'],
            'timestamp': f"{r['receipt_date']} 09:30:00",
            'reference_id': r['receipt_id']
        })
        move_counter += 1

for d in deliveries_data:
    if d['status'] == 'Done':
        moves_data.append({
            'move_id': f'MOV-{2026000 + move_counter}',
            'product_id': d['product_id'],
            'movement_type': 'Delivery',
            'from_location': 'Main Warehouse / Stock',
            'to_location': f"Customer: {d['customer_name']}",
            'quantity': d['quantity_delivered'],
            'timestamp': f"{d['delivery_date']} 14:15:00",
            'reference_id': d['delivery_id']
        })
        move_counter += 1

for t in transfers_data:
    if t['status'] == 'Done':
        moves_data.append({
            'move_id': f'MOV-{2026000 + move_counter}',
            'product_id': t['product_id'],
            'movement_type': 'Transfer',
            'from_location': t['from_location'],
            'to_location': t['to_location'],
            'quantity': t['quantity_transferred'],
            'timestamp': f"{t['transfer_date']} 11:00:00",
            'reference_id': t['transfer_id']
        })
        move_counter += 1

for a in adjustments_data:
    qty_diff = a['counted_quantity'] - a['recorded_quantity']
    moves_data.append({
        'move_id': f'MOV-{2026000 + move_counter}',
        'product_id': a['product_id'],
        'movement_type': 'Adjustment',
        'from_location': 'Inventory Loss / Gain' if qty_diff > 0 else 'Main Warehouse / Stock',
        'to_location': 'Main Warehouse / Stock' if qty_diff > 0 else 'Inventory Loss / Gain',
        'quantity': abs(qty_diff),
        'timestamp': f"{a['adjustment_date']} 16:45:00",
        'reference_id': a['adjustment_id']
    })
    move_counter += 1

with open('docs/move_history.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['move_id', 'product_id', 'movement_type', 'from_location', 'to_location', 'quantity', 'timestamp', 'reference_id'])
    w.writeheader()
    w.writerows(moves_data)

print(f"Successfully generated all missing datasets! Total moves in Stock Ledger: {len(moves_data)}")
