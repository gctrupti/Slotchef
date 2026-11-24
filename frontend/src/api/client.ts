import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Request interceptor to attach JWT access token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("slotchef_access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle 401s and format error details
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle token expiration & refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("slotchef_refresh_token");

      if (refreshToken) {
        try {
          const res = await axios.post(`${BASE_URL}/auth/token/refresh`, {
            refresh: refreshToken,
          });
          const newAccess = res.data.access;
          localStorage.setItem("slotchef_access_token", newAccess);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccess}`;
          }
          return apiClient(originalRequest);
        } catch (_refreshError) {
          // Token refresh failed - log out
          localStorage.removeItem("slotchef_access_token");
          localStorage.removeItem("slotchef_refresh_token");
          localStorage.removeItem("slotchef_user");
          window.location.href = "/";
        }
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Extract human-readable error string from Django RFC 7807 structured errors
 */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data === "string") return data;
    if (data?.detail) return String(data.detail);
    if (data?.message) return String(data.message);
    if (typeof data === "object" && data !== null) {
      const messages: string[] = [];
      for (const [key, val] of Object.entries(data)) {
        if (Array.isArray(val)) {
          messages.push(`${key}: ${val.join(", ")}`);
        } else if (typeof val === "string") {
          messages.push(`${key}: ${val}`);
        }
      }
      if (messages.length > 0) return messages.join(" | ");
    }
    return error.message || "An unexpected error occurred.";
  }
  return error instanceof Error ? error.message : "Network error. Please try again.";
}

