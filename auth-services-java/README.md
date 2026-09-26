# StockSense Authentication Microservice (Java 21 / Spring Boot 4)

Enterprise-grade, high-performance authentication microservice for the **StockSense Intelligent Inventory Management System**. Provides secure user onboarding, authentication, OTP password recovery, stateless JWT authorization, and seamless cross-service communication with the Python Inventory Backend and web frontends.

---

## 🌟 Key Features

- **Java 21 & Spring Boot 4**: Built on modern virtual threads and Jakarta EE standards.
- **Ultra-Lean Architecture**: 5-file consolidated codebase operating on a single high-performance PostgreSQL `users` table.
- **RFC 7519 Stateless JWT Engine**: High-entropy 256-bit HMAC-SHA256 tokens (24-hour expiration) enabling instant cross-service verification.
- **Hardened Cryptography**: BCrypt work factor 12 password hashing with salting.
- **Zero-Exposure Secrets Management**: Database credentials and secret keys are externalized through git-ignored `.env` and environment variables—never committed or baked into images.
- **3-Step OTP Password Reset**: Rate-limited 6-digit OTP verification with disk-persisted crash resilience.
- **Defense in Depth**:
  - IP-based rate limiting on sensitive authentication endpoints.
  - Automatic account lockout after 5 consecutive failed login attempts (with immediate unlock via OTP reset).
  - Configurable CORS whitelist for modern frontend development servers.
- **Dual Deployment Ready**: Seamless execution locally via Maven, within multi-stage Docker containers, or via Docker Compose.

---

## 📁 Repository Structure

```
auth-services-java/
├── Dockerfile                             # Multi-stage production container build (Alpine JRE)
├── docker-compose.yml                     # Single-command container deployment with .env injection
├── .env.example                           # Clean credentials template (safe for git)
├── .env                                   # Git-ignored local secrets (never committed)
├── .gitignore / .dockerignore             # Strict rules preventing secret leaks
├── pom.xml                                # Maven build descriptor
├── run_frontend_simulation_tests.py       # 20/20 comprehensive E2E frontend simulation suite
│
├── frontend-integration/
│   ├── authService.js                     # Drop-in JavaScript SDK for React/Vue/Vite/Next.js
│   └── authService.d.ts                   # Complete TypeScript declarations
│
├── src/main/java/com/example/stocksense/
│   ├── StocksenseAuthApplication.java     # Spring Boot application bootstrap
│   ├── User.java                          # JPA User entity (table: users)
│   ├── SecurityConfig.java                # Spring Security filter chain, JWT & rate limiter
│   ├── AuthService.java                   # Core auth logic, BCrypt & OTP management
│   └── AuthController.java                # REST endpoints, DTO records & exception handler
│
├── src/main/resources/
│   ├── application.properties             # Production config (environment variable bindings)
│   ├── application-local.properties       # Zero-dependency local H2 in-memory profile
│   └── schema.sql                         # PostgreSQL DDL table definition
│
└── Documentation Guides:
    ├── API_DOCS_FOR_FRONTEND.md           # Exact REST API contracts & sample JSON payloads
    ├── FRONTEND_INTEGRATION_README.md     # Step-by-step frontend integration guide
    └── PYTHON_INVENTORY_BACKEND_INTEGRATION.md # Guide for Python inventory backend
```

---

## 🔒 Secrets & Credentials Handling

**No database passwords or secret keys are hardcoded in the codebase.**

### 1. Initial Setup
Copy the template to create your local `.env`:
```bash
cp .env.example .env
```

### 2. Configure Your `.env` File
```env
# Database Credentials
DB_URL=jdbc:postgresql://localhost:5433/stocksense_db
DB_USERNAME=stocksense_user
DB_PASSWORD=your_secure_password_here

# JWT Secret Key (Minimum 256 bits / 32 characters)
JWT_SECRET=StockSenseProductionSecureSecretKeyMinimum256BitsLongForHmacSha256!
JWT_EXPIRATION_SECONDS=86400

# Server Port & Frontend Integration
PORT=8081
INVENTORY_DASHBOARD_URL=http://localhost:8000/dashboard
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000
```

