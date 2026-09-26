from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..fetchers import warehouse_fetcher
from ..models import Warehouse, Product
from ..schemas import WarehouseSchema, WarehouseOut

router = APIRouter(prefix="/api/warehouses", tags=["Warehouses"])

@router.get("")
def list_warehouses(search: Optional[str] = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return warehouse_fetcher.fetch(db, search=search, skip=skip, limit=limit)

@router.get("/locations")
def list_warehouse_locations(db: Session = Depends(get_db)):
    results = db.query(Product.rack_location).distinct().filter(Product.rack_location.isnot(None)).all()
    locations = sorted([r[0] for r in results if r[0]])
    return {"locations": locations}

@router.get("/{id}", response_model=WarehouseOut)
def get_warehouse(id: int, db: Session = Depends(get_db)):
    warehouse = warehouse_fetcher.get_by_id(db, id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse

@router.post("", response_model=WarehouseOut)
def create_warehouse(payload: WarehouseSchema, db: Session = Depends(get_db)):
    existing = warehouse_fetcher.get_by_field(db, "warehouse_id", payload.warehouse_id)
    if existing:
        raise HTTPException(status_code=400, detail="Warehouse with this ID already exists")
    
    warehouse = Warehouse(**payload.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse

@router.put("/{id}", response_model=WarehouseOut)
def update_warehouse(id: int, payload: WarehouseSchema, db: Session = Depends(get_db)):
    warehouse = warehouse_fetcher.get_by_id(db, id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    for key, value in payload.model_dump().items():
        setattr(warehouse, key, value)
    
    db.commit()
    db.refresh(warehouse)
    return warehouse
