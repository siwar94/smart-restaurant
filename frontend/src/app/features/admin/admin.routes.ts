import { Routes } from '@angular/router';

export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./admin-layout/admin-layout.component').then((m) => m.AdminLayoutComponent),
    children: [
      { path: 'dashboard', loadComponent: () => import('./dashboard/dashboard.component').then((m) => m.DashboardComponent) },
      { path: 'analytics', loadComponent: () => import('./analytics/analytics.component').then((m) => m.AnalyticsComponent) },
      { path: 'users', loadComponent: () => import('./users/users.component').then((m) => m.UsersComponent) },
      { path: 'tables', loadComponent: () => import('./tables/tables.component').then((m) => m.TablesComponent) },
      { path: 'menu', loadComponent: () => import('./menu/menu.component').then((m) => m.MenuComponent) },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    ],
  },
];