import { apiClient } from "./client";
import { CookProfile, IncidentReport } from "@/types";

export const adminApi = {
  // Cook Fleet & KYC Oversight
  listCookVerifications: async (status?: string): Promise<CookProfile[]> => {
    const res = await apiClient.get<CookProfile[]>("/cooks", { params: { verification_status: status } });
    return res.data;
  },

  reviewCookVerification: async (cookId: string, decision: "verified" | "rejected", notes?: string) => {
    const res = await apiClient.post(`/cooks/${cookId}/verify`, {
      status: decision,
      admin_notes: notes || "",
    });
    return res.data;
  },

  // Incident Vault & Emergency Dispatch
  listIncidents: async (status?: string): Promise<IncidentReport[]> => {
    const res = await apiClient.get<IncidentReport[]>("/visits/safety/incidents", { params: { status } });
    return res.data;
  },

  resolveIncident: async (incidentId: string, resolution_notes: string, status: "resolved" | "dismissed") => {
    const res = await apiClient.post(`/visits/safety/incidents/${incidentId}/resolve`, {
      resolution_notes,
      status,
    });
    return res.data;
  },

  // Optimization & Master Scheduling Engine
  previewSchedule: async (date: string, societyId?: string) => {
    const res = await apiClient.post("/bookings/schedule/preview", {
      date,
      society_id: societyId,
    });
    return res.data;
  },

  commitSchedule: async (planId: string) => {
    const res = await apiClient.post(`/bookings/schedule/${planId}/commit`);
    return res.data;
  },

  // Communities Management
  listSocieties: async () => {
    const res = await apiClient.get("/societies");
    return res.data;
  },

  // Audit Logs
  getAuditLogs: async (limit: number = 50) => {
    const res = await apiClient.get("/audit/logs", { params: { limit } });
    return res.data;
  },
};

