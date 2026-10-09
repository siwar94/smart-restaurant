import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { TableService, RestaurantTable } from '../../../core/services/table.service';

@Component({
  selector: 'app-tables',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './tables.component.html',
  styleUrl: './tables.component.scss',
})
export class TablesComponent implements OnInit {
  private tableService = inject(TableService);
  private fb = inject(FormBuilder);

  tables = signal<RestaurantTable[]>([]);
  loading = signal(true);

  form = this.fb.group({
    number: [null as number | null, Validators.required],
  });

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

  onSubmit(): void {
    if (this.form.invalid) return;
    this.tableService.create({ number: this.form.value.number! }).subscribe(() => {
      this.form.reset();
      this.loadTables();
    });
  }

  deleteTable(id: number): void {
    if (!confirm('Supprimer cette table ?')) return;
    this.tableService.delete(id).subscribe(() => this.loadTables());
  }
}