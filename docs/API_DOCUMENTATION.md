# StockSense Inventory Backend API Documentation

**Base URL:** `http://127.0.0.1:8000`  
**Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`  
**OpenAPI JSON:** `http://127.0.0.1:8000/openapi.json`

---

## Overview of Modules

| Module | Route Prefix | Description |
| :--- | :--- | :--- |
| **1. Dashboard** | `/api/dashboard` | Live KPI cards, low-stock alerts, and recent activity ledger |
| **2. Products** | `/api/products` | Product catalog CRUD, search, category & warehouse filters |
| **3. Warehouses** | `/api/warehouses` | Master warehouse list and location/rack dropdowns |
| **4. Operations** | `/api/operations` | Receipts, Deliveries, Internal Transfers, and Stock Adjustments |
| **5. Move History** | `/api/moves` | Immutable Stock Movement Ledger (Audit Log) |

---

## 1. Dashboard (`/api/dashboard`)

### `GET /api/dashboard/kpis`
Returns all aggregated KPI metrics for the top dashboard cards.

**Response (`200 OK`):**
```json
{
  "total_products": 990,
  "low_stock_items": 465,
  "pending_receipts": 20,
  "pending_deliveries": 25,
  "internal_transfers_scheduled": 15,
  "total_stock_movements": 370
}
```

### `GET /api/dashboard/activity?limit=10`
Returns the most recent stock ledger activities.

### `GET /api/dashboard/low-stock?limit=10`
Returns products where `stock_quantity <= reorder_level`.

---

## 2. Products (`/api/products`)

### `GET /api/products`
Fetch paginated products with multi-filter search.

**Query Parameters:**
* `search`: string (fuzzy search on Name, SKU, Supplier)
* `category`: string (e.g. `Grains & Pulses`, `Dairy`, `Beverages`)
* `warehouse`: string (e.g. `Main Warehouse`)
* `status`: string (`Active`, `Backordered`, `Discontinued`)
* `low_stock`: boolean (`true` to show only low-stock items)
* `skip`: int (default `0`)
* `limit`: int (default `50`)

**Response (`200 OK`):**
```json
{
  "items": [
    {
      "id": 1,
      "product_id": "29-205-1132",
      "product_name": "Sushi Rice",
      "category": "Grains & Pulses",
      "supplier_id": "38-037-1699",
      "supplier_name": "Jaxnation",
      "stock_quantity": 22,
      "reorder_level": 72,
      "reorder_quantity": 70,
      "unit_price": 4.50,
      "unit_of_measure": "kg",
      "warehouse_name": "Main Warehouse",
      "warehouse_code": "WH-MAIN",
      "rack_location": "Rack-A1",
      "status": "Active"
    }
  ],
  "total": 990
}
```

### `GET /api/products/{sku}`
Fetch a single product by SKU / Product ID.

### `GET /api/products/categories`
Returns a list of all distinct category names for filter pills.

**Response (`200 OK`):**
```json
["Bakery", "Beverages", "Dairy", "Fruits & Vegetables", "Grains & Pulses", "Oils & Fats", "Seafood"]
```

### `POST /api/products`
Create a new product.

**Body:**
```json
{
  "product_id": "PRD-NEW-01",
  "product_name": "Organic Almond Milk",
  "category": "Dairy",
  "supplier_id": "SUP-101",
  "supplier_name": "NatureFresh Ltd",
  "stock_quantity": 50,
  "reorder_level": 15,
  "reorder_quantity": 40,
  "unit_price": 3.80,
  "unit_of_measure": "liters",
  "warehouse_name": "Main Warehouse",
  "warehouse_code": "WH-MAIN",
  "rack_location": "Rack-B1",
  "status": "Active"
}
```

### `PUT /api/products/{sku}`
Update product fields (partial update supported).

### `DELETE /api/products/{sku}`
Delete a product by SKU.

---

## 3. Warehouses (`/api/warehouses`)

### `GET /api/warehouses`
List master warehouses.

**Response (`200 OK`):**
```json
{
  "items": [
    {
      "id": 1,
      "warehouse_id": "WH-001",
      "warehouse_name": "Main Central Warehouse",
      "city": "Chicago",
      "capacity": 50000
    }
  ],
  "total": 3
}
```

### `GET /api/warehouses/locations`
Returns all unique racks / storage locations for dropdown selects on operations forms.

**Response (`200 OK`):**
```json
{
  "locations": [
    "Cold-Room-1",
    "Rack-A1",
    "Rack-A2",
    "Rack-B1",
    "Rack-B2",
    "Rack-C1",
    "Rack-C2",
    "Shelf-01",
    "Shelf-02"
  ]
}
```

---

## 4. Operations (`/api/operations`)

