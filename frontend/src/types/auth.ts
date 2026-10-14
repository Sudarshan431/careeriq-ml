export type Role = "CANDIDATE" | "RECRUITER" | "ADMIN";

export interface RegisterRequest {
  email: string;
  password: string;
  role: "CANDIDATE" | "RECRUITER";
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
}

export interface UserResponse {
  id: string;
  email: string;
  role: Role;
  is_active: boolean;
}
