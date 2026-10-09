import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { jwtDecode } from 'jwt-decode';
import { environment } from '../../../environments/environment';
import { LoginRequest, LoginResponse, User, UserRole } from '../models/user.model';
import { RealtimeService } from './realtime.service';

interface JwtPayload {
  sub: string;
  role: UserRole;
  exp: number;
}

const TOKEN_KEY = 'smart_restaurant_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private realtimeService = inject(RealtimeService);
  private currentUserSignal = signal<User | null>(this.loadUserFromToken());

  currentUser = computed(() => this.currentUserSignal());
  isAuthenticated = computed(() => this.currentUserSignal() !== null);
  role = computed(() => this.currentUserSignal()?.role ?? null);

  constructor(private http: HttpClient, private router: Router) {
    const token = this.getToken();
    if (token && this.currentUserSignal()) {
      this.realtimeService.connect(token);
    }
  }

  login(credentials: LoginRequest): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${environment.apiUrl}/auth/login`, credentials)
      .pipe(
        tap((res) => {
          localStorage.setItem(TOKEN_KEY, res.access_token);
          this.currentUserSignal.set(this.decodeToken(res.access_token));
          this.realtimeService.connect(res.access_token);
        })
      );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.currentUserSignal.set(null);
    this.realtimeService.disconnect();
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  private loadUserFromToken(): User | null {
    const token = this.getToken();
    if (!token) return null;
    const user = this.decodeToken(token);
    if (!user) {
      localStorage.removeItem(TOKEN_KEY);
    }
    return user;
  }

  private decodeToken(token: string): User | null {
    try {
      const payload = jwtDecode<JwtPayload>(token);
      if (payload.exp * 1000 < Date.now()) {
        return null;
      }
      return {
        id: 0,
        name: '',
        email: payload.sub,
        role: payload.role,
        is_active: true,
      };
    } catch {
      return null;
    }
  }
}