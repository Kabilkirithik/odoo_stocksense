# Backend File Guide

This document explains the purpose of each file in the `backend` folder. The project follows a modular FastAPI structure where each feature has its own API routes, database models, validation schemas, and business logic.

---

# Backend Structure

```text id="46w5eq"
backend/
│
├── app/
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── core/
│   ├── database.py
│   └── main.py
│
├── requirements.txt
├── Dockerfile
└── .env
```

---

# `main.py`

**Purpose:** Entry point of the FastAPI application.

Responsibilities:

* Creates the FastAPI app.
* Registers all API routes.
* Enables middleware such as CORS.
* Exposes the `/metrics` endpoint for Prometheus.

Think of this as the application's starting point.

---

# `database.py`

**Purpose:** Connects the backend to PostgreSQL.

Responsibilities:

* Creates the SQLAlchemy database engine.
* Creates database sessions.
* Provides reusable database connections for API routes.

Every module accesses the database through this file.

---

# API Folder (`app/api/`)

This folder contains the REST API endpoints. Each file handles one feature.

## `auth.py`

Handles user authentication.

Endpoints:

* Register
* Login
* Forgot Password

---

## `dashboard.py`

Returns dashboard data.

Examples:

* Total Products
* Low Stock
* Pending Deliveries
* Recent Activities

Instead of calculating everything in the frontend, this file sends ready-to-use dashboard data.

---

## `products.py`

Manages product-related operations.

Responsibilities:

* Create Product
* Update Product
* Delete Product
* Search Products

---

## `receipts.py`

Handles incoming stock.

Workflow:

* Create receipt
* Validate receipt
* Increase inventory automatically

---

## `deliveries.py`

Handles outgoing shipments.

Workflow:

* Create delivery
* Validate delivery
* Reduce inventory automatically

---

## `transfers.py`

Moves stock between warehouses or locations.

Example:

* Main Warehouse → Rack A

Stock quantity remains the same overall while the location changes.

---

## `adjustments.py`

Corrects inventory after physical counting.

Example:

Expected:

```text id="jlwmg2"
50
```

Actual:

```text id="0g1hpl"
47
```

Difference:

```text id="v3s6qq"
-3
```

The adjustment is recorded in the stock history.

---

## `warehouse.py`

Manages warehouses and storage locations.

Responsibilities:

* Create Warehouse
* Manage Locations
* View available stock per warehouse

---

## `move_history.py`

Displays the complete stock movement history.

Every inventory operation appears here, making it the audit trail of the application.

---

# Models Folder (`app/models/`)

These files define the database tables using SQLAlchemy.

## `user.py`

Stores:

* User information
* Email
* Password hash

---

## `product.py`

Stores:

* Product name
* SKU
* Category
* Unit
* Reorder level

---

## `warehouse.py`

Stores warehouse information.

Example:

* Main Warehouse
* Warehouse 2

---

## `stock.py`

Tracks current stock.

This table always contains the latest inventory quantity for each product and location.

---

## `receipt.py`

Stores incoming stock transactions.

---

## `delivery.py`

Stores outgoing delivery records.

---

## `transfer.py`

Stores internal warehouse transfers.

---

## `adjustment.py`

Stores stock correction records.

---

## `move_history.py`

Stores every inventory movement.

Examples:

* Receipt
* Delivery
* Transfer
* Adjustment

Unlike `stock.py`, this table never overwrites previous records.

---

# Schemas Folder (`app/schemas/`)

These files contain Pydantic models used for request validation and API responses.

## `auth.py`

Validates:

* Login requests
* Registration requests

---

## `product.py`

Validates product creation and updates.

---

## `warehouse.py`

Validates warehouse data.

---

## `receipt.py`

Validates receipt requests.

---

## `delivery.py`

Validates delivery requests.

---

## `transfer.py`

Validates transfer requests.

---

## `adjustment.py`

Validates inventory adjustment requests.

---

## `dashboard.py`

Defines the structure of dashboard responses.

Example:

```json id="e8x7uv"
{
  "total_products": 120,
  "low_stock": 8,
  "pending_deliveries": 5
}
```

---

# Services Folder (`app/services/`)

The service layer contains business logic. API routes should remain small and call these services.

## `auth_service.py`

Handles:

* Password hashing
* JWT token generation
* User verification

---

## `inventory_service.py`

Contains the most important business logic.

Responsibilities:

* Increase stock
* Reduce stock
* Update inventory
* Create stock history entries

Every inventory operation passes through this service.

---

## `warehouse_service.py`

Handles warehouse-specific operations.

Example:

* Move stock between locations
* Validate warehouse availability

---

## `dashboard_service.py`

Calculates dashboard statistics.

Instead of sending raw database tables, it prepares business-friendly summaries.

---

# Core Folder (`app/core/`)

Contains application-wide configuration.

## `config.py`

Loads environment variables.

Examples:

* Database URL
* JWT Secret
* Application settings

---

## `security.py`

Handles security features.

Responsibilities:

* JWT authentication
* Password verification
* Protected routes

---

## `metrics.py`

Integrates Prometheus.

Responsibilities:

* HTTP request metrics
* Response time metrics
* Custom inventory metrics
* Business monitoring

This file allows Grafana to visualize both system health and inventory activity.

---

# Root Files

## `requirements.txt`

Lists all Python dependencies.

Example packages:

* FastAPI
* Uvicorn
* SQLAlchemy
* Pydantic
* Prometheus Client

---

## `Dockerfile`

Packages the backend into a production-ready container.

Responsibilities:

* Install dependencies
* Copy application files
* Start the FastAPI server

---

## `.env`

Stores configuration values that should not be hardcoded.

Examples:

```text id="ck9vqc"
DATABASE_URL=
JWT_SECRET=
PROMETHEUS_ENABLED=
```

This file should never be committed to Git.

---

# Request Flow

A typical request moves through the backend in this order:

```text id="vwpjcc"
Frontend
   │
   ▼
API Route
   │
   ▼
Service Layer
   │
   ▼
Database Models
   │
   ▼
PostgreSQL
```

This separation keeps the project organized, makes testing easier, and allows new features to be added without turning the application into a single large `main.py` file.
