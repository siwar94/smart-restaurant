import { Routes } from '@angular/router';

export const CUISINE_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./cuisine-layout/cuisine-layout.component').then((m) => m.CuisineLayoutComponent),
    children: [
      { path: 'orders', loadComponent: () => import('./kitchen-board/kitchen-board.component').then((m) => m.KitchenBoardComponent) },
      { path: '', redirectTo: 'orders', pathMatch: 'full' },
    ],
  },
];