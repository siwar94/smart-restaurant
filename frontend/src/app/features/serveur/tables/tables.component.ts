import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TableService, RestaurantTable, TableStatus } from '../../../core/services/table.service';

@Component({
  selector: 'app-serveur-tables',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tables.component.html',
  styleUrl: './tables.component.scss',
})
export class TablesComponent implements OnInit {
  private tableService = inject(TableService);
  private router = inject(Router);

  tables = signal<RestaurantTable[]>([]);
  loading = signal(true);
  TableStatus = TableStatus;

  ngOnInit(): void {
    this.loadTables();
  }

  loadTables(): void {
    this.loading.set(true);
    this.tableService.list().subscribe({
      next: (res) => {
        this.tables.set(res);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  selectTable(table: RestaurantTable): void {
    this.router.navigate(['/serveur/tables', table.id, 'new-order']);
  }

  freeTable(table: RestaurantTable, event: Event): void {
    event.stopPropagation();
    if (!confirm(`Le client de la table ${table.number} est-il parti ?`)) return;

    this.tableService.update(table.id, { status: TableStatus.FREE }).subscribe({
      next: () => this.loadTables(),
      error: (err) => alert(`Erreur : ${err.error?.detail ?? 'impossible de libérer la table'}`),
    });
  }
}