import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Category } from './category.service';

export interface MenuItem {
  id: number;
  name: string;
  description: string | null;
  price: number;
  available: boolean;
  category_id: number | null;
  category: Category | null;
}

export interface MenuItemCreate {
  name: string;
  description?: string;
  price: number;
  category_id?: number;
  available: boolean;
}

export type MenuItemUpdate = Partial<MenuItemCreate>;

@Injectable({ providedIn: 'root' })
export class MenuItemService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/menu-items`;

  list(categoryId?: number, availableOnly = false) {
    let url = `${this.baseUrl}/?`;
    if (categoryId) url += `category_id=${categoryId}&`;
    if (availableOnly) url += `available_only=true`;
    return this.http.get<MenuItem[]>(url);
  }

  create(payload: MenuItemCreate) {
    return this.http.post<MenuItem>(`${this.baseUrl}/`, payload);
  }

  update(id: number, payload: MenuItemUpdate) {
    return this.http.put<MenuItem>(`${this.baseUrl}/${id}`, payload);
  }

  delete(id: number) {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}