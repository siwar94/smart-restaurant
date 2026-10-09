import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export interface Category {
  id: number;
  name: string;
}

@Injectable({ providedIn: 'root' })
export class CategoryService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/categories`;

  list() {
    return this.http.get<Category[]>(`${this.baseUrl}/`);
  }

  create(name: string) {
    return this.http.post<Category>(`${this.baseUrl}/`, { name });
  }

  update(id: number, name: string) {
    return this.http.put<Category>(`${this.baseUrl}/${id}`, { name });
  }

  delete(id: number) {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}