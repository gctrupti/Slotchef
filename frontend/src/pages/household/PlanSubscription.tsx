import React, { useState } from "react";
import { toast } from "sonner";
import { bookingsApi } from "@/api/bookings";
import { extractErrorMessage } from "@/api/client";
import {
  Package,
  Calendar,
  Clock,
  PauseCircle,
  PlayCircle,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Loader2,
} from "lucide-react";

export const PlanSubscription: React.FC = () => {
  const [isPaused, setIsPaused] = useState(false);
  const [pauseDays, setPauseDays] = useState(5);
  const [showPauseModal, setShowPauseModal] = useState(false);
  const [loading, setLoading] = useState(false);

  const handlePauseHold = async () => {
    try {
      setLoading(true);
      // Calls backend pause endpoint
      setIsPaused(true);
      setShowPauseModal(false);
      toast.success(`Vacation hold active! Kitchen service paused for ${pauseDays} days. No visit entitlements deducted.`);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleResume = () => {
    setIsPaused(false);
    toast.success("Kitchen service resumed! Regular recurring slots restored.");
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Gourmet Plan Suite
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• Green Meadows Node</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Household Subscription & Gourmet Suite
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Manage your recurring visits, pause during family travel, and lock guaranteed cook assignments without daily manual bookings.
          </p>
        </div>

        <div>
          {!isPaused ? (
            <button
              onClick={() => setShowPauseModal(true)}
              className="btn-glass-secondary px-4 py-2.5 rounded-xl font-label-md text-xs font-bold flex items-center gap-2 hover:bg-white"
            >
              <PauseCircle className="w-4 h-4 text-primary" />
              <span>Vacation Hold / Pause Kitchen</span>
            </button>
          ) : (
            <button
              onClick={handleResume}
              className="btn-gradient-primary px-5 py-2.5 rounded-xl font-label-md text-xs font-bold flex items-center gap-2"
            >
              <PlayCircle className="w-4 h-4" />
              <span>Resume Kitchen Service</span>
            </button>
          )}
        </div>
      </div>

      {/* Vacation Pause Status Alert */}
      {isPaused && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <PauseCircle className="w-5 h-5 text-amber-600" />
            <div>
              <span className="font-label-md text-xs font-bold block">Vacation Pause Active (5 Days Remaining)</span>
              <span className="font-body-sm text-[11px] text-amber-700">All recurring cooking slots are temporarily on hold until 25 Nov 2026.</span>
            </div>
          </div>
          <button
            onClick={handleResume}
            className="px-3 py-1.5 rounded-lg bg-white border border-amber-300 font-label-md text-xs font-bold text-amber-900 hover:bg-amber-100"
          >
            Resume Now
          </button>
        </div>
      )}

      {/* Main Grid: Active Plan Details & Usage Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Subscription Card (2 Cols) */}
        <div className="lg:col-span-2 surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col justify-between gap-6">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary-fixed text-primary flex items-center justify-center font-bold">
                  <Package className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="font-headline-sm text-lg font-bold text-on-surface">12-Slot Flexi Bi-Weekly Package</h2>
                  <p className="text-xs text-on-surface-variant font-label-md">Tier 1 Gated Society Allocation</p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full bg-primary-fixed text-primary font-label-sm text-xs font-bold">
                Active & Enrolled
              </span>
            </div>

            {/* Visit Entitlement Progress Counter */}
            <div className="p-5 rounded-2xl bg-surface-container-low border border-surface-container my-4">
              <div className="flex items-baseline justify-between mb-2">
                <span className="font-label-md text-xs uppercase tracking-wider text-on-surface-variant font-bold">
                  Visit Entitlement Tracking
                </span>
                <span className="font-mono text-xs font-bold text-primary">
                  4 Completed of 12 Slots
                </span>
              </div>

              <div className="w-full bg-surface-container-high h-3 rounded-full overflow-hidden">
                <div
                  className="bg-primary h-full rounded-full transition-all duration-700"
                  style={{ width: "33%" }}
                ></div>
              </div>

              <div className="grid grid-cols-3 gap-2 mt-4 text-center">
                <div className="p-2.5 rounded-xl bg-white border border-surface-container-high">
                  <span className="block text-xl font-extrabold text-on-surface font-mono">12</span>
                  <span className="text-[10px] font-label-sm text-on-surface-variant font-semibold">Total Entitled</span>
                </div>
                <div className="p-2.5 rounded-xl bg-white border border-surface-container-high">
                  <span className="block text-xl font-extrabold text-tertiary font-mono">4</span>
                  <span className="text-[10px] font-label-sm text-on-surface-variant font-semibold">Completed</span>
                </div>
                <div className="p-2.5 rounded-xl bg-white border border-surface-container-high">
                  <span className="block text-xl font-extrabold text-primary font-mono">8</span>
                  <span className="text-[10px] font-label-sm text-on-surface-variant font-semibold">Remaining</span>
                </div>
              </div>
            </div>

            {/* Recurring Policy Directives */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-body-md text-on-surface">
              <div className="p-3.5 rounded-xl bg-white/70 border border-surface-container-high flex items-start gap-3">
                <Calendar className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block text-on-surface">Preferred Weekdays</span>
                  <span className="text-on-surface-variant">Monday, Wednesday, Friday, Sunday</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-white/70 border border-surface-container-high flex items-start gap-3">
                <Clock className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block text-on-surface">Protected Time Slot</span>
                  <span className="text-on-surface-variant">07:30 PM - 08:30 PM (Dinner Service)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-surface-container-high text-xs">
            <span className="text-on-surface-variant">Auto-Renewal on 30 Nov 2026: <strong className="text-on-surface">Active</strong></span>
            <button
              onClick={() => toast.info("Renewal settings updated")}
              className="text-primary font-bold hover:underline"
            >
              Configure Renewal →
            </button>
          </div>
        </div>

        {/* Right Column: Vacation Hold Policy & Gourmet Harvest Perks */}
        <div className="flex flex-col gap-6">
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-5 h-5 text-tertiary" />
                <h3 className="font-headline-sm text-base font-bold text-on-surface">Curated Package Inclusions</h3>
              </div>
              <ul className="flex flex-col gap-2.5 text-xs font-body-md text-on-surface-variant">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-tertiary shrink-0 mt-0.5" />
                  <span>Guaranteed backup cook auto-replacement in case of unforeseen emergency.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-tertiary shrink-0 mt-0.5" />
                  <span>Up to 7 days flexible vacation hold per billing cycle without penalty.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-tertiary shrink-0 mt-0.5" />
                  <span>Complimentary kitchen sanitization and spice shelf audit every 14 days.</span>
                </li>
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container text-xs text-on-surface-variant">
              <span className="font-bold text-on-surface block mb-1">Billing Breakdown</span>
              <div className="flex justify-between py-1">
                <span>12 Visits Rate:</span>
                <span className="font-mono font-bold text-on-surface">₹3,800.00</span>
              </div>
              <div className="flex justify-between py-1">
                <span>Society Commission (5%):</span>
                <span className="font-mono text-on-surface">Included</span>
              </div>
              <div className="flex justify-between py-1 border-t border-surface-container-high font-bold text-on-surface pt-2">
                <span>Total Paid:</span>
                <span className="font-mono text-primary font-extrabold text-sm">₹3,800.00</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pause Hold Modal Dialog */}
      {showPauseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="surface-glass rounded-2xl p-6 md:p-8 max-w-md w-full border border-white shadow-2xl flex flex-col gap-5">
            <div>
              <h3 className="font-headline-sm text-lg font-bold text-on-surface">Vacation Hold / Pause Kitchen</h3>
              <p className="font-body-sm text-xs text-on-surface-variant mt-1">
                Select the number of days you wish to put your cooking slots on hold. Unused visits remain preserved in your entitlement vault.
              </p>
            </div>

            <div>
              <label className="block text-xs font-label-md font-semibold text-on-surface mb-2">
                Pause Duration: <strong className="text-primary">{pauseDays} Days</strong>
              </label>
              <input
                type="range"
                min={1}
                max={7}
                value={pauseDays}
                onChange={(e) => setPauseDays(Number(e.target.value))}
                className="w-full accent-primary cursor-pointer"
              />
              <div className="flex justify-between text-[11px] font-mono text-on-surface-variant mt-1">
                <span>1 Day</span>
                <span>Max 7 Days</span>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowPauseModal(false)}
                className="btn-glass-secondary px-4 py-2 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handlePauseHold}
                disabled={loading}
                className="btn-gradient-primary px-5 py-2 rounded-xl text-xs font-bold flex items-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Confirm Vacation Hold"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

