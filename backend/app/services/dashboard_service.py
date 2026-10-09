from datetime import datetime, time, timezone
from decimal import Decimal
from typing import List
from app.schemas.dashboard import (
    DashboardSummary,
    TopMenuItem,
    PreparationStats,
    OrdersByDayPoint,
    PeakHourPoint,
)

from sqlalchemy import func, case
from sqlalchemy.orm import Session
from datetime import timedelta
from sqlalchemy import case

from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.menu_item import MenuItem
from app.models.restaurant_table import RestaurantTable, TableStatus
from app.schemas.dashboard import DashboardSummary, TopMenuItem, PreparationStats


def _today_bounds():
    """Bornes UTC du jour courant (00:00 -> 23:59:59)."""
    now = datetime.now(timezone.utc)
    start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
    return start, end


def get_summary(db: Session) -> DashboardSummary:
    start, end = _today_bounds()

    orders_today = (
        db.query(func.count(Order.id))
        .filter(Order.created_at.between(start, end))
        .scalar()
    )

    orders_in_progress = (
        db.query(func.count(Order.id))
        .filter(Order.status.in_([OrderStatus.NEW, OrderStatus.IN_PREPARATION]))
        .scalar()
    )

    orders_ready = (
        db.query(func.count(Order.id))
        .filter(Order.status == OrderStatus.READY)
        .scalar()
    )

    orders_served_today = (
        db.query(func.count(Order.id))
        .filter(
            Order.status == OrderStatus.SERVED,
            Order.created_at.between(start, end),
        )
        .scalar()
    )

    revenue_today = (
        db.query(func.coalesce(func.sum(Order.total), 0))
        .filter(
            Order.status == OrderStatus.SERVED,
            Order.created_at.between(start, end),
        )
        .scalar()
    )

    occupied_tables = (
        db.query(func.count(RestaurantTable.id))
        .filter(RestaurantTable.status == TableStatus.OCCUPIED)
        .scalar()
    )

    total_tables = db.query(func.count(RestaurantTable.id)).scalar()

    return DashboardSummary(
        orders_today=orders_today or 0,
        orders_in_progress=orders_in_progress or 0,
        orders_ready=orders_ready or 0,
        orders_served_today=orders_served_today or 0,
        revenue_today=Decimal(revenue_today or 0),
        occupied_tables=occupied_tables or 0,
        total_tables=total_tables or 0,
    )


def get_top_items(db: Session, limit: int = 5) -> List[TopMenuItem]:
    rows = (
        db.query(
            MenuItem.id,
            MenuItem.name,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("total_revenue"),
        )
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status == OrderStatus.SERVED)
        .group_by(MenuItem.id, MenuItem.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )

    return [
        TopMenuItem(
            menu_item_id=r.id,
            name=r.name,
            total_quantity=int(r.total_quantity),
            total_revenue=Decimal(r.total_revenue),
        )
        for r in rows
    ]


def get_preparation_stats(db: Session) -> PreparationStats:
    """RM/BF12 : temps moyen de préparation, calculé à partir des timestamps
    déjà présents sur Order (sent_to_kitchen_at, preparation_started_at, ready_at)."""

    # Durée "préparation active" = ready_at - preparation_started_at
    prep_seconds = func.extract(
        "epoch", Order.ready_at - Order.preparation_started_at
    )
    # Durée "totale cuisine" = ready_at - sent_to_kitchen_at
    total_seconds = func.extract(
        "epoch", Order.ready_at - Order.sent_to_kitchen_at
    )

    result = (
        db.query(
            func.avg(prep_seconds).label("avg_prep"),
            func.avg(total_seconds).label("avg_total"),
            func.count(Order.id).label("measured"),
        )
        .filter(
            Order.ready_at.isnot(None),
            Order.preparation_started_at.isnot(None),
            Order.sent_to_kitchen_at.isnot(None),
        )
        .one()
    )

    return PreparationStats(
        average_preparation_seconds=float(result.avg_prep) if result.avg_prep is not None else None,
        average_total_seconds=float(result.avg_total) if result.avg_total is not None else None,
        orders_measured=result.measured or 0,
    )


def get_orders_by_day(db: Session, days: int = 14) -> List[OrdersByDayPoint]:
    """Historique des commandes et du CA jour par jour, sur les `days` derniers jours
    (jours sans commande inclus avec des valeurs à zéro)."""
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days - 1)

    rows = (
        db.query(
            func.date(Order.created_at).label("day"),
            func.count(Order.id).label("orders_count"),
            func.coalesce(
                func.sum(case((Order.status == OrderStatus.SERVED, Order.total), else_=0)),
                0,
            ).label("revenue"),
        )
        .filter(func.date(Order.created_at) >= start_date)
        .group_by(func.date(Order.created_at))
        .all()
    )

    by_day = {row.day: row for row in rows}

    result = []
    current = start_date
    while current <= end_date:
        row = by_day.get(current)
        result.append(
            OrdersByDayPoint(
                date=current.isoformat(),
                orders_count=int(row.orders_count) if row else 0,
                revenue=Decimal(row.revenue) if row else Decimal("0"),
            )
        )
        current += timedelta(days=1)

    return result


def get_peak_hours(db: Session) -> List[PeakHourPoint]:
    """Répartition du nombre de commandes par heure de la journée (0-23),
    toutes dates confondues, pour repérer les heures de pointe."""
    rows = (
        db.query(
            func.extract("hour", Order.created_at).label("hour"),
            func.count(Order.id).label("orders_count"),
        )
        .group_by(func.extract("hour", Order.created_at))
        .all()
    )

    by_hour = {int(row.hour): int(row.orders_count) for row in rows}

    return [PeakHourPoint(hour=h, orders_count=by_hour.get(h, 0)) for h in range(24)]