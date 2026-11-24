import React from "react";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/store/useAuthStore";
import {
  CalendarDays,
  Clock,
  Wallet,
  ShieldCheck,
  CheckCircle2,
  ChefHat,
  ArrowRight,
  Flame,
  AlertCircle,
  MapPin,
  Play,
} from "lucide-react";

export const CookHome: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-secondary/15 via-secondary-fixed/40 to-surface-container-high border border-white/80 shadow-glass">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-secondary text-white font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Fleet Partner #GM-CK-104
            </span>
            <span className="text-xs font-label-md text-on-surface-variant font-semibold">Green Meadows Residency</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface">
            Namaste, Chef {user?.first_name || "Partner"}!
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant mt-1">
            You have <strong className="text-on-surface">3 scheduled visits</strong> in Tower B today. All transit is within 5 minutes walking distance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/cook/shift-active"
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-secondary text-white font-label-md text-xs font-bold flex items-center justify-center gap-2 shadow-md hover:bg-secondary/90 transition-colors"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Open Active Shift Cockpit</span>
          </Link>
          <Link
            to="/cook/schedule"
            className="btn-glass-secondary px-4 py-2.5 rounded-xl font-label-md text-xs font-semibold"
          >
            View Daily Roster
          </Link>
        </div>
      </div>

      {/* KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Today's Visits
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-on-surface font-mono">3</span>
            <span className="text-xs text-on-surface-variant font-label-md">Slots (All Tower B)</span>
          </div>
          <span className="text-[10px] text-tertiary font-medium block mt-1">✓ 1 Completed • 2 Remaining</span>
        </div>

        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            This Month Earnings
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-secondary font-mono">₹28,450</span>
          </div>
          <span className="text-[10px] text-tertiary font-medium block mt-1">✓ Weekly payout processed</span>
        </div>

        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Pending Cash Collected
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-on-surface font-mono">₹700</span>
          </div>
          <span className="text-[10px] text-amber-600 font-medium block mt-1">Awaiting household confirm</span>
        </div>

        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Verification Standing
          </span>
          <div className="flex items-center gap-1.5 mt-2">
            <ShieldCheck className="w-6 h-6 text-tertiary" />
            <span className="font-label-lg text-sm font-extrabold text-tertiary">Verified MasterChef</span>
          </div>
          <span className="text-[10px] text-on-surface-variant block mt-1">Aadhaar, BGV & Skills Clear</span>
        </div>
      </div>

      {/* Immediate Next Shift Roster Card */}
      <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col justify-between gap-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-secondary" />
            <h2 className="font-headline-sm text-lg font-bold text-on-surface">Upcoming Shift Service</h2>
          </div>
          <span className="px-3 py-1 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-xs font-bold animate-pulse">
            Next Up at 07:30 PM
          </span>
        </div>

        <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-secondary text-white flex items-center justify-center font-bold text-lg shadow-sm">
              <MapPin className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-label-lg font-bold text-on-surface">Sharma Household • Flat B-402</h3>
              <p className="font-body-sm text-xs text-on-surface-variant">Green Meadows Residency, Tower B (Floor 4)</p>
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                <span className="px-2 py-0.5 rounded bg-white text-[10px] font-semibold text-on-surface border">
                  4 Persons
                </span>
                <span className="px-2 py-0.5 rounded bg-white text-[10px] font-semibold text-on-surface border">
                  Medium Spiced
                </span>
                <span className="px-2 py-0.5 rounded bg-white text-[10px] font-semibold text-tertiary border">
                  Vegetarian
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-col md:items-end">
            <span className="text-xs font-label-md text-on-surface-variant font-bold">Planned Window</span>
            <span className="font-mono text-lg font-extrabold text-secondary">07:30 PM - 08:30 PM</span>
            <Link
              to="/cook/shift-active"
              className="mt-2 w-full md:w-auto px-4 py-2 rounded-xl bg-secondary text-white font-label-md text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm hover:bg-secondary/90"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Start Shift Checklist</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

