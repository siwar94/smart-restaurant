import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardService, DashboardData, TopMenuItem } from '../../../core/services/dashboard.service';
import { AiService, DemandForecast } from '../../../core/services/ai.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private dashboardService = inject(DashboardService);
  private aiService = inject(AiService);

  data = signal<DashboardData | null>(null);
  loading = signal(true);

  forecast = signal<DemandForecast | null>(null);
  forecastUnavailable = signal(false);

  ngOnInit(): void {
    this.dashboardService.getDashboard().subscribe({
      next: (res) => {
        this.data.set(res);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });

    this.aiService.getDemandForecast().subscribe({
      next: (res) => this.forecast.set(res),
      error: () => this.forecastUnavailable.set(true),
    });
  }

  formatMinutes(seconds: number | null): string {
    if (seconds === null) return '—';
    return `${Math.round(seconds / 60)} min`;
  }

  maxPredicted(): number {
    const items = this.forecast()?.items ?? [];
    return Math.max(1, ...items.map((i) => i.predicted_quantity));
  }

  barWidth(qty: number): string {
    return `${(qty / this.maxPredicted()) * 100}%`;
  }

  shareWidth(quantity: number, items: TopMenuItem[]): string {
    const max = Math.max(1, ...items.map((i) => i.total_quantity));
    return `${(quantity / max) * 100}%`;
  }
}