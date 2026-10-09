import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators
} from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';
import { UserRole } from '../../../core/models/user.model';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  loading = signal(false);
  errorMessage = signal<string | null>(null);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set(null);

    const email = this.form.value.email ?? '';
    const password = this.form.value.password ?? '';

    this.authService.login({
      email,
      password,
    }).subscribe({
      next: () => {
        console.log('LOGIN OK');
        console.log('Role:', this.authService.role());

        this.redirectByRole();
      },

      error: (error) => {
        console.error('LOGIN ERROR:', error);

        this.errorMessage.set(
          error?.error?.detail ||
          'Email ou mot de passe incorrect'
        );

        this.loading.set(false);
      },

      complete: () => {
        console.log('LOGIN REQUEST COMPLETE');
        this.loading.set(false);
      }
    });
  }

  private redirectByRole(): void {
    const role = this.authService.role();

    console.log('Redirect avec role:', role);

    switch (role) {
      case UserRole.ADMIN:
        this.router.navigate(['/admin/dashboard']);
        break;

      case UserRole.SERVEUR:
        this.router.navigate(['/serveur/tables']);
        break;

      case UserRole.CUISINE:
        this.router.navigate(['/cuisine/orders']);
        break;

      default:
        console.error('Role inconnu:', role);
        this.errorMessage.set('Rôle utilisateur invalide.');
        this.loading.set(false);
        this.router.navigate(['/login']);
        break;
    }
  }
}