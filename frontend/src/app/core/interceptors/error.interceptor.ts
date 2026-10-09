import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);

  return next(req).pipe(
    catchError((err) => {
      const isAuthMissing = err.status === 401 || (err.status === 403 && err.error?.detail === 'Not authenticated');
      if (isAuthMissing) {
        authService.logout();
      }
      return throwError(() => err);
    })
  );
};