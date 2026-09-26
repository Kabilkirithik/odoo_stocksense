from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="Warehouse Staff")  # Admin, Inventory Manager, Warehouse Staff
    reset_otp = Column(String(10), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(String(50), unique=True, index=True, nullable=False)
    warehouse_name = Column(String(150), nullable=False)
    city = Column(String(100), nullable=False)
    capacity = Column(Integer, default=10000)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(50), unique=True, index=True, nullable=False)  # SKU
    product_name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), index=True)
    supplier_id = Column(String(50), index=True)
    supplier_name = Column(String(150))
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    unit_price = Column(Float, default=0.0)
    unit_of_measure = Column(String(50), default="units")
    date_received = Column(String(50))
    last_order_date = Column(String(50))
    expiration_date = Column(String(50))
    warehouse_location = Column(String(200))
    warehouse_name = Column(String(150))
    warehouse_code = Column(String(50))
    rack_location = Column(String(100))
    sales_volume = Column(Integer, default=0)
    inventory_turnover_rate = Column(Float, default=0.0)
    status = Column(String(50), default="Active")  # Active, Backordered, Discontinued


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(String(50), unique=True, index=True, nullable=False)
    supplier_id = Column(String(50), nullable=False)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    quantity_received = Column(Integer, default=0)
    receipt_date = Column(String(50))
    status = Column(String(50), default="Draft")  # Draft, Waiting, Ready, Done, Canceled


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(String(50), unique=True, index=True, nullable=False)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    quantity_delivered = Column(Integer, default=0)
    delivery_date = Column(String(50))
    customer_name = Column(String(150))
    status = Column(String(50), default="Draft")  # Draft, Waiting, Ready, Done, Canceled


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(String(50), unique=True, index=True, nullable=False)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    from_location = Column(String(150), nullable=False)
    to_location = Column(String(150), nullable=False)
    quantity_transferred = Column(Integer, default=0)
    transfer_date = Column(String(50))
    status = Column(String(50), default="Draft")  # Draft, Ready, Done, Canceled


class Adjustment(Base):
    __tablename__ = "adjustments"

    id = Column(Integer, primary_key=True, index=True)
    adjustment_id = Column(String(50), unique=True, index=True, nullable=False)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    recorded_quantity = Column(Integer, default=0)
    counted_quantity = Column(Integer, default=0)
    adjustment_reason = Column(Text)
    adjustment_date = Column(String(50))


class MoveHistory(Base):
    __tablename__ = "move_history"

    id = Column(Integer, primary_key=True, index=True)
    move_id = Column(String(50), unique=True, index=True, nullable=False)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    movement_type = Column(String(50), nullable=False)  # Receipt, Delivery, Transfer, Adjustment
    from_location = Column(String(150), nullable=False)
    to_location = Column(String(150), nullable=False)
    quantity = Column(Integer, default=0)
    timestamp = Column(String(50))
    reference_id = Column(String(50), nullable=False)
