from decimal import Decimal
from typing import List, Optional
from typing import List

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

class OrdersByDayPoint(BaseModel):
    date: str  # format ISO "2026-09-20"
    orders_count: int
    revenue: Decimal


class PeakHourPoint(BaseModel):
    hour: int  # 0-23
    orders_count: int


class AnalyticsOut(BaseModel):
    orders_by_day: List[OrdersByDayPoint]
    peak_hours: List[PeakHourPoint]