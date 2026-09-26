# This document contains the step by step process carried out to set up the backend folder

## Step 1: create virtual environment

- Created virtual environment using uv
- To use this project's venv use the following command:
        uv init
            (if uv not present, type: "pip install uv")
        uv sync
        
        To activate:
            For windows:
                .venv\Scripts\activate
            For Linux:
                source .venv/bin/activate

## Step 2: database and env setup

- Installed packages:
        uv add fastapi "uvicorn[standard]" sqlalchemy psycopg2-binary python-dotenv

- Added `.env` and `.env.example`:
        DATABASE_URL= set_your_url_here
        SECRET_KEY=stocksense_secret_key_123

- Created `app/database.py` with SQLAlchemy connection and session handling.
- Created `app/main.py` for FastAPI server entry point.

## Step 3: remote database connection

- Configured remote PostgreSQL server hosted on GCP (`35.206.93.73:5433`).
- Tested and verified database connection via SQLAlchemy:
        PostgreSQL 16.15 on x86_64-pc-linux-gnu

## Step 4: backend folder restructuring

- Removed unnecessary micro-boilerplate folders (api, core, services).
- Established clean, flat architecture:
        app/
        ├── database.py
        ├── models.py
        ├── schemas.py
        ├── auth.py
        ├── routers/
        │   ├── auth.py
        │   ├── products.py
        │   ├── warehouses.py
        │   ├── operations.py
        │   ├── moves.py
        │   └── dashboard.py
        └── main.py

## Step 5: dataset analysis and mock field enrichment

- Downloaded primary dataset: `docs/Grocery_Inventory_and_Sales_Dataset.csv` (990 items).
- Enriched dataset with missing inventory attributes while preserving original columns:
        - Unit_of_Measure (kg, liters, units, dozen)
        - Warehouse_Name (Main Warehouse, East Distribution Center, North Cold Storage)
        - Warehouse_Code (WH-MAIN, WH-EAST, WH-NORTH)
        - Rack_Location (Rack-A1, Rack-A2, Rack-B1, Cold-Room-1, etc.)
- Shifted all historical dates (`Date_Received`, `Last_Order_Date`, `Expiration_Date`) to recent active years (2026 / 2027).

## Step 6: generated relational operational datasets

- Created generator script: `docs/generate_mock_data.py`
- Generated mock datasets for relational ERP workflows based on the primary dataset:
        - `docs/users.csv`: Seed accounts (Admin, Inventory Manager, Warehouse Staff)
        - `docs/warehouses.csv`: Master warehouses (Chicago, New York, Minneapolis)
        - `docs/receipts.csv`: Incoming stock transactions (150 records)
        - `docs/deliveries.csv`: Outgoing customer shipments (150 records)
        - `docs/transfers.csv`: Internal movements between locations (80 records)
        - `docs/adjustments.csv`: Physical count audit records (50 records)
        - `docs/move_history.csv`: Immutable Stock Ledger audit log (370 entries)
- Planned PDF document generation endpoint for Receipts and Delivery slips.

## Step 7: database models and table schema definition

Created SQLAlchemy models in `app/models.py` for all 8 database tables:

1. **`users`**
   - `id` (Integer, Primary Key)
   - `user_id` (String, Unique, e.g. USR-001)
   - `name` (String)
   - `email` (String, Unique)
   - `password_hash` (String)
   - `role` (String: Admin, Inventory Manager, Warehouse Staff)
   - `reset_otp` (String, Nullable)
   - `otp_expiry` (DateTime, Nullable)
   - `created_at` (DateTime)

2. **`warehouses`**
   - `id` (Integer, Primary Key)
   - `warehouse_id` (String, Unique, e.g. WH-001)
   - `warehouse_name` (String)
   - `city` (String)
   - `capacity` (Integer)

3. **`products`**
   - `id` (Integer, Primary Key)
   - `product_id` (String, Unique SKU, e.g. 29-205-1132)
   - `product_name` (String)
   - `category` (String)
   - `supplier_id` (String)
   - `supplier_name` (String)
   - `stock_quantity` (Integer)
   - `reorder_level` (Integer)
   - `reorder_quantity` (Integer)
   - `unit_price` (Float)
   - `unit_of_measure` (String)
   - `date_received` (String)
   - `last_order_date` (String)
   - `expiration_date` (String)
   - `warehouse_location` (String)
   - `warehouse_name` (String)
   - `warehouse_code` (String)
   - `rack_location` (String)
   - `sales_volume` (Integer)
   - `inventory_turnover_rate` (Float)
   - `status` (String: Active, Backordered, Discontinued)

4. **`receipts`**
   - `id` (Integer, Primary Key)
   - `receipt_id` (String, Unique, e.g. REC-2026001)
   - `supplier_id` (String)
   - `product_id` (String, ForeignKey -> products.product_id)
   - `quantity_received` (Integer)
   - `receipt_date` (String)
   - `status` (String: Draft, Waiting, Ready, Done, Canceled)

5. **`deliveries`**
   - `id` (Integer, Primary Key)
   - `delivery_id` (String, Unique, e.g. DEL-2026001)
   - `product_id` (String, ForeignKey -> products.product_id)
   - `quantity_delivered` (Integer)
   - `delivery_date` (String)
   - `customer_name` (String)
   - `status` (String: Draft, Waiting, Ready, Done, Canceled)

6. **`transfers`**
   - `id` (Integer, Primary Key)
   - `transfer_id` (String, Unique, e.g. TRF-2026001)
   - `product_id` (String, ForeignKey -> products.product_id)
   - `from_location` (String)
   - `to_location` (String)
   - `quantity_transferred` (Integer)
   - `transfer_date` (String)
   - `status` (String: Draft, Ready, Done, Canceled)

7. **`adjustments`**
   - `id` (Integer, Primary Key)
   - `adjustment_id` (String, Unique, e.g. ADJ-2026001)
   - `product_id` (String, ForeignKey -> products.product_id)
   - `recorded_quantity` (Integer)
   - `counted_quantity` (Integer)
   - `adjustment_reason` (Text)
   - `adjustment_date` (String)

8. **`move_history` (Stock Ledger)**
   - `id` (Integer, Primary Key)
   - `move_id` (String, Unique, e.g. MOV-2026001)
   - `product_id` (String, ForeignKey -> products.product_id)
   - `movement_type` (String: Receipt, Delivery, Transfer, Adjustment)
   - `from_location` (String)
   - `to_location` (String)
   - `quantity` (Integer)
   - `timestamp` (String)
   - `reference_id` (String)

## Step 8: database seeding execution

- Created `seed.py` using batch bulk inserts (`db.bulk_save_objects`) for high performance over remote GCP network connection.
- Executed seed script:
        uv run python seed.py
- Seed Results:
        - Users: 4 seeded
        - Warehouses: 3 seeded
        - Products: 990 seeded
        - Receipts: 150 seeded
        - Deliveries: 150 seeded
        - Internal Transfers: 80 seeded
        - Stock Adjustments: 50 seeded
        - Stock Ledger (Move History): 370 seeded
