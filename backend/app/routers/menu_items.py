from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.ws_manager import manager
from app.database.session import get_db
from app.core.deps import require_role, get_current_user
from app.models.user import User, UserRole
from app.models.menu_item import MenuItem
from app.models.category import Category
from app.schemas.menu_item import (
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemOut,
)


router = APIRouter(
    prefix="/menu-items",
    tags=["Menu Items"],
)


@router.get("/", response_model=List[MenuItemOut])
def list_menu_items(
    category_id: Optional[int] = None,
    available_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MenuItem)

    if category_id is not None:
        query = query.filter(MenuItem.category_id == category_id)

    if available_only:
        query = query.filter(MenuItem.available == True)

    return query.order_by(MenuItem.name).all()


@router.get("/{item_id}", response_model=MenuItemOut)
def get_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(MenuItem)
        .filter(MenuItem.id == item_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Plat introuvable",
        )

    return item


@router.post(
    "/",
    response_model=MenuItemOut,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_item(
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    if payload.category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == payload.category_id)
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=400,
                detail="Catégorie invalide",
            )

    new_item = MenuItem(
        **payload.model_dump()
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


@router.put(
    "/{item_id}",
    response_model=MenuItemOut,
)
async def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    """
    Modifier un plat.

    Si la disponibilité du plat change,
    une notification WebSocket est envoyée
    aux serveurs et aux administrateurs.
    """

    item = (
        db.query(MenuItem)
        .filter(MenuItem.id == item_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Plat introuvable",
        )

    # Récupère uniquement les champs réellement
    # envoyés dans la requête.
    update_data = payload.model_dump(
        exclude_unset=True
    )

    # Vérification de la catégorie si elle est modifiée.
    if (
        "category_id" in update_data
        and update_data["category_id"] is not None
    ):
        category = (
            db.query(Category)
            .filter(
                Category.id == update_data["category_id"]
            )
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=400,
                detail="Catégorie invalide",
            )

    # Vérifie si la disponibilité va réellement changer.
    availability_changed = (
        "available" in update_data
        and update_data["available"] != item.available
    )

    # Applique les modifications.
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    # Notification uniquement si la disponibilité
    # du plat a changé.
    if availability_changed:
        recipients = [
            user_id
            for user_id, in (
                db.query(User.id)
                .filter(
                    User.role.in_(
                        [
                            UserRole.SERVEUR,
                            UserRole.ADMIN,
                        ]
                    )
                )
                .all()
            )
        ]

        await manager.broadcast_to_roles(
            {
                "type": "menu_item_availability_changed",
                "menu_item_id": item.id,
                "menu_item_name": item.name,
                "available": item.available,
            },
            recipients,
        )

    return item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    item = (
        db.query(MenuItem)
        .filter(MenuItem.id == item_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Plat introuvable",
        )

    db.delete(item)
    db.commit()

    return None

