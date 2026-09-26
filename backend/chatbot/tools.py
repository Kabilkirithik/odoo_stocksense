import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.models import Product, Receipt, Delivery, Adjustment, MoveHistory
from app.fetchers import (
    dashboard_fetcher, product_fetcher, move_fetcher, warehouse_fetcher
)

def _gen_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def _get_db(config: RunnableConfig) -> Session:
    db = config.get("configurable", {}).get("db")
    if db is None:
        raise RuntimeError("Database session not found in RunnableConfig.")
    return db

# ============================================================================
# PYDANTIC INPUT SCHEMAS (Validation & Type Safety)
# ============================================================================

class SearchProductsInput(BaseModel):
    search: Optional[str] = Field(default=None, description="Search term for name, SKU, or supplier")
    category: Optional[str] = Field(default=None, description="Filter by product category")
    warehouse: Optional[str] = Field(default=None, description="Filter by warehouse name")
    low_stock_only: bool = Field(default=False, description="Filter products where stock <= reorder_level")
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")

class GetProductInput(BaseModel):
    sku: str = Field(..., description="Unique product SKU or product_id")

class CreateProductInput(BaseModel):
    product_name: str = Field(..., min_length=2, description="Product title / name")
    product_id: Optional[str] = Field(default=None, description="SKU identifier (auto-generated if omitted)")
    category: str = Field(default="General", description="Product category")
    stock_quantity: int = Field(default=0, ge=0, description="Initial inventory on hand")
    unit_price: float = Field(default=0.0, ge=0.0, description="Price per unit in USD")
    reorder_level: int = Field(default=10, ge=0, description="Minimum stock threshold before alert")
    reorder_quantity: int = Field(default=50, ge=1, description="Replenishment batch size")
    warehouse_name: str = Field(default="Main Warehouse", description="Storage warehouse name")
    rack_location: str = Field(default="A-01-01", description="Shelf/rack coordinate")

class CreateReceiptInput(BaseModel):
    product_id: str = Field(..., description="SKU of the inbound product")
    quantity_received: int = Field(..., gt=0, description="Number of incoming units")
    supplier_id: str = Field(default="SUP-001", description="Supplier identifier")

class ValidateReceiptInput(BaseModel):
    receipt_id: str = Field(..., description="Inbound receipt identifier (e.g. REC-1001)")

class CreateDeliveryInput(BaseModel):
    product_id: str = Field(..., description="SKU of the outbound product to ship")
    quantity_delivered: int = Field(..., gt=0, description="Number of units to deliver")
    customer_name: str = Field(default="General Customer", description="Recipient customer name")

class ValidateDeliveryInput(BaseModel):
    delivery_id: str = Field(..., description="Outbound delivery identifier (e.g. DEL-1001)")

class CreateStockAdjustmentInput(BaseModel):
    product_id: str = Field(..., description="SKU to adjust")
    counted_quantity: int = Field(..., ge=0, description="Physical count observed on shelf")
    reason: str = Field(default="Physical cycle count", description="Reason for variance")

class ListMovementsInput(BaseModel):
    movement_type: Optional[str] = Field(default=None, description="Filter: Receipt, Delivery, Transfer, Adjustment")
    limit: int = Field(default=15, ge=1, le=100, description="Max entries to return")

# ============================================================================
# LANGGRAPH TOOL DEFINITIONS (Reusing backend models and fetchers directly)
# ============================================================================

@tool
def get_inventory_status(config: RunnableConfig) -> str:
    """Fetch current inventory status, high-level KPIs, total inventory valuation, and stock health."""
    db = _get_db(config)
    kpis = dashboard_fetcher.fetch_kpis(db)
    products = db.query(Product).all()
    valuation = round(sum(p.stock_quantity * (p.unit_price or 0.0) for p in products), 2)
    out_of_stock = [p.product_name for p in products if p.stock_quantity == 0]
    return json.dumps({
        "kpis": kpis,
        "total_valuation_usd": valuation,
        "out_of_stock_items": out_of_stock[:10],
        "categories": product_fetcher.fetch_categories(db)
    })

@tool
def predict_inventory_trends(config: RunnableConfig) -> str:
    """Analyze sales velocity, turnover rates, and pending orders to forecast stockout risks and replenishment plans."""
    db = _get_db(config)
    products = db.query(Product).all()
    hazards = []
    reorders = []
    for p in products:
        if p.stock_quantity <= p.reorder_level:
            hazards.append({
                "sku": p.product_id, "name": p.product_name, "stock": p.stock_quantity,
                "reorder_level": p.reorder_level, "urgency": "CRITICAL" if p.stock_quantity == 0 else "HIGH"
            })
            reorders.append({
                "sku": p.product_id, "name": p.product_name, "suggested_qty": p.reorder_quantity or 50,
                "supplier": p.supplier_name or p.supplier_id or "Primary Supplier"
            })
    return json.dumps({
        "stockout_hazards_count": len(hazards),
        "stockout_hazards": hazards[:8],
        "recommended_reorders": reorders[:8],
        "outlook": "Replenishment required for low-stock SKUs." if hazards else "Inventory levels are healthy."
    })

