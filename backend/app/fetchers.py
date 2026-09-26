from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.models import Product, Receipt, Delivery, Transfer, Adjustment, MoveHistory, Warehouse


# this file contains the fetching logic for all the tables and it is implented using polymorphism where the same function is used multiple times in multiple formats


T = TypeVar("T")

class BaseFetcher(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def get_by_id(self, db: Session, id_value: Any) -> Optional[T]:
        return db.query(self.model).filter(self.model.id == id_value).first()

    def get_by_field(self, db: Session, field_name: str, value: Any) -> Optional[T]:
        field = getattr(self.model, field_name, None)
        return db.query(self.model).filter(field == value).first() if field is not None else None

    def get_all(self, db: Session, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, descending: bool = False) -> List[T]:
        query = db.query(self.model)
        if order_by:
            field = getattr(self.model, order_by, None)
            if field is not None:
                query = query.order_by(desc(field) if descending else asc(field))
        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, **filters) -> int:
        query = db.query(self.model)
        for key, value in filters.items():
            field = getattr(self.model, key, None)
            if field is not None and value is not None:
                query = query.filter(field == value)
        return query.count()

    def fetch(self, db: Session, **kwargs) -> Dict[str, Any]:
        skip = kwargs.get("skip", 0)
        limit = kwargs.get("limit", 100)
        return {
            "items": self.get_all(db, skip=skip, limit=limit),
            "total": self.count(db)
        }


class ProductFetcher(BaseFetcher[Product]):
    def __init__(self):
        super().__init__(Product)

    def fetch(self, db: Session, search: Optional[str] = None, category: Optional[str] = None, warehouse: Optional[str] = None, status: Optional[str] = None, low_stock_only: bool = False, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        query = db.query(self.model)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    self.model.product_name.ilike(pattern),
                    self.model.product_id.ilike(pattern),
                    self.model.supplier_name.ilike(pattern)
                )
            )

        if category:
            query = query.filter(self.model.category == category)
        if warehouse:
            query = query.filter(self.model.warehouse_name == warehouse)
        if status:
            query = query.filter(self.model.status == status)
        if low_stock_only:
            query = query.filter(self.model.stock_quantity <= self.model.reorder_level)

        return {
            "items": query.order_by(self.model.id.asc()).offset(skip).limit(limit).all(),
            "total": query.count()
        }

    def fetch_by_sku(self, db: Session, sku: str) -> Optional[Product]:
        return db.query(self.model).filter(self.model.product_id == sku).first()

    def fetch_categories(self, db: Session) -> List[str]:
        results = db.query(self.model.category).distinct().filter(self.model.category.isnot(None)).all()
        return [r[0] for r in results if r[0]]

    def fetch_low_stock_count(self, db: Session) -> int:
        return db.query(self.model).filter(self.model.stock_quantity <= self.model.reorder_level).count()


