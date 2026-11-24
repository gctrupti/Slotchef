import { apiClient } from "./client";
import { Household } from "@/types";

export const householdsApi = {
  getMyHousehold: async (): Promise<Household> => {
    const res = await apiClient.get<Household>("/households/me");
    return res.data;
  },

  updateHousehold: async (payload: Partial<Household>): Promise<Household> => {
    const res = await apiClient.patch<Household>("/households/me", payload);
    return res.data;
  },

  getDietaryVault: async () => {
    const res = await apiClient.get("/households/me/preferences");
    return res.data;
  },

  updateDietaryVault: async (preferences: Record<string, string | number | boolean | string[]>) => {
    const res = await apiClient.post("/households/me/preferences", { preferences });
    return res.data;
  },

  submitResidencyProof: async (payload: {
    flat_id: string;
    proof_type: string;
    document_reference: string;
  }) => {
    const res = await apiClient.post("/households/me/residency-verification", payload);
    return res.data;
  },
};

