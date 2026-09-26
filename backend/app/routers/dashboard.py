from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.fetchers import dashboard_fetcher, move_fetcher, product_fetcher
from app.schemas import DashboardKPIOut

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/kpis", response_model=DashboardKPIOut)
def get_dashboard_kpis(db: Session = Depends(get_db)):
    return dashboard_fetcher.fetch_kpis(db)

@router.get("/activity")
def get_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    return move_fetcher.fetch(db, limit=limit)

@router.get("/low-stock")
def get_low_stock_products(limit: int = 10, db: Session = Depends(get_db)):
    return product_fetcher.fetch(db, low_stock_only=True, limit=limit)
