from typing import Optional

from pydantic import BaseModel

from app.models.restaurant_table import TableStatus


class TableCreate(BaseModel):
    number: int


class TableUpdate(BaseModel):
    number: Optional[int] = None
    status: Optional[TableStatus] = None


class TableOut(BaseModel):
    id: int
    number: int
    status: TableStatus

    class Config:
        from_attributes = True