import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.component')
        .then(m => m.LoginComponent)
  },

  {
    path: 'admin',
    loadChildren: () =>
      import('./features/admin/admin.routes')
        .then(m => m.ADMIN_ROUTES)
  },

  {
    path: 'serveur',
    loadChildren: () =>
      import('./features/serveur/serveur.routes')
        .then(m => m.SERVEUR_ROUTES)
  },

  {
    path: 'cuisine',
    loadChildren: () =>
      import('./features/cuisine/cuisine.routes')
        .then(m => m.CUISINE_ROUTES)
  },

  {
    path: '**',
    redirectTo: 'login'
  }
];