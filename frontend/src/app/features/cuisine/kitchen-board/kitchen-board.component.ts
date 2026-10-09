import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { interval, Subscription, switchMap, startWith } from 'rxjs';
import { OrderService, Order, OrderStatus } from '../../../core/services/order.service';
import { TableService, RestaurantTable } from '../../../core/services/table.service';
import { RealtimeService } from '../../../core/services/realtime.service';

@Component({
  selector: 'app-kitchen-board',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './kitchen-board.component.html',
  styleUrl: './kitchen-board.component.scss',
})
export class KitchenBoardComponent implements OnInit, OnDestroy {
  private orderService = inject(OrderService);
  private tableService = inject(TableService);
  private realtimeService = inject(RealtimeService);

  orders = signal<Order[]>([]);
  tablesById = signal<Map<number, RestaurantTable>>(new Map());
  private pollSub?: Subscription;
  private realtimeSub?: Subscription;

  newOrders = computed(() => this.orders().filter((o) => o.status === OrderStatus.NEW));
  inPrepOrders = computed(() => this.orders().filter((o) => o.status === OrderStatus.IN_PREPARATION));
  readyOrders = computed(() => this.orders().filter((o) => o.status === OrderStatus.READY));

  ngOnInit(): void {
    this.tableService.list().subscribe((tables) => {
      this.tablesById.set(new Map(tables.map((t) => [t.id, t])));
    });

    this.pollSub = interval(20000)
      .pipe(
        startWith(0),
        switchMap(() => this.orderService.list({ kitchenView: true }))
      )
      .subscribe((res) => this.orders.set(res));

    this.realtimeSub = this.realtimeService.messages$.subscribe((msg) => {
      if (
        msg.type === 'order_created' ||
        msg.type === 'order_sent_to_kitchen' ||
        msg.type === 'order_status_updated'
      ) {
        this.orderService.list({ kitchenView: true }).subscribe((res) => this.orders.set(res));
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

  elapsedMinutes(order: Order): number {
    const start = order.sent_to_kitchen_at ?? order.created_at;
    return Math.floor((Date.now() - new Date(start).getTime()) / 60000);
  }

  startPreparation(order: Order): void {
    this.orderService.updateStatus(order.id, OrderStatus.IN_PREPARATION).subscribe({
      next: (updated) => {
        this.orders.update((list) => list.map((o) => (o.id === order.id ? updated : o)));
      },
      error: (err) => {
        alert(`Erreur : ${err.error?.detail ?? 'impossible de démarrer la préparation'}`);
        console.error(err);
      },
    });
  }

  markReady(order: Order): void {
    this.orderService.updateStatus(order.id, OrderStatus.READY).subscribe({
      next: (updated) => {
        this.orders.update((list) => list.map((o) => (o.id === order.id ? updated : o)));
      },
      error: (err) => {
        alert(`Erreur : ${err.error?.detail ?? 'impossible de marquer la commande prête'}`);
        console.error(err);
      },
    });
  }
}