> **Security Guarantee**: `.env` and `.env.*` are explicitly listed in both `.gitignore` and `.dockerignore`. Secrets are never committed to version control and never baked into Docker image layers.

---

## 🚀 How to Run

### Method 1: Docker Compose (Recommended)
Docker Compose automatically loads `.env` and mounts network access to PostgreSQL running on the host machine:

```bash
# Build and start container in the background
docker compose up -d --build

# View real-time logs
docker compose logs -f

# Stop container
docker compose down
```

### Method 2: Standalone Docker
Build and run using `--env-file`:

```bash
# 1. Build the lightweight production image
docker build -t stocksense-auth-service:latest .

# 2. Run container passing secrets via .env
docker run -d \
  --name stocksense-auth \
  --env-file .env \
  -p 8081:8081 \
  stocksense-auth-service:latest
```

### Method 3: Local Development with Maven
To run directly on your host machine against PostgreSQL:

```bash
# Export .env variables into your shell session:
export $(cat .env | grep -v '^#' | xargs)

# Start Spring Boot:
./mvnw spring-boot:run
```

To run offline without PostgreSQL (using in-memory H2):
```bash
./mvnw spring-boot:run -Dspring-boot.run.profiles=local
```

---

## 📡 REST API Reference

Base URL: `http://localhost:8081/api/v1/auth`

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/register` | Public | Register new user; returns JWT token & `dashboardUrl` |
| `POST` | `/login` | Public | Authenticate with username/email & password |
| `POST` | `/logout` | Public | Stateless logout signal |
| `POST` | `/forgot-password` | Public | Dispatch 6-digit verification OTP to email |
| `POST` | `/verify-otp` | Public | Verify OTP code; returns temporary single-use `resetToken` |
| `POST` | `/reset-password` | Public | Update password using `resetToken` |
| `GET` | `/me` | Bearer Token | Retrieve currently authenticated user profile |
| `GET` | `/health` | Public | Service health and operational status check |

For complete request/response schemas, see [`API_DOCS_FOR_FRONTEND.md`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/API_DOCS_FOR_FRONTEND.md).

---

## 💻 Frontend Integration

Drop [`frontend-integration/authService.js`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/frontend-integration/authService.js) into your React, Vue, Vite, or Next.js app:

```javascript
import StockSenseAuth from './services/authService';

// Login & redirect to Python Inventory Dashboard
const data = await StockSenseAuth.login({
  usernameOrEmail: "warehouse_staff",
  password: "Password123@"
});
window.location.href = data.redirectUrl;

// Authenticated API call to Python Backend (token automatically attached)
const res = await StockSenseAuth.authFetch('http://localhost:8000/api/v1/inventory/items');
```

Full instructions and code examples are available in [`FRONTEND_INTEGRATION_README.md`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/FRONTEND_INTEGRATION_README.md).

---

## 🐍 Python Inventory Backend Integration

The Python backend (FastAPI / Flask / Django) can verify incoming requests in two ways:
1. **Locally (Recommended)**: Verify the HMAC-SHA256 JWT signature using PyJWT and the shared `JWT_SECRET`.
2. **Via Auth Service**: Introspect requests by calling `GET http://localhost:8081/api/v1/auth/me` with `Authorization: Bearer <token>`.

See [`PYTHON_INVENTORY_BACKEND_INTEGRATION.md`](file:///Users/kabil/Desktop/Projects/odoo_hackathon/odoo_stocksense/auth-services-java/PYTHON_INVENTORY_BACKEND_INTEGRATION.md) for ready-to-copy Python decorators.

---

## 🧪 Testing & Quality Assurance

### 1. Automated Unit & Integration Tests
```bash
./mvnw test
```
*Executes unit and controller slice tests against in-memory H2 database (`BUILD SUCCESS`).*

### 2. Comprehensive Frontend E2E Simulation Suite
```bash
python3 run_frontend_simulation_tests.py
```
*Simulates 20 real-world frontend interactions (registration, login, brute-force locking, OTP lifecycle, token authorization, CORS, and password updates) against the live service.*