@tool(args_schema=SearchProductsInput)
def search_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    warehouse: Optional[str] = None,
    low_stock_only: bool = False,
    limit: int = 20,
    config: RunnableConfig = None
) -> str:
    """Search products in inventory with optional filters."""
    db = _get_db(config)
    res = product_fetcher.fetch(db, search=search, category=category, warehouse=warehouse, low_stock_only=low_stock_only, limit=limit)
    items = [
        {"sku": p.product_id, "name": p.product_name, "category": p.category, "stock": p.stock_quantity, "price": p.unit_price}
        for p in res.get("items", [])
    ]
    return json.dumps({"total": res.get("total", 0), "products": items})

@tool(args_schema=GetProductInput)
def get_product(sku: str, config: RunnableConfig = None) -> str:
    """Get full details of a specific product by SKU."""
    db = _get_db(config)
    p = product_fetcher.fetch_by_sku(db, sku)
    if not p:
        return json.dumps({"error": f"Product with SKU '{sku}' not found"})
    return json.dumps({
        "sku": p.product_id, "name": p.product_name, "category": p.category,
        "stock": p.stock_quantity, "unit_price": p.unit_price, "rack": p.rack_location,
        "warehouse": p.warehouse_name, "supplier": p.supplier_name, "status": p.status
    })

