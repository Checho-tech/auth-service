import type { MessageResponse, TokenResponse, UserProfile } from "../types/api";
import { apiFetch } from "./client";

export function register(email: string, password: string, fullName: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/v1/auth/register", {
    method: "POST",
    auth: false,
    body: { email, password, full_name: fullName || null },
  });
}

export function verifyEmail(token: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/v1/auth/verify-email", {
    method: "POST",
    auth: false,
    body: { token },
  });
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    auth: false,
    body: { email, password },
  });
}

export function logout(refreshToken: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/v1/auth/logout", {
    method: "POST",
    auth: false,
    body: { refresh_token: refreshToken },
  });
}

export function forgotPassword(email: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/v1/auth/forgot-password", {
    method: "POST",
    auth: false,
    body: { email },
  });
}

export function resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/v1/auth/reset-password", {
    method: "POST",
    auth: false,
    body: { token, new_password: newPassword },
  });
}

export function changePassword(oldPassword: string, newPassword: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/v1/auth/change-password", {
    method: "POST",
    body: { old_password: oldPassword, new_password: newPassword },
  });
}

export function getMyProfile(): Promise<UserProfile> {
  return apiFetch<UserProfile>("/api/v1/users/me", { method: "GET" });
}
