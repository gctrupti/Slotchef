import { apiClient } from "./client";
import { CookProfile, CookEarnings, SkillItem } from "@/types";

export const cooksApi = {
  list: async (params?: { society?: string; skill?: string; active?: boolean }): Promise<CookProfile[]> => {
    const res = await apiClient.get<CookProfile[]>("/cooks", { params });
    return res.data;
  },

  get: async (id: string): Promise<CookProfile> => {
    const res = await apiClient.get<CookProfile>(`/cooks/${id}`);
    return res.data;
  },

  getMyProfile: async (): Promise<CookProfile> => {
    const res = await apiClient.get<CookProfile>("/cooks/me");
    return res.data;
  },

  getMySchedule: async (date?: string) => {
    const res = await apiClient.get("/cooks/me/schedule", { params: { date } });
    return res.data;
  },

  getMyAvailability: async () => {
    const res = await apiClient.get("/cooks/me/availability");
    return res.data;
  },

  updateAvailability: async (availabilities: Array<{
    weekday: number;
    start_minute: number;
    end_minute: number;
    is_available: boolean;
  }>) => {
    const res = await apiClient.post("/cooks/me/availability", { availabilities });
    return res.data;
  },

  getSkillCatalog: async (): Promise<SkillItem[]> => {
    const res = await apiClient.get<SkillItem[]>("/cooks/skills");
    return res.data;
  },

  updateMySkills: async (skills: Array<{ skill_id: string; proficiency_level: string }>) => {
    const res = await apiClient.post("/cooks/me/skills", { skills });
    return res.data;
  },

  getMyEarnings: async (): Promise<CookEarnings> => {
    const res = await apiClient.get<CookEarnings>("/finance/cook-earnings");
    return res.data;
  },
};

