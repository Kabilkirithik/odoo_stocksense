# StockSense

StockSense is a production-style Inventory Management System built to replace manual stock tracking with a simple, centralized web application. The idea is to make everyday warehouse operations,receiving products, delivering orders, moving stock between locations, and adjusting inventory,easy to manage while keeping a complete history of every stock movement.

## Our Approach

Instead of building this as a basic CRUD project, we planned it like a real-world ERP system with a modular architecture.

* **React + Vite** for a fast and responsive frontend.
* **FastAPI** as the backend for clean REST APIs.
* **PostgreSQL** to maintain reliable inventory relationships.
* **Prometheus + Grafana** to monitor both system health and business metrics like low-stock items, deliveries, and API performance.
* **Docker** to run the entire application as a single stack.

The core workflow follows a real warehouse process:

1. Products are received from suppliers.
2. Stock is stored in warehouses and specific locations.
3. Items can be transferred between locations.
4. Deliveries reduce stock automatically.
5. Every operation is recorded in a stock ledger for traceability.

The goal is to create an inventory system that feels production-ready—not just in functionality, but also in architecture, monitoring, and deployment.

# Folder Structure

stocksense/
│
├── frontend/
├── backend/
├── monitoring/
├── docs/
│
├── .env.example
├── .gitignore
└── README.md