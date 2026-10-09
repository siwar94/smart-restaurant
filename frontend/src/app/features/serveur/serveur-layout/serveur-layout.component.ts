import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { Subscription } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { RealtimeService } from '../../../core/services/realtime.service';
import { NotificationService } from '../../../core/services/notification.service';
import { TableService, RestaurantTable } from '../../../core/services/table.service';
import { ToastComponent } from '../../../shared/toast/toast.component';

@Component({
  selector: 'app-serveur-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, ToastComponent],
  templateUrl: './serveur-layout.component.html',
  styleUrl: './serveur-layout.component.scss',
})
export class ServeurLayoutComponent implements OnInit, OnDestroy {
  authService = inject(AuthService);
  private realtimeService = inject(RealtimeService);
  private notificationService = inject(NotificationService);
  private tableService = inject(TableService);

  sidebarOpen = false;

  private tablesById = new Map<number, RestaurantTable>();
  private realtimeSub?: Subscription;

  ngOnInit(): void {
    this.tableService.list().subscribe((tables) => {
      this.tablesById = new Map(tables.map((t) => [t.id, t]));
    });

    this.realtimeSub = this.realtimeService.messages$.subscribe((msg) => {
      if (msg.type === 'order_status_updated' && msg.status === 'READY' && msg.table_id !== undefined) {
        const tableNumber = this.tablesById.get(msg.table_id)?.number ?? msg.table_id;
        this.notificationService.push(`Commande prête — Table ${tableNumber} 🍽️`);
        this.playNotificationSound();
      }
    });
  }

  ngOnDestroy(): void {
    this.realtimeSub?.unsubscribe();
  }

  logout(): void {
    this.authService.logout();
  }

  private playNotificationSound(): void {
    try {
      const ctx = new AudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    } catch {
      // ignore
    }
  }
}