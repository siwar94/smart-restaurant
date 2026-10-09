import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { UserService } from '../../../core/services/user.service';
import { User, UserRole } from '../../../core/models/user.model';

@Component({
  selector: 'app-users',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './users.component.html',
  styleUrl: './users.component.scss',
})
export class UsersComponent implements OnInit {
  private userService = inject(UserService);
  private fb = inject(FormBuilder);

  users = signal<User[]>([]);
  roles = Object.values(UserRole);
  showForm = signal(false);

  form = this.fb.group({
    name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
    role: [UserRole.SERVEUR, Validators.required],
  });

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.userService.list().subscribe((res) => this.users.set(res));
  }

  toggleForm(): void {
    this.showForm.update((v) => !v);
  }

  onSubmit(): void {
  if (this.form.invalid) return;

  const raw = this.form.getRawValue();
  this.userService
    .create({
      name: raw.name!,
      email: raw.email!,
      password: raw.password!,
      role: raw.role!,
    })
    .subscribe(() => {
      this.form.reset({ role: UserRole.SERVEUR });
      this.showForm.set(false);
      this.loadUsers();
    });
}

  deactivate(user: User): void {
    if (!confirm(`Désactiver ${user.name} ?`)) return;
    this.userService.update(user.id, { is_active: false }).subscribe(() => this.loadUsers());
  }
  initials(name: string): string {
    return name
      .split(' ')
      .map((part) => part[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }
}