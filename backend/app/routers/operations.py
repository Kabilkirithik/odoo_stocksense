from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..fetchers import (
    receipt_fetcher, delivery_fetcher, transfer_fetcher,
    adjustment_fetcher, product_fetcher
)
from ..models import Receipt, Delivery, Transfer, Adjustment, MoveHistory, Product
from ..schemas import (
    ReceiptSchema, ReceiptOut,
    DeliverySchema, DeliveryOut,
    TransferSchema, TransferOut,
    AdjustmentSchema, AdjustmentOut
)

router = APIRouter(prefix="/api/operations", tags=["Operations"])

def generate_move_id(prefix: str = "MOV") -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}"

# =====================================================================
# 1. RECEIPTS (Incoming Goods)
# =====================================================================
@router.get("/receipts")
def list_receipts(
    status: Optional[str] = None,
    supplier_id: Optional[str] = None,
    product_id: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return receipt_fetcher.fetch(
        db, status=status, supplier_id=supplier_id, product_id=product_id, search=search, skip=skip, limit=limit
    )

@router.get("/receipts/{id}", response_model=ReceiptOut)
def get_receipt(id: int, db: Session = Depends(get_db)):
    receipt = receipt_fetcher.get_by_id(db, id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt

@router.post("/receipts", response_model=ReceiptOut)
def create_receipt(payload: ReceiptSchema, db: Session = Depends(get_db)):
    receipt = Receipt(**payload.model_dump())
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt

@router.put("/receipts/{id}", response_model=ReceiptOut)
def update_receipt(id: int, payload: ReceiptSchema, db: Session = Depends(get_db)):
    receipt = receipt_fetcher.get_by_id(db, id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    for key, value in payload.model_dump().items():
        setattr(receipt, key, value)
    
    db.commit()
    db.refresh(receipt)
    return receipt

@router.post("/receipts/{id}/ready", response_model=ReceiptOut)
def set_receipt_ready(id: int, db: Session = Depends(get_db)):
    receipt = receipt_fetcher.get_by_id(db, id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    receipt.status = "Ready"
    db.commit()
    db.refresh(receipt)
    return receipt

@router.post("/receipts/{id}/validate", response_model=ReceiptOut)
def validate_receipt(id: int, db: Session = Depends(get_db)):
    receipt = receipt_fetcher.get_by_id(db, id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if receipt.status == "Done":
        raise HTTPException(status_code=400, detail="Receipt is already validated")
    
    # 1. Update product physical stock (+ quantity)
    product = product_fetcher.fetch_by_sku(db, receipt.product_id)
    if product:
        product.stock_quantity += receipt.quantity_received
        product.date_received = datetime.now().strftime("%m/%d/%Y")

    # 2. Mark receipt as Done
    receipt.status = "Done"

    # 3. Create immutable Stock Ledger entry
    move = MoveHistory(
        move_id=generate_move_id(),
        product_id=receipt.product_id,
        movement_type="Receipt",
        from_location="Vendors / Supplier",
        to_location=product.rack_location if product else "Main Warehouse / Stock",
        quantity=receipt.quantity_received,
        timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        reference_id=receipt.receipt_id
    )
    db.add(move)
    db.commit()
    db.refresh(receipt)
    return receipt

@router.post("/receipts/{id}/cancel", response_model=ReceiptOut)
def cancel_receipt(id: int, db: Session = Depends(get_db)):
    receipt = receipt_fetcher.get_by_id(db, id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if receipt.status == "Done":
        raise HTTPException(status_code=400, detail="Cannot cancel an already completed receipt")
    
    receipt.status = "Canceled"
    db.commit()
    db.refresh(receipt)
    return receipt

@router.delete("/receipts/{id}")
def delete_receipt(id: int, db: Session = Depends(get_db)):
    receipt = receipt_fetcher.get_by_id(db, id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if receipt.status == "Done":
        raise HTTPException(status_code=400, detail="Cannot delete a validated receipt")
    
    db.delete(receipt)
    db.commit()
    return {"message": "Receipt deleted successfully"}


# =====================================================================
# 2. DELIVERIES (Outgoing Goods)
# =====================================================================
@router.get("/deliveries")
def list_deliveries(
    status: Optional[str] = None,
    customer_name: Optional[str] = None,
    product_id: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return delivery_fetcher.fetch(
        db, status=status, customer_name=customer_name, product_id=product_id, search=search, skip=skip, limit=limit
    )

@router.get("/deliveries/{id}", response_model=DeliveryOut)
def get_delivery(id: int, db: Session = Depends(get_db)):
    delivery = delivery_fetcher.get_by_id(db, id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery

@router.post("/deliveries", response_model=DeliveryOut)
def create_delivery(payload: DeliverySchema, db: Session = Depends(get_db)):
    delivery = Delivery(**payload.model_dump())
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery

@router.put("/deliveries/{id}", response_model=DeliveryOut)
def update_delivery(id: int, payload: DeliverySchema, db: Session = Depends(get_db)):
    delivery = delivery_fetcher.get_by_id(db, id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    for key, value in payload.model_dump().items():
        setattr(delivery, key, value)
    
    db.commit()
    db.refresh(delivery)
    return delivery

@router.post("/deliveries/{id}/ready", response_model=DeliveryOut)
def set_delivery_ready(id: int, db: Session = Depends(get_db)):
    delivery = delivery_fetcher.get_by_id(db, id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    delivery.status = "Ready"
    db.commit()
    db.refresh(delivery)
    return delivery

@router.post("/deliveries/{id}/validate", response_model=DeliveryOut)
def validate_delivery(id: int, db: Session = Depends(get_db)):
    delivery = delivery_fetcher.get_by_id(db, id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if delivery.status == "Done":
        raise HTTPException(status_code=400, detail="Delivery is already validated")
    
    # 1. Update product physical stock (- quantity)
    product = product_fetcher.fetch_by_sku(db, delivery.product_id)
    if product:
        if product.stock_quantity < delivery.quantity_delivered:
            raise HTTPException(status_code=400, detail=f"Insufficient stock on hand ({product.stock_quantity} available)")
        product.stock_quantity -= delivery.quantity_delivered
        product.sales_volume += delivery.quantity_delivered
        product.last_order_date = datetime.now().strftime("%m/%d/%Y")

    # 2. Mark delivery as Done
    delivery.status = "Done"

    # 3. Create immutable Stock Ledger entry
    move = MoveHistory(
        move_id=generate_move_id(),
        product_id=delivery.product_id,
        movement_type="Delivery",
        from_location=product.rack_location if product else "Main Warehouse / Stock",
        to_location=f"Customer: {delivery.customer_name or 'Direct'}",
        quantity=delivery.quantity_delivered,
        timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        reference_id=delivery.delivery_id
    )
    db.add(move)
    db.commit()
    db.refresh(delivery)
    return delivery

@router.post("/deliveries/{id}/cancel", response_model=DeliveryOut)
def cancel_delivery(id: int, db: Session = Depends(get_db)):
    delivery = delivery_fetcher.get_by_id(db, id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if delivery.status == "Done":
        raise HTTPException(status_code=400, detail="Cannot cancel an already completed delivery")
    
    delivery.status = "Canceled"
    db.commit()
    db.refresh(delivery)
    return delivery

@router.delete("/deliveries/{id}")
def delete_delivery(id: int, db: Session = Depends(get_db)):
    delivery = delivery_fetcher.get_by_id(db, id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if delivery.status == "Done":
        raise HTTPException(status_code=400, detail="Cannot delete a validated delivery")
    
    db.delete(delivery)
    db.commit()
    return {"message": "Delivery deleted successfully"}


# =====================================================================
# 3. INTERNAL TRANSFERS
# =====================================================================
@router.get("/transfers")
def list_transfers(
    status: Optional[str] = None,
    location: Optional[str] = None,
    product_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return transfer_fetcher.fetch(db, status=status, location=location, product_id=product_id, skip=skip, limit=limit)

@router.get("/transfers/{id}", response_model=TransferOut)
def get_transfer(id: int, db: Session = Depends(get_db)):
    transfer = transfer_fetcher.get_by_id(db, id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer

@router.post("/transfers", response_model=TransferOut)
def create_transfer(payload: TransferSchema, db: Session = Depends(get_db)):
    transfer = Transfer(**payload.model_dump())
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer

@router.post("/transfers/{id}/validate", response_model=TransferOut)
def validate_transfer(id: int, db: Session = Depends(get_db)):
    transfer = transfer_fetcher.get_by_id(db, id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if transfer.status == "Done":
        raise HTTPException(status_code=400, detail="Transfer is already completed")
    
    product = product_fetcher.fetch_by_sku(db, transfer.product_id)
    if product:
        product.rack_location = transfer.to_location

    transfer.status = "Done"

    move = MoveHistory(
        move_id=generate_move_id(),
        product_id=transfer.product_id,
        movement_type="Transfer",
        from_location=transfer.from_location,
        to_location=transfer.to_location,
        quantity=transfer.quantity_transferred,
        timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        reference_id=transfer.transfer_id
    )
    db.add(move)
    db.commit()
    db.refresh(transfer)
    return transfer


# =====================================================================
# 4. STOCK ADJUSTMENTS
# =====================================================================
@router.get("/adjustments")
def list_adjustments(product_id: Optional[str] = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return adjustment_fetcher.fetch(db, product_id=product_id, skip=skip, limit=limit)

@router.post("/adjustments", response_model=AdjustmentOut)
def create_adjustment(payload: AdjustmentSchema, db: Session = Depends(get_db)):
    adjustment = Adjustment(**payload.model_dump())
    db.add(adjustment)

    product = product_fetcher.fetch_by_sku(db, payload.product_id)
    diff = payload.counted_quantity - payload.recorded_quantity
    if product:
        product.stock_quantity = payload.counted_quantity

    move = MoveHistory(
        move_id=generate_move_id(),
        product_id=payload.product_id,
        movement_type="Adjustment",
        from_location="Inventory Loss / Discrepancy" if diff > 0 else (product.rack_location if product else "Warehouse"),
        to_location=(product.rack_location if product else "Warehouse") if diff > 0 else "Inventory Loss / Discrepancy",
        quantity=abs(diff),
        timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        reference_id=payload.adjustment_id
    )
    db.add(move)
    db.commit()
    db.refresh(adjustment)
    return adjustment


# =====================================================================
# 5. DROPDOWN HELPERS
# =====================================================================
@router.get("/suppliers")
def list_suppliers(db: Session = Depends(get_db)):
    results = db.query(Product.supplier_id, Product.supplier_name).distinct().all()
    suppliers = [{"supplier_id": r[0], "supplier_name": r[1]} for r in results if r[0] and r[1]]
    return {"suppliers": suppliers}
