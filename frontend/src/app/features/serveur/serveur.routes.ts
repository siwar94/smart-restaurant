import { Routes } from '@angular/router';

export const SERVEUR_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./serveur-layout/serveur-layout.component').then((m) => m.ServeurLayoutComponent),
    children: [
      { path: 'tables', loadComponent: () => import('./tables/tables.component').then((m) => m.TablesComponent) },
      { path: 'tables/:tableId/new-order', loadComponent: () => import('./new-order/new-order.component').then((m) => m.NewOrderComponent) },
      { path: 'orders', loadComponent: () => import('./orders/orders.component').then((m) => m.OrdersComponent) },
      { path: 'orders/:id', loadComponent: () => import('./order-detail/order-detail.component').then((m) => m.OrderDetailComponent) },
      { path: 'orders/:id/edit', loadComponent: () => import('./edit-order/edit-order.component').then((m) => m.EditOrderComponent) },
      { path: '', redirectTo: 'tables', pathMatch: 'full' },
    ],
  },
];