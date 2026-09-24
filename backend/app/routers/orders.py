from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus
from app.models.restaurant_table import RestaurantTable, TableStatus
from app.schemas.order import (
    OrderCreate,
    OrderOut,
    OrderItemsReplace,
    OrderStatusUpdate,
)
from app.services.order_service import (
    build_order_items,
    compute_total,
    ensure_order_editable,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SERVEUR, UserRole.ADMIN)),
):
    table = db.query(RestaurantTable).filter(RestaurantTable.id == payload.table_id).first()
    if not table:
        raise HTTPException(status_code=400, detail="Table introuvable")  # RM01

    order_items = build_order_items(db, payload.items)

    new_order = Order(
        table_id=table.id,
        server_id=current_user.id,
        status=OrderStatus.NEW,
        total=compute_total(order_items),
        items=order_items,
    )
    db.add(new_order)

    table.status = TableStatus.OCCUPIED

    db.commit()
    db.refresh(new_order)
    return new_order


@router.get("/", response_model=List[OrderOut])
def list_orders(
    status_filter: Optional[OrderStatus] = None,
    table_id: Optional[int] = None,
    mine_only: bool = False,
    kitchen_view: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Order)

    if status_filter is not None:
        query = query.filter(Order.status == status_filter)
    if table_id is not None:
        query = query.filter(Order.table_id == table_id)
    if mine_only:
        query = query.filter(Order.server_id == current_user.id)
    if kitchen_view:
        # Uniquement les commandes envoyées en cuisine et pas encore prêtes/servies
        query = query.filter(
            Order.sent_to_kitchen_at.isnot(None),
            Order.status.in_([OrderStatus.NEW, OrderStatus.IN_PREPARATION]),
        )

    return query.order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    return order


@router.put("/{order_id}/items", response_model=OrderOut)
def replace_order_items(
    order_id: int,
    payload: OrderItemsReplace,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SERVEUR, UserRole.ADMIN)),
):
    """BF07 : ajouter/supprimer/modifier des articles avant envoi en cuisine.
    On remplace l'ensemble des articles pour garantir un total toujours cohérent."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    ensure_order_editable(order)

    new_items = build_order_items(db, payload.items)

    order.items.clear()
    db.flush()
    order.items = new_items
    order.total = compute_total(new_items)

    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/send-to-kitchen", response_model=OrderOut)
def send_to_kitchen(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SERVEUR, UserRole.ADMIN)),
):
    """BF08 : confirmation et transmission à la cuisine."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    ensure_order_editable(order)

    order.sent_to_kitchen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """BF09 : Nouvelle -> En préparation -> Prête (cuisine), puis Servie (serveur)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    current = order.status
    target = payload.status
    now = datetime.now(timezone.utc)

    valid_transitions = {
        (OrderStatus.NEW, OrderStatus.IN_PREPARATION): (UserRole.CUISINE, UserRole.ADMIN),
        (OrderStatus.IN_PREPARATION, OrderStatus.READY): (UserRole.CUISINE, UserRole.ADMIN),
        (OrderStatus.READY, OrderStatus.SERVED): (UserRole.SERVEUR, UserRole.ADMIN),
    }

    allowed_roles = valid_transitions.get((current, target))
    if allowed_roles is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transition invalide : {current.value} -> {target.value}",
        )
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle non autorisé pour cette transition",
        )

    if target == OrderStatus.IN_PREPARATION and order.sent_to_kitchen_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette commande n'a pas encore été envoyée en cuisine",
        )

    order.status = target
    if target == OrderStatus.IN_PREPARATION:
        order.preparation_started_at = now
    elif target == OrderStatus.READY:
        order.ready_at = now
    elif target == OrderStatus.SERVED:
        table = db.query(RestaurantTable).filter(RestaurantTable.id == order.table_id).first()
        if table:
            table.status = TableStatus.FREE

    db.commit()
    db.refresh(order)
    return order