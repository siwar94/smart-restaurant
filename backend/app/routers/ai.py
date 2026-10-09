from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.schemas.ai import DemandForecastOut
from app.services.ml_service import predict_demand, ModelNotAvailableError
from typing import List

from app.core.deps import get_current_user
from app.schemas.ai import RecommendationItem, ItemRecommendations
from app.services import recommendation_service

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/demand-forecast", response_model=DemandForecastOut)
def get_demand_forecast(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    forecast_date = target_date or (date.today() + timedelta(days=1))
    try:
        items = predict_demand(db, forecast_date)
    except ModelNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return DemandForecastOut(date=forecast_date, items=items)

@router.get("/recommendations/{menu_item_id}", response_model=List[RecommendationItem])
def get_item_recommendations(
    menu_item_id: int,
    current_user: User = Depends(get_current_user),  # accessible à tout utilisateur connecté (utile côté serveur)
):
    try:
        return recommendation_service.get_recommendations_for_item(menu_item_id)
    except recommendation_service.ModelNotAvailableError:
        return []  # pas de suggestion plutôt qu'une erreur bloquante côté serveur


@router.get("/recommendations", response_model=List[ItemRecommendations])
def get_all_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    try:
        return recommendation_service.get_all_recommendations(db)
    except recommendation_service.ModelNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))