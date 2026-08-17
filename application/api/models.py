from sqlalchemy import Column, Integer, String, Float
from database import Base

class OrderModel(Base):
    """
    Database model representing customer orders in the shopflow system.
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="pending") # Status can be pending, processing, completed
