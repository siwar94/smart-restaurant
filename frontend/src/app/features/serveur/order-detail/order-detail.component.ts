import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { OrderService, Order, OrderStatus } from '../../../core/services/order.service';

@Component({
  selector: 'app-order-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './order-detail.component.html',
  styleUrl: './order-detail.component.scss',
})
export class OrderDetailComponent implements OnInit {
  private orderService = inject(OrderService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  order = signal<Order | null>(null);
  OrderStatus = OrderStatus;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.orderService.get(id).subscribe((res) => this.order.set(res));
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

  markServed(): void {
    const current = this.order();
    if (!current) return;
    this.orderService.updateStatus(current.id, OrderStatus.SERVED).subscribe((res) => this.order.set(res));
  }

  cancelOrder(): void {
    const current = this.order();
    if (!current) return;
    if (!confirm('Annuler cette commande ?')) return;

    this.orderService.cancel(current.id).subscribe({
      next: (res) => this.order.set(res),
      error: (err) => alert(`Erreur : ${err.error?.detail ?? 'impossible d\'annuler la commande'}`),
    });
  }
}
