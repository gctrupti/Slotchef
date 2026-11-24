import { apiClient } from "./client";
import { Booking, PackagePlan, PackageSubscription } from "@/types";

export interface CreateBookingPayload {
  household?: string;
  service_date: string;
  earliest_start_minute: number;
  latest_finish_minute: number;
  duration_minutes: number;
  meal_type: "breakfast" | "lunch" | "dinner" | "snacks";
  priority?: number;
  notes?: string;
  requirements?: string[]; // skill codes
  preferred_cook_id?: string;
}

export const bookingsApi = {
  list: async (): Promise<Booking[]> => {
    const res = await apiClient.get<Booking[]>("/bookings");
    return res.data;
  },

  get: async (id: string): Promise<Booking> => {
    const res = await apiClient.get<Booking>(`/bookings/${id}`);
    return res.data;
  },

  create: async (payload: CreateBookingPayload): Promise<Booking> => {
    const res = await apiClient.post<Booking>("/bookings/request", payload);
    return res.data;
  },

  cancel: async (id: string, reason: string): Promise<void> => {
    await apiClient.post(`/bookings/${id}/cancel`, { cancellation_reason: reason });
  },

  // Package Subscriptions
  listPackagePlans: async (): Promise<PackagePlan[]> => {
    const res = await apiClient.get<PackagePlan[]>("/packages/plans");
    return res.data;
  },

  subscribePackage: async (payload: {
    package_plan_id: string;
    start_date: string;
    preferred_weekdays: number[];
    preferred_start_minute: number;
    preferred_end_minute: number;
  }): Promise<PackageSubscription> => {
    const res = await apiClient.post<PackageSubscription>("/packages/subscribe", payload);
    return res.data;
  },

  getMySubscriptions: async (): Promise<PackageSubscription[]> => {
    const res = await apiClient.get<PackageSubscription[]>("/packages/my-subscriptions");
    return res.data;
  },

  pauseSubscription: async (subscriptionId: string, pauseDays: number): Promise<PackageSubscription> => {
    const res = await apiClient.post<PackageSubscription>(`/packages/subscriptions/${subscriptionId}/pause`, {
      pause_days: pauseDays,
    });
    return res.data;
  },

  resumeSubscription: async (subscriptionId: string): Promise<PackageSubscription> => {
    const res = await apiClient.post<PackageSubscription>(`/packages/subscriptions/${subscriptionId}/resume`);
    return res.data;
  },
};

