from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers.dashboard import router as dashboard_router
from .routers.products import router as products_router
from .routers.warehouses import router as warehouses_router
from .routers.operations import router as operations_router
from .routers.moves import router as moves_router

app = FastAPI(
    title="StockSense Inventory API",
    description="REST API for StockSense Inventory & Warehouse Management System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


app.include_router(dashboard_router)
app.include_router(products_router)
app.include_router(warehouses_router)
app.include_router(operations_router)
app.include_router(moves_router)


@app.get("/")
def root():
    return {
        "app": "StockSense Inventory API",
        "status": "online",
        "docs_url": "/docs"
    }
