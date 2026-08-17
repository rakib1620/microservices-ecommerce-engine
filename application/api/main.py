import os
import json
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import redis

from database import engine, Base, get_db
import models

# Create all database tables automatically on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ShopFlow Event-Driven API")

# Redis connection setup using environment variables (Production standard)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
except Exception as e:
    print(f"Redis connection error: {e}")

# Pydantic schema for incoming order requests
class OrderCreate(BaseModel):
    item_name: str
    quantity: int
    total_price: float
    customer_email: str

# Root endpoint to check API health
@app.get("/")
def read_root():
    """
    Root health check endpoint for the ShopFlow API.
    """
    return {
        "message": "Welcome to ShopFlow Event-Driven API with PostgreSQL & Redis!",
        "status": "Running"
    }

# Endpoint to create a new order (Saves to PostgreSQL and pushes to Redis queue)
@app.post("/orders/")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """
    Create a new order in PostgreSQL database and queue it in Redis for background processing.
    """
    try:
        # 1. Save the order into PostgreSQL database
        new_order = models.OrderModel(
            item_name=order.item_name,
            quantity=order.quantity,
            total_price=order.total_price,
            status="pending"
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        # 2. Prepare event payload and push to Redis queue for background worker
        order_event = {
            "order_id": new_order.id,
            "item_name": new_order.item_name,
            "quantity": new_order.quantity,
            "total_price": new_order.total_price,
            "customer_email": order.customer_email,
            "status": new_order.status
        }
        
        redis_client.lpush("order_queue", json.dumps(order_event))

        return {
            "message": "Order created successfully and queued for processing!",
            "order_id": new_order.id,
            "status": new_order.status
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
