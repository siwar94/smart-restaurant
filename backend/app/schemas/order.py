from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    table_id: int
    items: List[OrderItemCreate] = Field(min_length=1)


class OrderItemsReplace(BaseModel):
    items: List[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderItemOut(BaseModel):
    id: int
    menu_item_id: int
    menu_item_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    table_id: int
    server_id: int
    status: OrderStatus
    total: Decimal
    created_at: datetime
    sent_to_kitchen_at: Optional[datetime]
    preparation_started_at: Optional[datetime]
    ready_at: Optional[datetime]
    items: List[OrderItemOut]

    class Config:
        from_attributes = True