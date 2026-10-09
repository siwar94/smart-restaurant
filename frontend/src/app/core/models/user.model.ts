export enum UserRole {
  ADMIN = 'ADMIN',
  SERVEUR = 'SERVEUR',
  CUISINE = 'CUISINE',
}

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active?: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}