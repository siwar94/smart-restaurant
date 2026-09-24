from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardOut
from app.services import dashboard_service
from app.schemas.dashboard import DashboardOut, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardOut)
def get_dashboard(
    top_limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """BF12 : réservé à l'administrateur/responsable."""
    return DashboardOut(
        summary=dashboard_service.get_summary(db),
        top_items=dashboard_service.get_top_items(db, limit=top_limit),
        preparation=dashboard_service.get_preparation_stats(db),
    )


@router.get("/summary", response_model=dashboard_service.DashboardSummary)
def get_summary_only(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    return dashboard_service.get_summary(db)