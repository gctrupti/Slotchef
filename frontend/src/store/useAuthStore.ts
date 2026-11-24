import { create } from "zustand";
import { User, Society, RoleType } from "@/types";
import { apiClient, extractErrorMessage } from "@/api/client";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  activePortal: "household" | "cook" | "admin" | null;
  currentSociety: Society | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setAuth: (user: User, access: string, refresh?: string) => void;
  setUser: (user: User) => void;
  setCurrentSociety: (society: Society) => void;
  setActivePortal: (portal: "household" | "cook" | "admin") => void;
  logout: () => void;
  fetchProfile: () => Promise<void>;
  hasRole: (role: RoleType) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => {
  // Restore initial state from localStorage
  const savedUser = localStorage.getItem("slotchef_user");
  const parsedUser: User | null = savedUser ? JSON.parse(savedUser) : null;
  const initialAccess = localStorage.getItem("slotchef_access_token");
  const initialRefresh = localStorage.getItem("slotchef_refresh_token");

  // Determine initial portal based on roles
  let initialPortal: "household" | "cook" | "admin" | null = null;
  if (parsedUser) {
    if (parsedUser.roles.includes("platform_admin") || parsedUser.roles.includes("society_admin")) {
      initialPortal = "admin";
    } else if (parsedUser.roles.includes("cook")) {
      initialPortal = "cook";
    } else if (parsedUser.roles.includes("household_member")) {
      initialPortal = "household";
    }
  }

  return {
    user: parsedUser,
    accessToken: initialAccess,
    refreshToken: initialRefresh,
    activePortal: initialPortal,
    currentSociety: null,
    isLoading: false,
    error: null,

    setAuth: (user: User, access: string, refresh?: string) => {
      localStorage.setItem("slotchef_user", JSON.stringify(user));
      localStorage.setItem("slotchef_access_token", access);
      if (refresh) {
        localStorage.setItem("slotchef_refresh_token", refresh);
      }

      let portal: "household" | "cook" | "admin" = "household";
      if (user.roles.includes("platform_admin") || user.roles.includes("society_admin")) {
        portal = "admin";
      } else if (user.roles.includes("cook")) {
        portal = "cook";
      }

      set({
        user,
        accessToken: access,
        refreshToken: refresh || get().refreshToken,
        activePortal: portal,
        error: null,
      });
    },

    setUser: (user: User) => {
      localStorage.setItem("slotchef_user", JSON.stringify(user));
      set({ user });
    },

    setCurrentSociety: (society: Society) => {
      set({ currentSociety: society });
    },

    setActivePortal: (portal: "household" | "cook" | "admin") => {
      set({ activePortal: portal });
    },

    logout: () => {
      localStorage.removeItem("slotchef_user");
      localStorage.removeItem("slotchef_access_token");
      localStorage.removeItem("slotchef_refresh_token");
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        activePortal: null,
        currentSociety: null,
      });
    },

    fetchProfile: async () => {
      try {
        set({ isLoading: true, error: null });
        const res = await apiClient.get<User>("/me");
        get().setUser(res.data);
      } catch (err) {
        set({ error: extractErrorMessage(err) });
      } finally {
        set({ isLoading: false });
      }
    },

    hasRole: (role: RoleType) => {
      const user = get().user;
      return user ? user.roles.includes(role) : false;
    },
  };
});

