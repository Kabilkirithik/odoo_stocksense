from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.fetchers import product_fetcher
from app.models import Product
from app.schemas import ProductSchema, ProductUpdate, ProductOut

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("")
def list_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    warehouse: Optional[str] = None,
    status: Optional[str] = None,
    low_stock: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return product_fetcher.fetch(
        db,
        search=search,
        category=category,
        warehouse=warehouse,
        status=status,
        low_stock_only=low_stock,
        skip=skip,
        limit=limit
    )

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    return product_fetcher.fetch_categories(db)

@router.get("/low-stock")
def list_low_stock_products(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return product_fetcher.fetch(db, low_stock_only=True, skip=skip, limit=limit)

@router.get("/{sku}", response_model=ProductOut)
def get_product(sku: str, db: Session = Depends(get_db)):
    product = product_fetcher.fetch_by_sku(db, sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("", response_model=ProductOut)
def create_product(payload: ProductSchema, db: Session = Depends(get_db)):
    existing = product_fetcher.fetch_by_sku(db, payload.product_id)
    if existing:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.put("/{sku}", response_model=ProductOut)
def update_product(sku: str, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = product_fetcher.fetch_by_sku(db, sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{sku}")
def delete_product(sku: str, db: Session = Depends(get_db)):
    product = product_fetcher.fetch_by_sku(db, sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully", "product_id": sku}
