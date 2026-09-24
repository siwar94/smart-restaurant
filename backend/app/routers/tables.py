from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.deps import require_role, get_current_user
from app.models.user import User, UserRole
from app.models.restaurant_table import RestaurantTable
from app.schemas.table import TableCreate, TableUpdate, TableOut

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.get("/", response_model=List[TableOut])
def list_tables(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(RestaurantTable).order_by(RestaurantTable.number).all()


@router.get("/{table_id}", response_model=TableOut)
def get_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    table = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table introuvable")
    return table


@router.post("/", response_model=TableOut, status_code=status.HTTP_201_CREATED)
def create_table(
    payload: TableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    existing = db.query(RestaurantTable).filter(RestaurantTable.number == payload.number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de table existe déjà")

    new_table = RestaurantTable(number=payload.number)
    db.add(new_table)
    db.commit()
    db.refresh(new_table)
    return new_table


@router.put("/{table_id}", response_model=TableOut)
def update_table(
    table_id: int,
    payload: TableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    table = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table introuvable")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(table, field, value)

    db.commit()
    db.refresh(table)
    return table


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    table = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table introuvable")

    db.delete(table)
    db.commit()
    return None