class ReceiptFetcher(BaseFetcher[Receipt]):
    def __init__(self):
        super().__init__(Receipt)

    def fetch(self, db: Session, status: Optional[str] = None, supplier_id: Optional[str] = None, product_id: Optional[str] = None, search: Optional[str] = None, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        query = db.query(self.model)

        if status:
            query = query.filter(self.model.status == status)
        if supplier_id:
            query = query.filter(self.model.supplier_id == supplier_id)
        if product_id:
            query = query.filter(self.model.product_id == product_id)
        if search:
            query = query.filter(self.model.receipt_id.ilike(f"%{search.strip()}%"))

        return {
            "items": query.order_by(desc(self.model.id)).offset(skip).limit(limit).all(),
            "total": query.count()
        }

    def fetch_pending_count(self, db: Session) -> int:
        return db.query(self.model).filter(self.model.status.in_(["Draft", "Waiting", "Ready"])).count()


class DeliveryFetcher(BaseFetcher[Delivery]):
    def __init__(self):
        super().__init__(Delivery)

    def fetch(self, db: Session, status: Optional[str] = None, customer_name: Optional[str] = None, product_id: Optional[str] = None, search: Optional[str] = None, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        query = db.query(self.model)

        if status:
            query = query.filter(self.model.status == status)
        if customer_name:
            query = query.filter(self.model.customer_name.ilike(f"%{customer_name.strip()}%"))
        if product_id:
            query = query.filter(self.model.product_id == product_id)
        if search:
            query = query.filter(self.model.delivery_id.ilike(f"%{search.strip()}%"))

        return {
            "items": query.order_by(desc(self.model.id)).offset(skip).limit(limit).all(),
            "total": query.count()
        }

    def fetch_pending_count(self, db: Session) -> int:
        return db.query(self.model).filter(self.model.status.in_(["Draft", "Waiting", "Ready"])).count()


class TransferFetcher(BaseFetcher[Transfer]):
    def __init__(self):
        super().__init__(Transfer)

    def fetch(self, db: Session, status: Optional[str] = None, location: Optional[str] = None, product_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        query = db.query(self.model)

        if status:
            query = query.filter(self.model.status == status)
        if location:
            query = query.filter(
                or_(
                    self.model.from_location.ilike(f"%{location.strip()}%"),
                    self.model.to_location.ilike(f"%{location.strip()}%")
                )
            )
        if product_id:
            query = query.filter(self.model.product_id == product_id)

        return {
            "items": query.order_by(desc(self.model.id)).offset(skip).limit(limit).all(),
            "total": query.count()
        }

    def fetch_scheduled_count(self, db: Session) -> int:
        return db.query(self.model).filter(self.model.status.in_(["Draft", "Ready"])).count()


class AdjustmentFetcher(BaseFetcher[Adjustment]):
    def __init__(self):
        super().__init__(Adjustment)

    def fetch(self, db: Session, product_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        query = db.query(self.model)

        if product_id:
            query = query.filter(self.model.product_id == product_id)

        return {
            "items": query.order_by(desc(self.model.id)).offset(skip).limit(limit).all(),
            "total": query.count()
        }


class MoveHistoryFetcher(BaseFetcher[MoveHistory]):
    def __init__(self):
        super().__init__(MoveHistory)

    def fetch(self, db: Session, movement_type: Optional[str] = None, product_id: Optional[str] = None, reference_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        query = db.query(self.model)

        if movement_type:
            query = query.filter(self.model.movement_type == movement_type)
        if product_id:
            query = query.filter(self.model.product_id == product_id)
        if reference_id:
            query = query.filter(self.model.reference_id.ilike(f"%{reference_id.strip()}%"))

        return {
            "items": query.order_by(desc(self.model.id)).offset(skip).limit(limit).all(),
            "total": query.count()
        }


class WarehouseFetcher(BaseFetcher[Warehouse]):
    def __init__(self):
        super().__init__(Warehouse)

    def fetch(self, db: Session, search: Optional[str] = None, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        query = db.query(self.model)
        if search:
            query = query.filter(
                or_(
                    self.model.warehouse_name.ilike(f"%{search.strip()}%"),
                    self.model.city.ilike(f"%{search.strip()}%"),
                    self.model.warehouse_id.ilike(f"%{search.strip()}%")
                )
            )
        return {
            "items": query.offset(skip).limit(limit).all(),
            "total": query.count()
        }


class DashboardFetcher:
    def __init__(self):
        self.products = ProductFetcher()
        self.receipts = ReceiptFetcher()
        self.deliveries = DeliveryFetcher()
        self.transfers = TransferFetcher()
        self.moves = MoveHistoryFetcher()

    def fetch_kpis(self, db: Session) -> Dict[str, Any]:
        return {
            "total_products": self.products.count(db),
            "low_stock_items": self.products.fetch_low_stock_count(db),
            "pending_receipts": self.receipts.fetch_pending_count(db),
            "pending_deliveries": self.deliveries.fetch_pending_count(db),
            "internal_transfers_scheduled": self.transfers.fetch_scheduled_count(db),
            "total_stock_movements": self.moves.count(db)
        }


product_fetcher = ProductFetcher()
receipt_fetcher = ReceiptFetcher()
delivery_fetcher = DeliveryFetcher()
transfer_fetcher = TransferFetcher()
adjustment_fetcher = AdjustmentFetcher()
move_fetcher = MoveHistoryFetcher()
warehouse_fetcher = WarehouseFetcher()
dashboard_fetcher = DashboardFetcher()
