from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.order import OrderItemCreate


def build_order_items(db: Session, items_payload: List[OrderItemCreate]) -> List[OrderItem]:
    """RM09 : un plat indisponible ne peut pas être ajouté à une commande."""
    order_items = []
    for item in items_payload:
        menu_item = db.query(MenuItem).filter(MenuItem.id == item.menu_item_id).first()
        if not menu_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plat introuvable (id={item.menu_item_id})",
            )
        if not menu_item.available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le plat '{menu_item.name}' n'est pas disponible",
            )
        order_items.append(
            OrderItem(
                menu_item_id=menu_item.id,
                quantity=item.quantity,
                unit_price=menu_item.price,  # prix figé au moment de la commande
            )
        )
    return order_items


def compute_total(order_items: List[OrderItem]) -> Decimal:
    """RM08 : total calculé automatiquement à partir des prix et quantités."""
    return sum((oi.quantity * oi.unit_price for oi in order_items), Decimal("0"))


def ensure_order_editable(order: Order):
    """RM03 / RM04 : modifiable uniquement avant l'envoi en cuisine."""
    if order.sent_to_kitchen_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette commande a déjà été envoyée en cuisine et ne peut plus être modifiée",
        )