import { Component, inject } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-cuisine-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './cuisine-layout.component.html',
  styleUrl: './cuisine-layout.component.scss',
})
export class CuisineLayoutComponent {
  authService = inject(AuthService);
  sidebarOpen = false;

  logout(): void {
    this.authService.logout();
  }
}