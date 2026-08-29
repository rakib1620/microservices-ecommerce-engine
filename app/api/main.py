import os
import json
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
import redis
from jose import JWTError, jwt

import models
import schemas
import security
from database import engine, Base, get_db
from schemas import UserCreate, UserResponse
from security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM

app = FastAPI(title="ShopFlow Event-Driven API")


@app.on_event("startup")
def on_startup():
    """
    Create all database tables on application startup — not at import time.
    This keeps `from main import app` safe to run in tests/CI without a live database.
    """
    models.Base.metadata.create_all(bind=engine)


# Redis connection setup using environment variables (Production standard)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
except Exception as e:
    print(f"Redis connection error: {e}")

# OAuth2 scheme for token authentication (Points to /auth/login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Validate JWT token and return the current authenticated user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Pydantic schema for incoming order requests
class OrderCreate(BaseModel):
    item_name: str
    quantity: int
    total_price: float

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
# USER AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user:
    1. Check if email already exists in PostgreSQL.
    2. Securely hash the password.
    3. Save the new user to the database.
    """
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

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
    3. Generate and return a JWT access token.
    """
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT Access Token
    access_token = create_access_token(data={"sub": db_user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==========================================
# ORDER ENDPOINTS (PROTECTED)
# ==========================================

@app.post("/orders/")
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new order in PostgreSQL database and queue it in Redis for background processing.
    Requires a valid JWT Bearer Token.
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

        # 2. Prepare event payload and push to Redis queue for background worker (using authenticated user's email)
        order_event = {
            "order_id": new_order.id,
            "item_name": new_order.item_name,
            "quantity": new_order.quantity,
            "total_price": new_order.total_price,
            "customer_email": current_user.email,
            "status": new_order.status
        }

        redis_client.lpush("order_queue", json.dumps(order_event))

        return {
            "message": "Order created successfully and queued for processing!",
            "order_id": new_order.id,
            "customer": current_user.email,
            "status": new_order.status
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the order: {str(e)}"
        )
