from datetime import date
from typing import List

from pydantic import BaseModel


class DemandForecastItem(BaseModel):
    menu_item_id: int
    menu_item_name: str
    predicted_quantity: int


class DemandForecastOut(BaseModel):
    date: date
    items: List[DemandForecastItem]


class RecommendationItem(BaseModel):
    menu_item_id: int
    menu_item_name: str
    confidence: float
    lift: float
    support: float


class ItemRecommendations(BaseModel):
    menu_item_id: int
    menu_item_name: str
    recommendations: List[RecommendationItem]