import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export interface DashboardSummary {
  orders_today: number;
  orders_in_progress: number;
  orders_ready: number;
  orders_served_today: number;
  revenue_today: number;
  occupied_tables: number;
  total_tables: number;
}

export interface TopMenuItem {
  menu_item_id: number;
  name: string;
  total_quantity: number;
  total_revenue: number;
}

export interface PreparationStats {
  average_preparation_seconds: number | null;
  average_total_seconds: number | null;
  orders_measured: number;
}

export interface DashboardData {
  summary: DashboardSummary;
  top_items: TopMenuItem[];
  preparation: PreparationStats;
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/dashboard`;

  getDashboard(topLimit = 5) {
    return this.http.get<DashboardData>(`${this.baseUrl}/?top_limit=${topLimit}`);
  }
 getAnalytics(days = 14) {
  return this.http.get<AnalyticsData>(`${this.baseUrl}/analytics?days=${days}`);
}
}

export interface OrdersByDayPoint {
  date: string;
  orders_count: number;
  revenue: number;
}

export interface PeakHourPoint {
  hour: number;
  orders_count: number;
}

export interface AnalyticsData {
  orders_by_day: OrdersByDayPoint[];
  peak_hours: PeakHourPoint[];
}