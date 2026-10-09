import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MenuItemService, MenuItem } from '../../../core/services/menu-item.service';
import { CategoryService, Category } from '../../../core/services/category.service';
import { OrderService, OrderStatus } from '../../../core/services/order.service';

interface CartLine {
  item: MenuItem;
  quantity: number;
}

@Component({
  selector: 'app-edit-order',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './edit-order.component.html',
  styleUrl: './edit-order.component.scss',
})
export class EditOrderComponent implements OnInit {
  private menuItemService = inject(MenuItemService);
  private categoryService = inject(CategoryService);
  private orderService = inject(OrderService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  orderId = Number(this.route.snapshot.paramMap.get('id'));
  tableId = signal<number | null>(null);

  categories = signal<Category[]>([]);
  items = signal<MenuItem[]>([]);
  cart = signal<Map<number, CartLine>>(new Map());
  loading = signal(true);
  submitting = signal(false);

  total = computed(() => {
    let sum = 0;
    for (const line of this.cart().values()) {
      sum += line.item.price * line.quantity;
    }
    return sum;
  });

  ngOnInit(): void {
    this.categoryService.list().subscribe((res) => this.categories.set(res));
    this.menuItemService.list(undefined, true).subscribe((res) => {
      this.items.set(res);
      this.loadOrder();
    });
  }

  private loadOrder(): void {
    this.orderService.get(this.orderId).subscribe({
      next: (order) => {
        if (order.status !== OrderStatus.NEW) {
          alert('Cette commande ne peut plus être modifiée : la cuisine a déjà commencé la préparation.');
          this.router.navigate(['/serveur/orders', this.orderId]);
          return;
        }

        this.tableId.set(order.table_id);

        const map = new Map<number, CartLine>();
        for (const line of order.items) {
          let item = this.items().find((i) => i.id === line.menu_item_id);
          if (!item) {
            // Plat devenu indisponible entre-temps : on garde la ligne telle quelle,
            // juste non ré-augmentable (pas dans la liste du menu affiché).
            item = {
              id: line.menu_item_id,
              name: line.menu_item_name,
              description: null,
              price: line.unit_price,
              available: false,
              category_id: null,
              category: null,
            };
          }
          map.set(line.menu_item_id, { item, quantity: line.quantity });
        }
        this.cart.set(map);
        this.loading.set(false);
      },
      error: () => {
        alert('Commande introuvable.');
        this.router.navigate(['/serveur/orders']);
      },
    });
  }

  itemsForCategory(categoryId: number): MenuItem[] {
    return this.items().filter((i) => i.category_id === categoryId);
  }

  quantityOf(itemId: number): number {
    return this.cart().get(itemId)?.quantity ?? 0;
  }

  add(item: MenuItem): void {
    const map = new Map(this.cart());
    const existing = map.get(item.id);
    map.set(item.id, { item, quantity: (existing?.quantity ?? 0) + 1 });
    this.cart.set(map);
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

  saveChanges(): void {
    if (this.cart().size === 0) return;
    this.submitting.set(true);

    const items = Array.from(this.cart().values()).map((line) => ({
      menu_item_id: line.item.id,
      quantity: line.quantity,
    }));

    this.orderService.replaceItems(this.orderId, items).subscribe({
      next: () => this.router.navigate(['/serveur/orders', this.orderId]),
      error: (err) => {
        this.submitting.set(false);
        alert(`Erreur : ${err.error?.detail ?? 'impossible de modifier la commande'}`);
      },
    });
  }
}