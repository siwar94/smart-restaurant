import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export enum TableStatus {
  FREE = 'FREE',
  OCCUPIED = 'OCCUPIED',
}

export interface RestaurantTable {
  id: number;
  number: number;
  status: TableStatus;
}

export interface TableCreate {
  number: number;
}

export interface TableUpdate {
  number?: number;
  status?: TableStatus;
}

@Injectable({ providedIn: 'root' })
export class TableService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/tables`;

  list() {
    return this.http.get<RestaurantTable[]>(`${this.baseUrl}/`);
  }

  create(payload: TableCreate) {
    return this.http.post<RestaurantTable>(`${this.baseUrl}/`, payload);
  }

  update(id: number, payload: TableUpdate) {
    return this.http.put<RestaurantTable>(`${this.baseUrl}/${id}`, payload);
  }

  delete(id: number) {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}