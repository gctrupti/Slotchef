import { apiClient } from "./client";
import { LoginResponse, RegisterResponse, User } from "@/types";

export interface RegisterPayload {
  email: string;
  password: string;
  phone?: string;
  first_name?: string;
  last_name?: string;
  role: "household_member" | "cook";
  verification_channel?: "sms" | "email";
}

export interface LoginPayload {
  identifier: string; // email or phone
  password: string;
}

export const authApi = {
  // Registration Flow (Step 1 & 2)
  register: async (payload: RegisterPayload): Promise<RegisterResponse> => {
    const res = await apiClient.post<RegisterResponse>("/auth/register", payload);
    return res.data;
  },

  verifyRegistrationOTP: async (target: string, channel: "sms" | "email", otp: string) => {
    const res = await apiClient.post("/auth/register/verify-otp", {
      target,
      channel,
      otp,
    });
    return res.data;
  },

  // Sequential 2nd Channel or Normal OTP
  requestOTP: async (target: string, channel: "sms" | "email", purpose: string = "registration") => {
    const res = await apiClient.post("/auth/otp/request", {
      target,
      channel,
      purpose,
    });
    return res.data;
  },

  verifyOTP: async (target: string, channel: "sms" | "email", purpose: string, otp: string) => {
    const res = await apiClient.post("/auth/otp/verify", {
      target,
      channel,
      purpose,
      otp,
    });
    return res.data;
  },

  // Dual Identifier Password Login
  login: async (payload: LoginPayload): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>("/auth/login", payload);
    return res.data;
  },

  // Admin Step-up MFA
  verifyAdminMFA: async (mfa_token: string, otp: string): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>("/auth/admin/mfa-verify", {
      mfa_token,
      otp,
    });
    return res.data;
  },

  // Self-Service Security
  requestPasswordReset: async (target: string, channel: "sms" | "email") => {
    const res = await apiClient.post("/auth/password-reset/request", { target, channel });
    return res.data;
  },

  confirmPasswordReset: async (target: string, channel: "sms" | "email", otp: string, new_password: string) => {
    const res = await apiClient.post("/auth/password-reset/confirm", {
      target,
      channel,
      otp,
      new_password,
    });
    return res.data;
  },

  requestContactChange: async (new_target: string, channel: "sms" | "email") => {
    const res = await apiClient.post("/auth/contact/request-change", { new_target, channel });
    return res.data;
  },

  confirmContactChange: async (new_target: string, channel: "sms" | "email", otp: string) => {
    const res = await apiClient.post("/auth/contact/confirm-change", { new_target, channel, otp });
    return res.data;
  },

  getProfile: async (): Promise<User> => {
    const res = await apiClient.get<User>("/me");
    return res.data;
  },
};

