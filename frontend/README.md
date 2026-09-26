<<<<<<< HEAD
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is enabled on this template. See [this documentation](https://react.dev/learn/react-compiler) for more information.

Note: This will impact Vite dev & build performances.
You can also try [the experimental native React Compiler support in plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md#rust-react-compiler) by using `compiler: true` in the plugin options instead of using the Babel plugin.

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
=======
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
>>>>>>> a80834cfe82b2512cb30b114c8a84d9ab03ef89c
