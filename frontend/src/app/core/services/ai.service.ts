import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export interface DemandForecastItem {
  menu_item_id: number;
  menu_item_name: string;
  predicted_quantity: number;
}

export interface DemandForecast {
  date: string;
  items: DemandForecastItem[];
}

@Injectable({ providedIn: 'root' })
export class AiService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/ai`;

  getDemandForecast(targetDate?: string) {
    const query = targetDate ? `?target_date=${targetDate}` : '';
    return this.http.get<DemandForecast>(`${this.baseUrl}/demand-forecast${query}`);
  }
getRecommendationsForItem(menuItemId: number) {
  return this.http.get<RecommendationItem[]>(`${this.baseUrl}/recommendations/${menuItemId}`);
}

getAllRecommendations() {
  return this.http.get<ItemRecommendations[]>(`${this.baseUrl}/recommendations`);
}
}
export interface RecommendationItem {
  menu_item_id: number;
  menu_item_name: string;
  confidence: number;
  lift: number;
  support: number;
}

export interface ItemRecommendations {
  menu_item_id: number;
  menu_item_name: string;
  recommendations: RecommendationItem[];
}