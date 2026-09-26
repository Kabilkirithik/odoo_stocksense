from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class ProductSchema(BaseModel):
    product_id: str
    product_name: str
    category: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    stock_quantity: int = 0
    reorder_level: int = 10
    reorder_quantity: int = 50
    unit_price: float = 0.0
    unit_of_measure: str = "units"
    date_received: Optional[str] = None
    last_order_date: Optional[str] = None
    expiration_date: Optional[str] = None
    warehouse_location: Optional[str] = None
    warehouse_name: Optional[str] = None
    warehouse_code: Optional[str] = None
    rack_location: Optional[str] = None
    sales_volume: int = 0
    inventory_turnover_rate: float = 0.0
    status: str = "Active"

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    stock_quantity: Optional[int] = None
    reorder_level: Optional[int] = None
    reorder_quantity: Optional[int] = None
    unit_price: Optional[float] = None
    unit_of_measure: Optional[str] = None
    warehouse_name: Optional[str] = None
    rack_location: Optional[str] = None
    status: Optional[str] = None

class ProductOut(ProductSchema):
    id: int

    class Config:
        from_attributes = True


class WarehouseSchema(BaseModel):
    warehouse_id: str
    warehouse_name: str
    city: str
    capacity: int = 10000

class WarehouseOut(WarehouseSchema):
    id: int

    class Config:
        from_attributes = True


class ReceiptSchema(BaseModel):
    receipt_id: str
    supplier_id: str
    product_id: str
    quantity_received: int
    receipt_date: Optional[str] = None
    status: str = "Draft"

class ReceiptOut(ReceiptSchema):
    id: int

    class Config:
        from_attributes = True


class DeliverySchema(BaseModel):
    delivery_id: str
    product_id: str
    quantity_delivered: int
    delivery_date: Optional[str] = None
    customer_name: Optional[str] = None
    status: str = "Draft"

class DeliveryOut(DeliverySchema):
    id: int

    class Config:
        from_attributes = True


class TransferSchema(BaseModel):
    transfer_id: str
    product_id: str
    from_location: str
    to_location: str
    quantity_transferred: int
    transfer_date: Optional[str] = None
    status: str = "Draft"

class TransferOut(TransferSchema):
    id: int

    class Config:
        from_attributes = True


class AdjustmentSchema(BaseModel):
    adjustment_id: str
    product_id: str
    recorded_quantity: int
    counted_quantity: int
    adjustment_reason: Optional[str] = None
    adjustment_date: Optional[str] = None

class AdjustmentOut(AdjustmentSchema):
    id: int

    class Config:
        from_attributes = True


class MoveHistoryOut(BaseModel):
    id: int
    move_id: str
    product_id: str
    movement_type: str
    from_location: str
    to_location: str
    quantity: int
    timestamp: Optional[str] = None
    reference_id: str

    class Config:
        from_attributes = True


class DashboardKPIOut(BaseModel):
    total_products: int
    low_stock_items: int
    pending_receipts: int
    pending_deliveries: int
    internal_transfers_scheduled: int
    total_stock_movements: int


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
