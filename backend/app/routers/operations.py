from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
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

@router.get("/receipts/{id}/slip", response_class=HTMLResponse)
def get_receipt_slip(id: int, db: Session = Depends(get_db)):
    receipt = receipt_fetcher.get_by_id(db, id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    product = product_fetcher.fetch_by_sku(db, receipt.product_id)
    prod_name = product.product_name if product else "N/A"
    prod_cat = product.category if product else "N/A"
    prod_uom = product.unit_of_measure if product else "units"
    prod_loc = product.rack_location if product else "Main Warehouse"
    supp_name = product.supplier_name if product else receipt.supplier_id

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Receipt Slip - {receipt.receipt_id}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 40px; color: #1e293b; }}
            .slip-card {{ max-width: 800px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 8px; padding: 32px; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
            .title {{ font-size: 24px; font-weight: bold; color: #0f172a; }}
            .meta {{ margin-top: 4px; color: #64748b; font-size: 14px; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 13px; background: #dbeafe; color: #1d4ed8; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
            .info-box {{ background: #f8fafc; padding: 12px 16px; border-radius: 6px; }}
            .label {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
            .value {{ font-size: 15px; font-weight: 500; margin-top: 4px; color: #0f172a; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
            th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #e2e8f0; }}
            th {{ background: #f1f5f9; font-size: 13px; font-weight: 600; color: #475569; }}
            .signatures {{ display: flex; justify-content: space-between; margin-top: 48px; padding-top: 24px; }}
            .sig-line {{ width: 200px; border-top: 1px dashed #94a3b8; text-align: center; font-size: 13px; color: #64748b; padding-top: 8px; }}
            .btn-print {{ background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px; margin-bottom: 20px; }}
            @media print {{ .btn-print {{ display: none; }} body {{ padding: 0; }} .slip-card {{ border: none; padding: 0; }} }}
        </style>
    </head>
    <body>
        <div style="max-width: 800px; margin: 0 auto;">
            <button class="btn-print" onclick="window.print()">🖨️ Print / Save as PDF</button>
        </div>
        <div class="slip-card">
            <div class="header">
                <div>
                    <div class="title">StockSense - Goods Receipt Note (GRN)</div>
                    <div class="meta">Reference: <strong>{receipt.receipt_id}</strong> | Generated on: {datetime.now().strftime("%B %d, %Y")}</div>
                </div>
                <div>
                    <span class="badge">{receipt.status.upper()}</span>
                </div>
            </div>

            <div class="grid">
                <div class="info-box">
                    <div class="label">Received From (Supplier)</div>
                    <div class="value">{supp_name} (ID: {receipt.supplier_id})</div>
                </div>
                <div class="info-box">
                    <div class="label">Destination Warehouse / Location</div>
                    <div class="value">{prod_loc}</div>
                </div>
                <div class="info-box">
                    <div class="label">Scheduled Date</div>
                    <div class="value">{receipt.receipt_date or 'Immediate'}</div>
                </div>
                <div class="info-box">
                    <div class="label">Document Status</div>
                    <div class="value">{receipt.status}</div>
                </div>
            </div>

            <h3>Item Details</h3>
            <table>
                <thead>
                    <tr>
                        <th>Product SKU</th>
                        <th>Product Name</th>
                        <th>Category</th>
                        <th>Quantity Received</th>
                        <th>Unit</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>{receipt.product_id}</strong></td>
                        <td>{prod_name}</td>
                        <td>{prod_cat}</td>
                        <td><strong>{receipt.quantity_received}</strong></td>
                        <td>{prod_uom}</td>
                    </tr>
                </tbody>
            </table>

            <div class="signatures">
                <div class="sig-line">Warehouse Receiver Signature</div>
                <div class="sig-line">Authorized Signatory / Date</div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

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
    
    product = product_fetcher.fetch_by_sku(db, receipt.product_id)
    if product:
        product.stock_quantity += receipt.quantity_received
        product.date_received = datetime.now().strftime("%m/%d/%Y")

    receipt.status = "Done"

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

@router.get("/deliveries/{id}/slip", response_class=HTMLResponse)
def get_delivery_slip(id: int, db: Session = Depends(get_db)):
    delivery = delivery_fetcher.get_by_id(db, id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    product = product_fetcher.fetch_by_sku(db, delivery.product_id)
    prod_name = product.product_name if product else "N/A"
    prod_cat = product.category if product else "N/A"
    prod_uom = product.unit_of_measure if product else "units"
    prod_loc = product.rack_location if product else "Main Warehouse"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Delivery Slip - {delivery.delivery_id}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 40px; color: #1e293b; }}
            .slip-card {{ max-width: 800px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 8px; padding: 32px; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
            .title {{ font-size: 24px; font-weight: bold; color: #0f172a; }}
            .meta {{ margin-top: 4px; color: #64748b; font-size: 14px; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 13px; background: #dcfce7; color: #15803d; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
            .info-box {{ background: #f8fafc; padding: 12px 16px; border-radius: 6px; }}
            .label {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
            .value {{ font-size: 15px; font-weight: 500; margin-top: 4px; color: #0f172a; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
            th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #e2e8f0; }}
            th {{ background: #f1f5f9; font-size: 13px; font-weight: 600; color: #475569; }}
            .signatures {{ display: flex; justify-content: space-between; margin-top: 48px; padding-top: 24px; }}
            .sig-line {{ width: 200px; border-top: 1px dashed #94a3b8; text-align: center; font-size: 13px; color: #64748b; padding-top: 8px; }}
            .btn-print {{ background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px; margin-bottom: 20px; }}
            @media print {{ .btn-print {{ display: none; }} body {{ padding: 0; }} .slip-card {{ border: none; padding: 0; }} }}
        </style>
    </head>
    <body>
        <div style="max-width: 800px; margin: 0 auto;">
            <button class="btn-print" onclick="window.print()">🖨️ Print / Save as PDF</button>
        </div>
        <div class="slip-card">
            <div class="header">
                <div>
                    <div class="title">StockSense - Delivery Packing Slip</div>
                    <div class="meta">Reference: <strong>{delivery.delivery_id}</strong> | Date: {datetime.now().strftime("%B %d, %Y")}</div>
                </div>
                <div>
                    <span class="badge">{delivery.status.upper()}</span>
                </div>
            </div>

            <div class="grid">
                <div class="info-box">
                    <div class="label">Customer / Destination</div>
                    <div class="value">{delivery.customer_name or 'Direct Customer'}</div>
                </div>
                <div class="info-box">
                    <div class="label">Source Location / Warehouse</div>
                    <div class="value">{prod_loc}</div>
                </div>
                <div class="info-box">
                    <div class="label">Delivery Scheduled Date</div>
                    <div class="value">{delivery.delivery_date or 'Immediate'}</div>
                </div>
                <div class="info-box">
                    <div class="label">Status</div>
                    <div class="value">{delivery.status}</div>
                </div>
            </div>

            <h3>Shipment Items</h3>
            <table>
                <thead>
                    <tr>
                        <th>Product SKU</th>
                        <th>Product Name</th>
                        <th>Category</th>
                        <th>Quantity Delivered</th>
                        <th>Unit</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>{delivery.product_id}</strong></td>
                        <td>{prod_name}</td>
                        <td>{prod_cat}</td>
                        <td><strong>{delivery.quantity_delivered}</strong></td>
                        <td>{prod_uom}</td>
                    </tr>
                </tbody>
            </table>

            <div class="signatures">
                <div class="sig-line">Picked & Packed By</div>
                <div class="sig-line">Customer Receipt Signature</div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

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
    
    product = product_fetcher.fetch_by_sku(db, delivery.product_id)
    if product:
        if product.stock_quantity < delivery.quantity_delivered:
            raise HTTPException(status_code=400, detail=f"Insufficient stock on hand ({product.stock_quantity} available)")
        product.stock_quantity -= delivery.quantity_delivered
        product.sales_volume += delivery.quantity_delivered
        product.last_order_date = datetime.now().strftime("%m/%d/%Y")

    delivery.status = "Done"

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

@router.get("/suppliers")
def list_suppliers(db: Session = Depends(get_db)):
    results = db.query(Product.supplier_id, Product.supplier_name).distinct().all()
    suppliers = [{"supplier_id": r[0], "supplier_name": r[1]} for r in results if r[0] and r[1]]
    return {"suppliers": suppliers}