### A. Receipts (Incoming Stock)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/operations/receipts` | List receipts (Filter by `status`, `search`, `supplier_id`, `product_id`) |
| `GET` | `/api/operations/receipts/{id}` | Single receipt detail |
| `GET` | `/api/operations/receipts/{id}/slip` | **Printable Receipt Slip (HTML/PDF)** with company header, itemized table, and signature line |
| `POST` | `/api/operations/receipts` | Create receipt in `Draft` status |
| `PUT` | `/api/operations/receipts/{id}` | Update receipt |
| `POST` | `/api/operations/receipts/{id}/ready` | Move receipt from `Draft` $\rightarrow$ `Ready` |
| `POST` | `/api/operations/receipts/{id}/validate` | **Validate Receipt**: Sets status to `Done`, **increases product stock**, and writes to `move_history` |
| `POST` | `/api/operations/receipts/{id}/cancel` | Cancel receipt |
| `DELETE`| `/api/operations/receipts/{id}` | Delete draft receipt |

**Create Receipt Body (`POST /api/operations/receipts`):**
```json
{
  "receipt_id": "REC-2026151",
  "supplier_id": "38-037-1699",
  "product_id": "29-205-1132",
  "quantity_received": 50,
  "receipt_date": "9/26/2026",
  "status": "Draft"
}
```

---

### B. Deliveries (Outgoing Stock)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/operations/deliveries` | List delivery orders |
| `GET` | `/api/operations/deliveries/{id}` | Single delivery detail |
| `GET` | `/api/operations/deliveries/{id}/slip` | **Printable Delivery Packing Slip (HTML/PDF)** with customer info, itemized table, and signature line |
| `POST` | `/api/operations/deliveries` | Create delivery order |
| `PUT` | `/api/operations/deliveries/{id}` | Update delivery order |
| `POST` | `/api/operations/deliveries/{id}/ready` | Move delivery to `Ready` |
| `POST` | `/api/operations/deliveries/{id}/validate` | **Validate Delivery**: Sets status to `Done`, **decreases product stock**, and writes to `move_history` |
| `POST` | `/api/operations/deliveries/{id}/cancel` | Cancel delivery |
| `DELETE`| `/api/operations/deliveries/{id}` | Delete delivery |

**Create Delivery Body (`POST /api/operations/deliveries`):**
```json
{
  "delivery_id": "DEL-2026151",
  "product_id": "29-205-1132",
  "quantity_delivered": 10,
  "delivery_date": "9/26/2026",
  "customer_name": "Metro Supermarkets",
  "status": "Draft"
}
```

---

### C. Internal Transfers

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/operations/transfers` | List transfers |
| `GET` | `/api/operations/transfers/{id}` | Transfer details |
| `POST` | `/api/operations/transfers` | Create transfer |
| `POST` | `/api/operations/transfers/{id}/validate` | **Validate Transfer**: Sets status to `Done`, updates product rack location, and logs to `move_history` |

**Create Transfer Body (`POST /api/operations/transfers`):**
```json
{
  "transfer_id": "TRF-2026081",
  "product_id": "29-205-1132",
  "from_location": "Rack-A1",
  "to_location": "Rack-B2",
  "quantity_transferred": 15,
  "transfer_date": "9/26/2026",
  "status": "Draft"
}
```

---

### D. Stock Adjustments (Physical Count Corrections)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/operations/adjustments` | List past adjustments |
| `POST` | `/api/operations/adjustments` | **Submit Adjustment**: Updates product physical stock to `counted_quantity` and logs the delta to `move_history` |

**Create Adjustment Body (`POST /api/operations/adjustments`):**
```json
{
  "adjustment_id": "ADJ-2026051",
  "product_id": "29-205-1132",
  "recorded_quantity": 22,
  "counted_quantity": 20,
  "adjustment_reason": "Damaged packages discarded",
  "adjustment_date": "9/26/2026"
}
```

---

### E. Suppliers Dropdown Helper
* `GET /api/operations/suppliers` $\rightarrow$ Returns all distinct vendors for receipt dropdowns.

---

## 5. Move History (Stock Ledger) (`/api/moves`)

The immutable audit trail of all receipts, deliveries, transfers, and adjustments.

### `GET /api/moves`
**Query Parameters:**
* `movement_type`: `Receipt` | `Delivery` | `Transfer` | `Adjustment`
* `product_id`: string
* `reference_id`: string (e.g. `REC-2026001`)
* `skip`: int
* `limit`: int

**Response (`200 OK`):**
```json
{
  "items": [
    {
      "id": 1,
      "move_id": "MOV-2026001",
      "product_id": "39-629-5554",
      "movement_type": "Receipt",
      "from_location": "Vendors / Supplier",
      "to_location": "Main Warehouse / Stock",
      "quantity": 17,
      "timestamp": "2/3/2026 09:30:00",
      "reference_id": "REC-2026001"
    }
  ],
  "total": 370
}
```

### `GET /api/moves/{id}`
Fetch single movement transaction.

---
