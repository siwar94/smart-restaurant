import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { interval, Subscription, switchMap, startWith } from 'rxjs';
import { OrderService, Order, OrderStatus } from '../../../core/services/order.service';
import { TableService, RestaurantTable } from '../../../core/services/table.service';
import { RealtimeService } from '../../../core/services/realtime.service';

@Component({
  selector: 'app-orders',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './orders.component.html',
  styleUrl: './orders.component.scss',
})
export class OrdersComponent implements OnInit, OnDestroy {
  private orderService = inject(OrderService);
  private tableService = inject(TableService);
  private realtimeService = inject(RealtimeService);

  orders = signal<Order[]>([]);
  tablesById = signal<Map<number, RestaurantTable>>(new Map());
  private pollSub?: Subscription;
  private realtimeSub?: Subscription;

  ngOnInit(): void {
    this.tableService.list().subscribe((tables) => {
      this.tablesById.set(new Map(tables.map((t) => [t.id, t])));
    });

    // Filet de sécurité : rafraîchit toutes les 20s même sans événement WebSocket
    this.pollSub = interval(20000)
      .pipe(
        startWith(0),
        switchMap(() => this.orderService.list({ mineOnly: true }))
      )
      .subscribe((res) => this.orders.set(res));

    // Rafraîchissement immédiat dès qu'un événement pertinent arrive
    this.realtimeSub = this.realtimeService.messages$.subscribe((msg) => {
      if (msg.type === 'order_status_updated' || msg.type === 'order_created') {
        this.orderService.list({ mineOnly: true }).subscribe((res) => this.orders.set(res));
      }
    });
  }

  ngOnDestroy(): void {
    this.pollSub?.unsubscribe();
    this.realtimeSub?.unsubscribe();
  }

  tableNumber(tableId: number): number | string {
    return this.tablesById().get(tableId)?.number ?? tableId;
  }

  statusLabel(status: OrderStatus): string {
    const labels: Record<OrderStatus, string> = {
      [OrderStatus.NEW]: 'Nouvelle',
      [OrderStatus.IN_PREPARATION]: 'En préparation',
      [OrderStatus.READY]: 'Prête',
      [OrderStatus.SERVED]: 'Servie',
      [OrderStatus.CANCELLED]: 'Annulée',
    };
    return labels[status];
  }

  statusClass(status: OrderStatus): string {
    const classes: Record<OrderStatus, string> = {
      [OrderStatus.NEW]: 'badge-order-new',
      [OrderStatus.IN_PREPARATION]: 'badge-order-prep',
      [OrderStatus.READY]: 'badge-order-ready',
      [OrderStatus.SERVED]: 'badge-order-served',
      [OrderStatus.CANCELLED]: 'badge-order-cancelled',
    };
    return classes[status];
  }

  markServed(order: Order, event: Event): void {
  event.stopPropagation();
  this.orderService.updateStatus(order.id, OrderStatus.SERVED).subscribe({
    next: () => {
      this.orders.update((list) =>
        list.map((o) => (o.id === order.id ? { ...o, status: OrderStatus.SERVED } : o))
      );
    },
    error: (err) => {
      alert(`Erreur : ${err.error?.detail ?? 'impossible de marquer la commande servie'}`);
      console.error(err);
    },
  });
}
}