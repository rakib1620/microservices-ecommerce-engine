import os
import json
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import redis

from database import engine, Base, get_db
import models
from schemas import UserCreate, UserResponse
from security import hash_password, verify_password

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

# ==========================================
# USER AUTHENTICATION ENDPOINTS (NEW)
# ==========================================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user:
    1. Check if email already exists in PostgreSQL.
    2. Securely hash the password.
    3. Save the new user to the database.
    """
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password and create new user instance
    hashed_pwd = hash_password(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/auth/login")
def login_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Login user:
    1. Verify if user exists in the database.
    2. Verify if the password matches the hashed password.
    3. Return a successful login message.
    """
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"message": "Login successful", "email": db_user.email}


# ==========================================
# ORDER ENDPOINTS
# ==========================================

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the order: {str(e)}"
        )
