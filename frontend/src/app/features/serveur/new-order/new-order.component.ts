import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription, switchMap } from 'rxjs';
import { MenuItemService, MenuItem } from '../../../core/services/menu-item.service';
import { CategoryService, Category } from '../../../core/services/category.service';
import { OrderService } from '../../../core/services/order.service';
import { AiService, RecommendationItem } from '../../../core/services/ai.service';
import { RealtimeService } from '../../../core/services/realtime.service';

interface CartLine {
  item: MenuItem;
  quantity: number;
}

@Component({
  selector: 'app-new-order',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './new-order.component.html',
  styleUrl: './new-order.component.scss',
})
export class NewOrderComponent implements OnInit, OnDestroy {
  private menuItemService = inject(MenuItemService);
  private categoryService = inject(CategoryService);
  private orderService = inject(OrderService);
  private aiService = inject(AiService);
  private realtimeService = inject(RealtimeService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  tableId = Number(this.route.snapshot.paramMap.get('tableId'));

  categories = signal<Category[]>([]);
  items = signal<MenuItem[]>([]);
  cart = signal<Map<number, CartLine>>(new Map());
  suggestions = signal<RecommendationItem[]>([]);
  submitting = signal(false);

  private realtimeSub?: Subscription;

  total = computed(() => {
    let sum = 0;
    for (const line of this.cart().values()) {
      sum += line.item.price * line.quantity;
    }
    return sum;
  });

  ngOnInit(): void {
    this.categoryService.list().subscribe((res) => this.categories.set(res));
    // On charge TOUS les plats (pas seulement les disponibles), pour pouvoir
    // afficher ceux indisponibles grisés plutôt que de les faire disparaître.
    this.menuItemService.list().subscribe((res) => this.items.set(res));

    this.realtimeSub = this.realtimeService.messages$.subscribe((msg) => {
      if (msg.type === 'menu_item_availability_changed') {
        this.items.update((list) =>
          list.map((i) =>
            i.id === msg.menu_item_id ? { ...i, available: msg.available! } : i
          )
        );
      }
    });
  }

  ngOnDestroy(): void {
    this.realtimeSub?.unsubscribe();
  }

  itemsForCategory(categoryId: number): MenuItem[] {
    return this.items().filter((i) => i.category_id === categoryId);
  }

  quantityOf(itemId: number): number {
    return this.cart().get(itemId)?.quantity ?? 0;
  }

  add(item: MenuItem): void {
    if (!item.available) return; // sécurité : ne jamais ajouter un plat devenu indisponible

    const map = new Map(this.cart());
    const existing = map.get(item.id);
    map.set(item.id, { item, quantity: (existing?.quantity ?? 0) + 1 });
    this.cart.set(map);

    this.aiService.getRecommendationsForItem(item.id).subscribe({
      next: (res) => this.suggestions.set(res.filter((r) => !this.cart().has(r.menu_item_id))),
      error: () => this.suggestions.set([]),
    });
  }

  remove(item: MenuItem): void {
    const map = new Map(this.cart());
    const existing = map.get(item.id);
    if (!existing) return;
    if (existing.quantity <= 1) {
      map.delete(item.id);
    } else {
      map.set(item.id, { item, quantity: existing.quantity - 1 });
    }
    this.cart.set(map);
  }

  addSuggestion(rec: RecommendationItem): void {
    const item = this.items().find((i) => i.id === rec.menu_item_id);
    if (item) this.add(item);
  }

  sendToKitchen(): void {
    if (this.cart().size === 0) return;

    // Garde-fou : un plat ajouté puis rendu indisponible entre-temps
    // (avant l'envoi) ne doit pas partir en commande.
    const unavailableInCart = Array.from(this.cart().values()).filter((l) => !l.item.available);
    if (unavailableInCart.length > 0) {
      alert(
        `Ces plats ne sont plus disponibles, retire-les avant d'envoyer : ` +
          unavailableInCart.map((l) => l.item.name).join(', ')
      );
      return;
    }

    this.submitting.set(true);

    const payload = {
      table_id: this.tableId,
      items: Array.from(this.cart().values()).map((line) => ({
        menu_item_id: line.item.id,
        quantity: line.quantity,
      })),
    };

    this.orderService
      .create(payload)
      .pipe(switchMap((order) => this.orderService.sendToKitchen(order.id)))
      .subscribe({
        next: () => this.router.navigate(['/serveur/orders']),
        error: () => this.submitting.set(false),
      });
  }
}