import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis

app = FastAPI(title="ShopFlow Event-Driven API")

# Environment variables theke connection parameters newa (Production standard)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
except Exception as e:
    print(f"Redis connection error: {e}")

class Order(BaseModel):
    order_id: str
    item_name: str
    quantity: int
    customer_email: str

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Order API"}

@app.post("/orders/")
def create_order(order: Order):
    try:
        # Order data-ke Redis queue-te push kora (Event-Driven approach)
        order_data = order.dict()
        redis_client.rpush("order_queue", json.dumps(order_data))
        return {"message": "Order received and queued successfully!", "order_id": order.order_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))