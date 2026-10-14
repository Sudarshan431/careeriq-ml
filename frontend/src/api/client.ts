import axios, { AxiosError } from "axios";
import type { ApiErrorBody } from "../types/api";
import { getToken, clearToken } from "../utils/storage";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const client = axios.create({ baseURL: API_BASE_URL });

client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let onUnauthorized: (() => void) | null = null;
export function registerUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

client.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      clearToken();
      onUnauthorized?.();
    }
    return Promise.reject(error);
  }
);

/** Extracts a user-friendly message from the backend's structured error envelope. */
export function getApiErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError<ApiErrorBody>;
  if (axiosError?.response?.data?.error?.message) {
    return axiosError.response.data.error.message;
  }
  if (axiosError?.message === "Network Error") {
    return "Unable to reach the server. Please check your connection and try again.";
  }
  return "Something went wrong. Please try again.";
}

export function getApiErrorCode(error: unknown): string | null {
  const axiosError = error as AxiosError<ApiErrorBody>;
  return axiosError?.response?.data?.error?.code ?? null;
}

export function getRequestId(error: unknown): string | null {
  const axiosError = error as AxiosError<ApiErrorBody>;
  return axiosError?.response?.data?.error?.request_id ?? null;
}
