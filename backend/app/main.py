from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.dashboard import router as dashboard_router
from app.routers.products import router as products_router
from app.routers.warehouses import router as warehouses_router
from app.routers.operations import router as operations_router
from app.routers.moves import router as moves_router
from chatbot import chat_router

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

app.include_router(dashboard_router)
app.include_router(products_router)
app.include_router(warehouses_router)
app.include_router(operations_router)
app.include_router(moves_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {
        "app": "StockSense Inventory API",
        "status": "online",
        "docs_url": "/docs"
    }
