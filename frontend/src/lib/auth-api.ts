import { apiRequest } from "@/lib/api";

export type User = {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type RegisterInput = LoginInput & {
  full_name: string;
};

export function login(input: LoginInput) {
  return apiRequest<User>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getCurrentUser(): Promise<User> {
  return apiRequest<User>("/api/v1/auth/me");
}

export function register(input: RegisterInput) {
  return apiRequest<User>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function logout(): Promise<void> {
  return apiRequest<void>("/api/v1/auth/logout", { method: "POST" });
}

export type UserProfileUpdateInput = {
  full_name: string;
};

export function updateProfile(input: UserProfileUpdateInput): Promise<User> {
  return apiRequest<User>("/api/v1/auth/profile", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export type PasswordChangeInput = {
  current_password: string;
  new_password: string;
  confirm_new_password: string;
};

export type PasswordResetRequestInput = {
  email: string;
};

export type PasswordResetConfirmInput = {
  token: string;
  new_password: string;
  confirm_new_password: string;
};

export function changePassword(input: PasswordChangeInput): Promise<void> {
  return apiRequest<void>("/api/v1/auth/change-password", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function requestPasswordReset(
  input: PasswordResetRequestInput,
): Promise<void> {
  return apiRequest<void>("/api/v1/auth/password-reset/request", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function confirmPasswordReset(
  input: PasswordResetConfirmInput,
): Promise<void> {
  return apiRequest<void>("/api/v1/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
