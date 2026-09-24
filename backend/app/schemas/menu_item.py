from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.schemas.category import CategoryOut


class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    category_id: Optional[int] = None
    available: bool = True


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    category_id: Optional[int] = None
    available: Optional[bool] = None


class MenuItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: Decimal
    available: bool
    category_id: Optional[int]
    category: Optional[CategoryOut] = None

    class Config:
        from_attributes = True