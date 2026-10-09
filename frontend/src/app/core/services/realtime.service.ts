import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface RealtimeMessage {
  type:
    | 'order_created'
    | 'order_sent_to_kitchen'
    | 'order_status_updated'
    | 'order_cancelled'
    | 'menu_item_availability_changed';

  order_id?: number;
  table_id?: number;
  status?: string;

  menu_item_id?: number;
  menu_item_name?: string;
  available?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class RealtimeService {
  private socket?: WebSocket;

  private reconnectDelay = 3000;
  private shouldReconnect = false;

  messages$ = new Subject<RealtimeMessage>();

  connect(token: string): void {
    this.shouldReconnect = true;
    this.openSocket(token);
  }

  disconnect(): void {
    this.shouldReconnect = false;

    this.socket?.close();
    this.socket = undefined;
  }

  private openSocket(token: string): void {
    this.socket = new WebSocket(
      `${environment.wsUrl}/ws?token=${token}`
    );

    this.socket.onopen = () => {
      console.log('WebSocket connecté');
    };

    this.socket.onmessage = (event) => {
      try {
        const message: RealtimeMessage = JSON.parse(
          event.data
        );

        this.messages$.next(message);
      } catch {
        // Message malformé : on ignore.
        console.warn(
          'Message WebSocket invalide reçu'
        );
      }
    };

    this.socket.onclose = () => {
      console.log('WebSocket déconnecté');

      if (this.shouldReconnect) {
        setTimeout(() => {
          this.openSocket(token);
        }, this.reconnectDelay);
      }
    };

    this.socket.onerror = () => {
      console.error('Erreur WebSocket');

      this.socket?.close();
    };
  }
}
