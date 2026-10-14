import { client } from "./client";
import type { LoginRequest, RegisterRequest, TokenResponse, UserResponse } from "../types/auth";

export const authApi = {
  register: (payload: RegisterRequest) => client.post<UserResponse>("/api/v1/auth/register", payload).then((r) => r.data),
  login: (payload: LoginRequest) => client.post<TokenResponse>("/api/v1/auth/login", payload).then((r) => r.data),
  me: () => client.get<UserResponse>("/api/v1/auth/me").then((r) => r.data),
};
