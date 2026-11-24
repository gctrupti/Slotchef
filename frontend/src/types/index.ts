/**
 * SlotChef TypeScript Interfaces & Types matching authoritative Django REST Framework serializers
 */

export type RoleType = "platform_admin" | "society_admin" | "cook" | "household_member";

export interface User {
  id: string;
  email: string;
  phone: string;
  first_name: string;
  last_name: string;
  legal_name?: string;
  roles: RoleType[];
  is_email_verified: boolean;
  is_mobile_verified: boolean;
  is_fully_verified: boolean;
  mfa_enabled?: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  access?: string;
  refresh?: string;
  user?: User;
  mfa_required?: boolean;
  mfa_token?: string;
  message?: string;
}

export interface RegisterResponse {
  user: User;
  access?: string;
  refresh?: string;
  verification_channel: "sms" | "email";
  verification_target: string;
  message: string;
}

export interface Society {
  id: string;
  name: string;
  slug: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  timezone: string;
}

export interface Building {
  id: string;
  society: string;
  name: string;
  code: string;
}

export interface Flat {
  id: string;
  building: string;
  flat_number: string;
  floor: number;
}

export interface Household {
  id: string;
  society: Society | string;
  society_name?: string;
  building_name: string;
  flat_number: string;
  contact_phone: string;
  verification_status?: "pending" | "in_review" | "verified" | "rejected" | "suspended";
}

export interface SkillItem {
  id: string;
  code: string;
  name: string;
  description: string;
  cuisine?: string;
}

export interface CookSkill {
  id: string;
  skill: SkillItem;
  proficiency_level: "basic" | "intermediate" | "expert";
}

export interface CookProfile {
  id: string;
  user: User;
  verification_status: "pending" | "verified" | "rejected" | "suspended";
  active_status: boolean;
  max_daily_minutes: number;
  max_daily_visits: number;
  skills: CookSkill[];
  societies: Society[];
  rating?: number;
  completed_visits_count?: number;
}

export interface BookingRequirement {
  id: string;
  skill_code: string;
  skill_name: string;
}

export interface Booking {
  id: string;
  household: Household | string;
  service_date: string;
  earliest_start_minute: number;
  latest_finish_minute: number;
  duration_minutes: number;
  meal_type: "breakfast" | "lunch" | "dinner" | "snacks";
  priority: number;
  status: "DRAFT" | "PENDING" | "CONFIRMED" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED" | "UNFULFILLED";
  notes?: string;
  assigned_cook?: CookProfile;
  assigned_start_minute?: number;
  assigned_finish_minute?: number;
  price_breakdown?: {
    service_price_minor_units: number;
    platform_fee_minor_units: number;
    total_price_minor_units: number;
    currency: string;
  };
}

export interface PackagePlan {
  id: string;
  name: string;
  plan_type: "weekly" | "monthly" | "per_visit";
  total_visits: number;
  validity_days: number;
  price_minor_units: number;
  currency: string;
  meal_type: string;
  default_duration_minutes: number;
  max_pause_days: number;
  is_active: boolean;
}

export interface PackageSubscription {
  id: string;
  package_plan: PackagePlan;
  status: "active" | "paused" | "completed" | "cancelled" | "expired";
  total_entitled_visits: number;
  used_visits: number;
  remaining_visits: number;
  preferred_weekdays: number[];
  preferred_start_minute: number;
  preferred_end_minute: number;
  start_date: string;
  end_date: string;
  pause_resumes_at?: string;
}

export interface Visit {
  id: string;
  booking: Booking;
  cook: CookProfile;
  status: "SCHEDULED" | "CHECKED_IN" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED" | "MISSED" | "ABANDONED";
  scheduled_start_time: string;
  scheduled_end_time: string;
  actual_start_time?: string;
  actual_end_time?: string;
  household_confirmed_arrival: boolean;
}

export interface IncidentReport {
  id: string;
  reporter_type: "household" | "cook" | "system";
  category: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  status: "reported" | "investigating" | "resolved" | "dismissed";
  resolution_notes?: string;
  created_at: string;
}

export interface CookEarnings {
  today_earnings_minor_units: number;
  weekly_earnings_minor_units: number;
  monthly_earnings_minor_units: number;
  pending_cash_minor_units: number;
  completed_visits_count: number;
  currency: string;
}

