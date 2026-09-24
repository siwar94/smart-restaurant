import enum

from sqlalchemy import Column, Integer, Enum
from sqlalchemy.orm import relationship

from app.database.session import Base


class TableStatus(str, enum.Enum):
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"


class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, nullable=False)
    status = Column(Enum(TableStatus, name="table_status"), default=TableStatus.FREE)

    orders = relationship("Order", back_populates="table")