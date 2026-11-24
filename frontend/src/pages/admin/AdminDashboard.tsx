import React from "react";
import { Link } from "react-router-dom";
import {
  Layers,
  Users,
  ShieldAlert,
  Wallet,
  ArrowRight,
  TrendingUp,
  Building,
  CheckCircle2,
  Clock,
  Sparkles,
  History,
} from "lucide-react";

export const AdminDashboard: React.FC = () => {
  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Top Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-on-surface/90 via-[#1a2238] to-primary/80 text-white border border-white/20 shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-primary text-white font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Node #04 Master Command
            </span>
            <span className="text-xs text-white/70 font-label-md">Green Meadows Residency (850 Units)</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold tracking-tight">
            Gated Culinary Operations Center
          </h1>
          <p className="font-body-md text-xs md:text-sm text-white/80 mt-1">
            Real-time OR-Tools scheduling telemetry, KYC fleet verification queues, and safety monitoring.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/admin/schedule"
            className="btn-gradient-primary px-5 py-2.5 rounded-xl font-label-md text-xs font-bold flex items-center gap-2"
          >
            <Layers className="w-4 h-4" />
            <span>Master Schedule</span>
          </Link>
          <Link
            to="/admin/incidents"
            className="px-4 py-2.5 rounded-xl bg-error/20 border border-error/40 text-white font-label-md text-xs font-bold hover:bg-error/30 flex items-center gap-2"
          >
            <ShieldAlert className="w-4 h-4 text-error-container" />
            <span>Incident Vault (1)</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Active Household Subscriptions
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-on-surface font-mono">184</span>
          </div>
          <span className="text-[10px] text-tertiary font-semibold block mt-1">+12 Enrolled this month</span>
        </div>

        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Verified Cook Fleet
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-primary font-mono">24</span>
          </div>
          <span className="text-[10px] text-secondary font-semibold block mt-1">2 Pending KYC Review</span>
        </div>

        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Today's Scheduled Shifts
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-on-surface font-mono">68</span>
          </div>
          <span className="text-[10px] text-tertiary font-semibold block mt-1">0 Overlaps • 100% Demand Solved</span>
        </div>

        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Monthly Platform GMV
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-tertiary font-mono">₹4.82L</span>
          </div>
          <span className="text-[10px] text-on-surface-variant block mt-1">5% Society Net Commission</span>
        </div>
      </div>

      {/* Main Action Modules */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/admin/schedule"
          className="surface-glass rounded-2xl p-6 border border-white hover:border-primary hover:shadow-glass-elevated transition-all flex flex-col justify-between group"
        >
          <div>
            <div className="w-12 h-12 rounded-xl bg-primary-fixed text-primary flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <Layers className="w-6 h-6" />
            </div>
            <h2 className="font-headline-sm text-lg font-bold text-on-surface">Master Scheduling Board</h2>
            <p className="font-body-md text-xs text-on-surface-variant mt-2 leading-relaxed">
              Google OR-Tools CP-SAT multi-track schedule orchestrator. Review corridor transit buffers, workload caps, and publish schedule plans.
            </p>
          </div>
          <div className="mt-4 pt-4 border-t border-surface-container-high flex items-center text-xs font-label-md text-primary font-bold">
            <span>Open Schedule Orchestrator →</span>
          </div>
        </Link>

        <Link
          to="/admin/cooks"
          className="surface-glass rounded-2xl p-6 border border-white hover:border-primary hover:shadow-glass-elevated transition-all flex flex-col justify-between group"
        >
          <div>
            <div className="w-12 h-12 rounded-xl bg-secondary-fixed text-secondary flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <Users className="w-6 h-6" />
            </div>
            <h2 className="font-headline-sm text-lg font-bold text-on-surface">Cook Fleet & KYC Oversight</h2>
            <p className="font-body-md text-xs text-on-surface-variant mt-2 leading-relaxed">
              Inspect government ID credentials, verify background verification partners (AuthBridge/IDfy), and approve certified cooking specializations.
            </p>
          </div>
          <div className="mt-4 pt-4 border-t border-surface-container-high flex items-center text-xs font-label-md text-secondary font-bold">
            <span>Review 2 Pending Verifications →</span>
          </div>
        </Link>

        <Link
          to="/admin/incidents"
          className="surface-glass rounded-2xl p-6 border border-white hover:border-error hover:shadow-glass-elevated transition-all flex flex-col justify-between group"
        >
          <div>
            <div className="w-12 h-12 rounded-xl bg-error-container text-error flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <h2 className="font-headline-sm text-lg font-bold text-on-surface">Kitchen Safety & Incident Vault</h2>
            <p className="font-body-md text-xs text-on-surface-variant mt-2 leading-relaxed">
              Real-time incident response, SOS alarms, sudden absence backup chef dispatching, and confidential complaint investigations.
            </p>
          </div>
          <div className="mt-4 pt-4 border-t border-surface-container-high flex items-center text-xs font-label-md text-error font-bold">
            <span>Investigate Active Incidents →</span>
          </div>
        </Link>
      </div>
    </div>
  );
};

