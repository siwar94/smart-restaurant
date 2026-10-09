import { Injectable, signal } from '@angular/core';

export interface ToastMessage {
  id: number;
  text: string;
}

@Injectable({ providedIn: 'root' })
export class NotificationService {
  toasts = signal<ToastMessage[]>([]);
  private nextId = 0;

  push(text: string, durationMs = 6000): void {
    const id = this.nextId++;
    this.toasts.update((list) => [...list, { id, text }]);
    setTimeout(() => this.dismiss(id), durationMs);
  }

  dismiss(id: number): void {
    this.toasts.update((list) => list.filter((t) => t.id !== id));
  }
}