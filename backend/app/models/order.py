import enum

from sqlalchemy import Column, Integer, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PREPARATION = "IN_PREPARATION"
    READY = "READY"
    SERVED = "SERVED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("restaurant_tables.id"), nullable=False)
    server_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatus, name="order_status"), default=OrderStatus.NEW)
    total = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    sent_to_kitchen_at = Column(DateTime(timezone=False), nullable=True)
    preparation_started_at = Column(DateTime(timezone=False), nullable=True)
    ready_at = Column(DateTime(timezone=False), nullable=True)

    table = relationship("RestaurantTable", back_populates="orders")
    server = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")