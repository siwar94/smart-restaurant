from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    orders_today: int
    orders_in_progress: int       # NEW + IN_PREPARATION
    orders_ready: int
    orders_served_today: int
    revenue_today: Decimal
    occupied_tables: int
    total_tables: int


class TopMenuItem(BaseModel):
    menu_item_id: int
    name: str
    total_quantity: int
    total_revenue: Decimal


class PreparationStats(BaseModel):
    average_preparation_seconds: Optional[float]
    average_total_seconds: Optional[float]  # de l'envoi cuisine au "Servie"
    orders_measured: int


class DashboardOut(BaseModel):
    summary: DashboardSummary
    top_items: List[TopMenuItem]
    preparation: PreparationStats