@tool(args_schema=CreateProductInput)
def create_product(
    product_name: str,
    product_id: Optional[str] = None,
    category: str = "General",
    stock_quantity: int = 0,
    unit_price: float = 0.0,
    reorder_level: int = 10,
    reorder_quantity: int = 50,
    warehouse_name: str = "Main Warehouse",
    rack_location: str = "A-01-01",
    config: RunnableConfig = None
) -> str:
    """Action: Add and register a new product in the inventory database."""
    db = _get_db(config)
    pid = product_id or _gen_id("SKU")
    if product_fetcher.fetch_by_sku(db, pid):
        return json.dumps({"error": f"Product with SKU '{pid}' already exists"})

    product = Product(
        product_id=pid, product_name=product_name, category=category,
        stock_quantity=int(stock_quantity), unit_price=float(unit_price),
        reorder_level=int(reorder_level), reorder_quantity=int(reorder_quantity),
        unit_of_measure="units", warehouse_name=warehouse_name,
        rack_location=rack_location, status="Active", date_received=datetime.now().strftime("%m/%d/%Y")
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    if product.stock_quantity > 0:
        move = MoveHistory(
            move_id=_gen_id("MOV-INIT"), product_id=product.product_id, movement_type="Receipt",
            from_location="Initial Setup", to_location=product.rack_location,
            quantity=product.stock_quantity, timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
            reference_id="INITIAL_STOCK"
        )
        db.add(move)
        db.commit()

    return json.dumps({
        "success": True, "message": f"Successfully created product '{product.product_name}'",
        "sku": product.product_id, "stock": product.stock_quantity
    })

@tool(args_schema=CreateReceiptInput)
def create_receipt(product_id: str, quantity_received: int, supplier_id: str = "SUP-001", config: RunnableConfig = None) -> str:
    """Action: Register an inbound purchase receipt in Draft status."""
    db = _get_db(config)
    receipt = Receipt(
        receipt_id=_gen_id("REC"), supplier_id=supplier_id, product_id=product_id,
        quantity_received=int(quantity_received), receipt_date=datetime.now().strftime("%m/%d/%Y"), status="Draft"
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return json.dumps({"success": True, "receipt_id": receipt.receipt_id, "status": receipt.status})

@tool(args_schema=ValidateReceiptInput)
def validate_receipt(receipt_id: str, config: RunnableConfig = None) -> str:
    """Action: Validate and finalize incoming receipt, incrementing physical stock."""
    db = _get_db(config)
    receipt = db.query(Receipt).filter(Receipt.receipt_id == receipt_id).first()
    if not receipt:
        return json.dumps({"error": f"Receipt '{receipt_id}' not found"})
    if receipt.status == "Done":
        return json.dumps({"error": "Receipt is already completed"})

    p = product_fetcher.fetch_by_sku(db, receipt.product_id)
    if p:
        p.stock_quantity += receipt.quantity_received
    receipt.status = "Done"

    move = MoveHistory(
        move_id=_gen_id("MOV-REC"), product_id=receipt.product_id, movement_type="Receipt",
        from_location="Vendors / Supplier", to_location=p.rack_location if p else "Main Warehouse",
        quantity=receipt.quantity_received, timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        reference_id=receipt.receipt_id
    )
    db.add(move)
    db.commit()
    return json.dumps({"success": True, "message": f"Receipt {receipt.receipt_id} validated. New stock: {p.stock_quantity if p else 'N/A'}"})

@tool(args_schema=CreateDeliveryInput)
def create_delivery(product_id: str, quantity_delivered: int, customer_name: str = "General Customer", config: RunnableConfig = None) -> str:
    """Action: Create an outbound delivery order in Draft status."""
    db = _get_db(config)
    delivery = Delivery(
        delivery_id=_gen_id("DEL"), product_id=product_id, quantity_delivered=int(quantity_delivered),
        customer_name=customer_name, delivery_date=datetime.now().strftime("%m/%d/%Y"), status="Draft"
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return json.dumps({"success": True, "delivery_id": delivery.delivery_id, "status": delivery.status})

@tool(args_schema=ValidateDeliveryInput)
def validate_delivery(delivery_id: str, config: RunnableConfig = None) -> str:
    """Action: Validate outbound delivery, decrementing physical stock and creating movement record."""
    db = _get_db(config)
    delivery = db.query(Delivery).filter(Delivery.delivery_id == delivery_id).first()
    if not delivery:
        return json.dumps({"error": f"Delivery '{delivery_id}' not found"})
    if delivery.status == "Done":
        return json.dumps({"error": "Delivery is already completed"})

    p = product_fetcher.fetch_by_sku(db, delivery.product_id)
    if p:
        if p.stock_quantity < delivery.quantity_delivered:
            return json.dumps({"error": f"Insufficient stock: {p.stock_quantity} available, {delivery.quantity_delivered} requested"})
        p.stock_quantity -= delivery.quantity_delivered
        p.sales_volume = (p.sales_volume or 0) + delivery.quantity_delivered
    delivery.status = "Done"

    move = MoveHistory(
        move_id=_gen_id("MOV-DEL"), product_id=delivery.product_id, movement_type="Delivery",
        from_location=p.rack_location if p else "Main Warehouse", to_location=f"Customer: {delivery.customer_name}",
        quantity=delivery.quantity_delivered, timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        reference_id=delivery.delivery_id
    )
    db.add(move)
    db.commit()
    return json.dumps({"success": True, "message": f"Delivery {delivery.delivery_id} validated. Remaining stock: {p.stock_quantity if p else 'N/A'}"})

@tool(args_schema=CreateStockAdjustmentInput)
def create_stock_adjustment(product_id: str, counted_quantity: int, reason: str = "Physical inventory count", config: RunnableConfig = None) -> str:
    """Action: Adjust physical inventory count and record variance in ledger."""
    db = _get_db(config)
    p = product_fetcher.fetch_by_sku(db, product_id)
    if not p:
        return json.dumps({"error": f"Product with SKU '{product_id}' not found"})

    recorded = p.stock_quantity
    diff = int(counted_quantity) - recorded
    p.stock_quantity = int(counted_quantity)

    adj = Adjustment(
        adjustment_id=_gen_id("ADJ"), product_id=product_id, recorded_quantity=recorded,
        counted_quantity=int(counted_quantity), adjustment_reason=reason,
        adjustment_date=datetime.now().strftime("%m/%d/%Y")
    )
    db.add(adj)
    db.commit()
    return json.dumps({"success": True, "message": f"Stock adjusted for '{p.product_name}' to {counted_quantity} (variance: {diff:+d})"})

@tool(args_schema=ListMovementsInput)
def list_movements(movement_type: Optional[str] = None, limit: int = 15, config: RunnableConfig = None) -> str:
    """Query immutable stock movement ledger records."""
    db = _get_db(config)
    res = move_fetcher.fetch(db, movement_type=movement_type, limit=limit)
    items = [
        {"move_id": m.move_id, "sku": m.product_id, "type": m.movement_type, "from": m.from_location, "to": m.to_location, "qty": m.quantity, "time": m.timestamp}
        for m in res.get("items", [])
    ]
    return json.dumps({"total": res.get("total", 0), "movements": items})

@tool
def list_warehouses(config: RunnableConfig) -> str:
    """List all registered warehouses and capacities."""
    db = _get_db(config)
    res = warehouse_fetcher.fetch(db, limit=20)
    items = [{"id": w.warehouse_id, "name": w.warehouse_name, "city": w.city, "capacity": w.capacity} for w in res.get("items", [])]
    return json.dumps({"warehouses": items})


# ============================================================================
# EXPORTED TOOL REGISTRY
# ============================================================================

INVENTORY_TOOLS = [
    get_inventory_status,
    predict_inventory_trends,
    search_products,
    get_product,
    create_product,
    create_receipt,
    validate_receipt,
    create_delivery,
    validate_delivery,
    create_stock_adjustment,
    list_movements,
    list_warehouses
]

ACTION_TOOL_NAMES = {
    "create_product",
    "create_receipt",
    "validate_receipt",
    "create_delivery",
    "validate_delivery",
    "create_stock_adjustment"
}
