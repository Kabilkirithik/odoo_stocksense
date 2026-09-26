import time
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Product, Receipt, Delivery, Transfer, Warehouse, MoveHistory

# --- System & HTTP Metrics ---
HTTP_REQUESTS_TOTAL = Counter(
    "stocksense_http_requests_total",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "stocksense_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# --- Inventory & Business Metrics ---
TOTAL_PRODUCTS = Gauge(
    "stocksense_total_products",
    "Total number of products in catalog"
)

TOTAL_STOCK_UNITS = Gauge(
    "stocksense_total_stock_units",
    "Total quantity of stock across all products"
)

LOW_STOCK_PRODUCTS = Gauge(
    "stocksense_low_stock_products",
    "Number of products with stock at or below min reorder point"
)

OUT_OF_STOCK_PRODUCTS = Gauge(
    "stocksense_out_of_stock_products",
    "Number of products completely out of stock (quantity = 0)"
)

PENDING_RECEIPTS = Gauge(
    "stocksense_pending_receipts",
    "Number of incoming receipts in Draft or Ready status"
)

PENDING_DELIVERIES = Gauge(
    "stocksense_pending_deliveries",
    "Number of outgoing deliveries in Draft or Ready status"
)

PENDING_TRANSFERS = Gauge(
    "stocksense_pending_transfers",
    "Number of internal transfers in Draft or Ready status"
)

TOTAL_WAREHOUSES = Gauge(
    "stocksense_total_warehouses",
    "Total number of configured warehouses"
)

INVENTORY_MOVES_TOTAL = Counter(
    "stocksense_inventory_moves_total",
    "Total stock movement transactions logged",
    ["action_type"]
)


def update_business_metrics():
    """Query database and update gauge values on scrape."""
    db = SessionLocal()
    try:
        # Total products & stock units
        prod_stats = db.query(
            func.count(Product.id),
            func.coalesce(func.sum(Product.stock_quantity), 0)
        ).filter(Product.status == "Active").first()
        
        TOTAL_PRODUCTS.set(prod_stats[0] or 0)
        TOTAL_STOCK_UNITS.set(float(prod_stats[1] or 0))

        # Low stock & Out of stock
        low_stock_count = db.query(func.count(Product.id)).filter(
            Product.status == "Active",
            Product.stock_quantity <= Product.reorder_level,
            Product.stock_quantity > 0
        ).scalar() or 0
        LOW_STOCK_PRODUCTS.set(low_stock_count)

        out_of_stock_count = db.query(func.count(Product.id)).filter(
            Product.status == "Active",
            Product.stock_quantity == 0
        ).scalar() or 0
        OUT_OF_STOCK_PRODUCTS.set(out_of_stock_count)

        # Pending operations
        pending_rec = db.query(func.count(Receipt.id)).filter(
            Receipt.status.in_(["Draft", "Ready"])
        ).scalar() or 0
        PENDING_RECEIPTS.set(pending_rec)

        pending_del = db.query(func.count(Delivery.id)).filter(
            Delivery.status.in_(["Draft", "Ready"])
        ).scalar() or 0
        PENDING_DELIVERIES.set(pending_del)

        pending_tra = db.query(func.count(Transfer.id)).filter(
            Transfer.status.in_(["Draft", "Ready"])
        ).scalar() or 0
        PENDING_TRANSFERS.set(pending_tra)

        # Warehouses
        wh_count = db.query(func.count(Warehouse.id)).scalar() or 0
        TOTAL_WAREHOUSES.set(wh_count)

    except Exception as e:
        print(f"Error collecting Prometheus business metrics: {e}")
    finally:
        db.close()


async def prometheus_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Normalize endpoint path for metric labels to prevent high cardinality
    path = request.url.path
    # Group parameterized IDs if needed, otherwise route path
    if request.scope.get("route"):
        endpoint = request.scope["route"].path
    else:
        endpoint = path

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=response.status_code
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)

    return response


def metrics_endpoint():
    update_business_metrics()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
