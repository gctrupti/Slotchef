import { apiClient } from "./client";
import { Visit, IncidentReport } from "@/types";

export const visitsApi = {
  list: async (): Promise<Visit[]> => {
    const res = await apiClient.get<Visit[]>("/visits");
    return res.data;
  },

  get: async (id: string): Promise<Visit> => {
    const res = await apiClient.get<Visit>(`/visits/${id}`);
    return res.data;
  },

  checkIn: async (id: string, lat?: number, lng?: number): Promise<Visit> => {
    const res = await apiClient.post<Visit>(`/visits/${id}/check-in`, { latitude: lat, longitude: lng });
    return res.data;
  },

  complete: async (id: string): Promise<Visit> => {
    const res = await apiClient.post<Visit>(`/visits/${id}/complete`);
    return res.data;
  },

  confirmArrival: async (id: string): Promise<Visit> => {
    const res = await apiClient.post<Visit>(`/visits/${id}/confirm-arrival`);
    return res.data;
  },

  // Trust & Safety
  reportIncident: async (payload: {
    booking_id?: string;
    visit_id?: string;
    category: string;
    severity: string;
    description: string;
    evidence_urls?: string[];
  }): Promise<IncidentReport> => {
    const res = await apiClient.post<IncidentReport>("/visits/safety/incidents", payload);
    return res.data;
  },

  triggerSOS: async (payload: {
    visit_id: string;
    latitude?: number;
    longitude?: number;
    notes?: string;
  }) => {
    const res = await apiClient.post("/visits/safety/sos", payload);
    return res.data;
  },

  getEmergencyContacts: async () => {
    const res = await apiClient.get("/visits/safety/emergency-contacts");
    return res.data;
  },

  addEmergencyContact: async (payload: { name: string; phone: string; relationship: string }) => {
    const res = await apiClient.post("/visits/safety/emergency-contacts", payload);
    return res.data;
  },
};

