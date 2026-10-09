import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CategoryService, Category } from '../../../core/services/category.service';
import { MenuItemService, MenuItem } from '../../../core/services/menu-item.service';

@Component({
  selector: 'app-menu',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './menu.component.html',
  styleUrl: './menu.component.scss',
})
export class MenuComponent implements OnInit {
  private categoryService = inject(CategoryService);
  private menuItemService = inject(MenuItemService);
  private fb = inject(FormBuilder);

  categories = signal<Category[]>([]);
  items = signal<MenuItem[]>([]);

  categoryForm = this.fb.group({ name: ['', Validators.required] });

  itemForm = this.fb.group({
    name: ['', Validators.required],
    description: [''],
    price: [null as number | null, [Validators.required, Validators.min(0)]],
    category_id: [null as number | null],
    available: [true],
  });

  ngOnInit(): void {
    this.loadCategories();
    this.loadItems();
  }

  loadCategories(): void {
    this.categoryService.list().subscribe((res) => this.categories.set(res));
  }

  loadItems(): void {
    this.menuItemService.list().subscribe((res) => this.items.set(res));
  }

  addCategory(): void {
    if (this.categoryForm.invalid) return;
    this.categoryService.create(this.categoryForm.value.name!).subscribe(() => {
      this.categoryForm.reset();
      this.loadCategories();
    });
  }

  addItem(): void {
    if (this.itemForm.invalid) return;
    const raw = this.itemForm.getRawValue();
    this.menuItemService
      .create({
        name: raw.name!,
        description: raw.description ?? undefined,
        price: raw.price!,
        category_id: raw.category_id ?? undefined,
        available: raw.available!,
      })
      .subscribe(() => {
        this.itemForm.reset({ available: true });
        this.loadItems();
      });
  }

  toggleAvailability(item: MenuItem): void {
    this.menuItemService.update(item.id, { available: !item.available }).subscribe(() => this.loadItems());
  }

  deleteItem(id: number): void {
    if (!confirm('Supprimer ce plat ?')) return;
    this.menuItemService.delete(id).subscribe(() => this.loadItems());
  }
  deleteCategory(category: Category): void {
    if (
      !confirm(
        `Supprimer la catégorie "${category.name}" ? Les plats qui l'utilisent deviendront "Sans catégorie".`
      )
    )
      return;

    this.categoryService.delete(category.id).subscribe({
      next: () => {
        this.loadCategories();
        this.loadItems(); // pour rafraîchir la colonne "Catégorie" des plats concernés
      },
      error: (err) => alert(`Erreur : ${err.error?.detail ?? 'impossible de supprimer la catégorie'}`),
    });
  }
}