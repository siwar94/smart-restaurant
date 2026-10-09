import {
  Component,
  OnInit,
  inject,
  signal,
  computed,
} from '@angular/core';

import { CommonModule } from '@angular/common';

import {
  DashboardService,
  AnalyticsData,
} from '../../../core/services/dashboard.service';

import {
  AiService,
  ItemRecommendations,
} from '../../../core/services/ai.service';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analytics.component.html',
  styleUrl: './analytics.component.scss',
})
export class AnalyticsComponent implements OnInit {

  // Services
  private dashboardService = inject(DashboardService);
  private aiService = inject(AiService);

  // Données analytics
  data = signal<AnalyticsData | null>(null);
  loading = signal(true);

  // Recommandations / associations IA
  associations = signal<ItemRecommendations[]>([]);
  associationsUnavailable = signal(false);

  // Maximum commandes par jour
  maxDailyOrders = computed(() => {
    const points = this.data()?.orders_by_day ?? [];

    return Math.max(
      1,
      ...points.map((p) => p.orders_count)
    );
  });

  // Maximum commandes par heure
  maxHourlyOrders = computed(() => {
    const points = this.data()?.peak_hours ?? [];

    return Math.max(
      1,
      ...points.map((p) => p.orders_count)
    );
  });

  ngOnInit(): void {

    // =========================
    // ANALYTICS
    // =========================

    this.dashboardService.getAnalytics(14).subscribe({
      next: (res) => {
        this.data.set(res);
        this.loading.set(false);
      },

      error: () => {
        this.loading.set(false);
      },
    });

    // =========================
    // RECOMMANDATIONS IA
    // =========================

    this.aiService.getAllRecommendations().subscribe({
      next: (res) => {
        this.associations.set(res);
        this.associationsUnavailable.set(false);
      },

      error: () => {
        this.associationsUnavailable.set(true);
      },
    });
  }

  // Hauteur des barres du graphique
  barHeight(value: number, max: number): string {
    return `${Math.max(4, (value / max) * 100)}%`;
  }

  // Format date
  shortDate(iso: string): string {
    const d = new Date(iso);

    return d.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
    });
  }

  // Format heure
  hourLabel(hour: number): string {
    return `${hour}h`;
  }
}