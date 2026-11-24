import React from "react";
import { Link } from "react-router-dom";
import { Utensils, Home, ChefHat, ShieldCheck, Clock, CheckCircle2, Building, ArrowRight } from "lucide-react";

export const PortalSelector: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f8fafc] via-[#f0f4f8] to-[#eaedff] flex flex-col justify-between p-6 md:p-12">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto w-full flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-primary flex items-center justify-center text-white shadow-glow-primary">
            <Utensils className="w-6 h-6" />
          </div>
          <div>
            <span className="font-headline-lg text-2xl font-bold tracking-tight text-on-surface">
              Slot<span className="text-primary">Chef</span>
            </span>
            <span className="block text-[11px] font-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
              Gated Society Culinary Network
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/80 backdrop-blur-md border border-white shadow-sm font-label-md text-xs text-on-surface-variant">
          <Building className="w-4 h-4 text-primary" />
          <span className="font-semibold text-on-surface">Green Meadows Residency</span>
          <span className="w-2 h-2 rounded-full bg-tertiary-fixed"></span>
        </div>
      </div>

      {/* Hero Content */}
      <div className="max-w-5xl mx-auto w-full my-auto py-12 flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-fixed/60 border border-primary-fixed text-primary font-label-sm text-xs font-bold uppercase tracking-wider mb-6">
          <Clock className="w-4 h-4" />
          <span>Dinner Service: Phulka, Paneer Bhurji & Dal Tadka (Active Node)</span>
        </div>

        <h1 className="font-display-lg text-4xl md:text-6xl font-extrabold text-on-surface tracking-tight max-w-3xl leading-tight">
          Engineered Daily <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary-container">Predictability</span> in Your Kitchen
        </h1>

        <p className="font-body-lg text-base md:text-lg text-on-surface-variant max-w-2xl mt-4 mb-10 leading-relaxed">
          Lock recurring daily meal slots, discover certified chefs specialized in your favorite regional cuisines, and eliminate daily cooking friction for your family.
        </p>

        {/* 3 Portal Selection Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left">
          {/* Card 1: Household Portal */}
          <div className="surface-glass rounded-2xl p-6 flex flex-col justify-between border border-white hover:border-primary-container/40 hover:shadow-glass-elevated transition-all group">
            <div>
              <div className="w-12 h-12 rounded-xl bg-primary-fixed flex items-center justify-center text-primary mb-4 group-hover:scale-105 transition-transform">
                <Home className="w-6 h-6" />
              </div>
              <h2 className="font-headline-sm text-xl font-bold text-on-surface">Household Resident</h2>
              <p className="font-body-md text-xs text-on-surface-variant mt-2 leading-relaxed">
                Book guaranteed cooking slots, browse curated multi-cuisine menus, and manage dietary preferences for your home.
              </p>
            </div>

            <div className="mt-6 flex flex-col gap-2">
              <Link
                to="/household/login"
                className="btn-gradient-primary w-full py-2.5 rounded-xl font-label-md text-xs font-bold text-center flex items-center justify-center gap-2"
              >
                <span>Resident Sign-In</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/household/register"
                className="btn-glass-secondary w-full py-2.5 rounded-xl font-label-md text-xs font-semibold text-center hover:bg-white"
              >
                New Resident Registration
              </Link>
            </div>
          </div>

          {/* Card 2: Cook Partner Portal */}
          <div className="surface-glass rounded-2xl p-6 flex flex-col justify-between border border-white hover:border-secondary-container/40 hover:shadow-glass-elevated transition-all group">
            <div>
              <div className="w-12 h-12 rounded-xl bg-secondary-fixed flex items-center justify-center text-secondary mb-4 group-hover:scale-105 transition-transform">
                <ChefHat className="w-6 h-6" />
              </div>
              <h2 className="font-headline-sm text-xl font-bold text-on-surface">Cook Partner Fleet</h2>
              <p className="font-body-md text-xs text-on-surface-variant mt-2 leading-relaxed">
                Daily walking-corridor rosters within gated societies, zero transit hassle, transparent weekly payouts, and guaranteed earnings.
              </p>
            </div>

            <div className="mt-6 flex flex-col gap-2">
              <Link
                to="/cook/login"
                className="w-full py-2.5 rounded-xl bg-secondary text-white font-label-md text-xs font-bold text-center flex items-center justify-center gap-2 shadow-md hover:bg-secondary/90 transition-colors"
              >
                <span>Cook Partner Sign-In</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/cook/register"
                className="btn-glass-secondary w-full py-2.5 rounded-xl font-label-md text-xs font-semibold text-center hover:bg-white"
              >
                Join as Certified Cook
              </Link>
            </div>
          </div>

          {/* Card 3: Admin Operations Command */}
          <div className="surface-glass rounded-2xl p-6 flex flex-col justify-between border border-white hover:border-tertiary-container/40 hover:shadow-glass-elevated transition-all group">
            <div>
              <div className="w-12 h-12 rounded-xl bg-surface-container-high flex items-center justify-center text-on-surface mb-4 group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h2 className="font-headline-sm text-xl font-bold text-on-surface">Operations Command</h2>
              <p className="font-body-md text-xs text-on-surface-variant mt-2 leading-relaxed">
                Constraint-driven OR-Tools CP-SAT schedule orchestration, live KYC verification reviews, and emergency reserve dispatch.
              </p>
            </div>

            <div className="mt-6 flex flex-col gap-2">
              <Link
                to="/admin/login"
                className="w-full py-2.5 rounded-xl bg-on-surface text-white font-label-md text-xs font-bold text-center flex items-center justify-center gap-2 shadow-md hover:bg-on-surface/90 transition-colors"
              >
                <span>Admin Master Command</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <span className="text-[10px] font-label-sm text-center text-on-surface-variant/80 uppercase tracking-widest pt-1">
                Strictly Invitation & MFA Protected
              </span>
            </div>
          </div>
        </div>

        {/* Feature Highlights Banner */}
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 w-full">
          <div className="p-3 rounded-xl bg-white/60 border border-white/80 flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-tertiary" />
            <span className="text-xs font-label-md font-semibold text-on-surface">Lock Recurring Slots</span>
          </div>
          <div className="p-3 rounded-xl bg-white/60 border border-white/80 flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-tertiary" />
            <span className="text-xs font-label-md font-semibold text-on-surface">Pre-Prepped Menu & Safety</span>
          </div>
          <div className="p-3 rounded-xl bg-white/60 border border-white/80 flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-tertiary" />
            <span className="text-xs font-label-md font-semibold text-on-surface">Guaranteed Auto-Replacement</span>
          </div>
          <div className="p-3 rounded-xl bg-white/60 border border-white/80 flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-tertiary" />
            <span className="text-xs font-label-md font-semibold text-on-surface">100% Background Verified</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-7xl mx-auto w-full text-center text-xs font-body-sm text-on-surface-variant pt-6 border-t border-surface-container-high/60">
        © 2026 SlotChef Technologies Inc. Built on Google OR-Tools CP-SAT & Supabase Cloud PostgreSQL.
      </div>
    </div>
  );
};

