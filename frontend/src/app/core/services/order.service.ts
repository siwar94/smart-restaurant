import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export enum OrderStatus {
  NEW = 'NEW',
  IN_PREPARATION = 'IN_PREPARATION',
  READY = 'READY',
  SERVED = 'SERVED',
  CANCELLED = 'CANCELLED',
}

export interface OrderItemOut {
  id: number;
  menu_item_id: number;
  menu_item_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Order {
  id: number;
  table_id: number;
  server_id: number;
  status: OrderStatus;
  total: number;
  created_at: string;
  sent_to_kitchen_at: string | null;
  preparation_started_at: string | null;
  ready_at: string | null;
  items: OrderItemOut[];
}

export interface OrderItemCreate {
  menu_item_id: number;
  quantity: number;
}

export interface OrderCreate {
  table_id: number;
  items: OrderItemCreate[];
}

export interface OrderListParams {
  statusFilter?: OrderStatus;
  tableId?: number;
  mineOnly?: boolean;
  kitchenView?: boolean;
}

@Injectable({ providedIn: 'root' })
export class OrderService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/orders`;

  create(payload: OrderCreate) {
    return this.http.post<Order>(`${this.baseUrl}/`, payload);
  }

  list(params: OrderListParams = {}) {
    const query = new URLSearchParams();
    if (params.statusFilter) query.set('status_filter', params.statusFilter);
    if (params.tableId) query.set('table_id', String(params.tableId));
    if (params.mineOnly) query.set('mine_only', 'true');
    if (params.kitchenView) query.set('kitchen_view', 'true');
    return this.http.get<Order[]>(`${this.baseUrl}/?${query.toString()}`);
  }

  get(id: number) {
    return this.http.get<Order>(`${this.baseUrl}/${id}`);
  }

  replaceItems(id: number, items: OrderItemCreate[]) {
    return this.http.put<Order>(`${this.baseUrl}/${id}/items`, { items });
  }

  sendToKitchen(id: number) {
    return this.http.post<Order>(`${this.baseUrl}/${id}/send-to-kitchen`, {});
  }

  updateStatus(id: number, status: OrderStatus) {
    return this.http.put<Order>(`${this.baseUrl}/${id}/status`, { status });
  }
  cancel(id: number) {
    return this.http.post<Order>(`${this.baseUrl}/${id}/cancel`, {});
  }
}