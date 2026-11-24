import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/store/useAuthStore";
import { bookingsApi } from "@/api/bookings";
import { Booking, PackageSubscription } from "@/types";
import {
  CalendarDays,
  Clock,
  ChefHat,
  Package,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Plus,
} from "lucide-react";

export const HouseholdHome: React.FC = () => {
  const { user } = useAuthStore();
  const [upcomingBooking, setUpcomingBooking] = useState<Booking | null>(null);
  const [activeSubscription, setActiveSubscription] = useState<PackageSubscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHomeData = async () => {
      try {
        setLoading(true);
        const [bookings, subs] = await Promise.all([
          bookingsApi.list().catch(() => []),
          bookingsApi.getMySubscriptions().catch(() => []),
        ]);

        if (bookings.length > 0) {
          setUpcomingBooking(bookings[0]);
        }
        if (subs.length > 0) {
          setActiveSubscription(subs[0]);
        }
      } finally {
        setLoading(false);
      }
    };

    loadHomeData();
  }, []);

  return (
    <div className="flex flex-col gap-8">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-primary/10 via-primary-fixed/30 to-surface-container-high border border-white/80 shadow-glass">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-primary text-white font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Active Society Node #04
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">Green Meadows Residency</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface">
            Hello, {user?.first_name || "Resident"}!
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant mt-1">
            Your kitchen coordination is on track. Tonight's service is ready for execution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/household/booking"
            className="btn-gradient-primary px-5 py-2.5 rounded-xl font-label-md text-xs font-bold flex items-center gap-2 shadow-glow-primary"
          >
            <Plus className="w-4 h-4" />
            <span>Book Cooking Slot</span>
          </Link>
          <Link
            to="/household/menu"
            className="btn-glass-secondary px-4 py-2.5 rounded-xl font-label-md text-xs font-semibold"
          >
            Explore Menu
          </Link>
        </div>
      </div>

      {/* Main Grid: Next Active Booking & Package Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Next Scheduled Visit Card */}
        <div className="lg:col-span-2 surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-primary-fixed text-primary flex items-center justify-center font-bold">
                  <Clock className="w-4 h-4" />
                </div>
                <h2 className="font-headline-sm text-lg font-bold text-on-surface">Next Scheduled Visit</h2>
              </div>
              <span className="px-3 py-1 rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-xs font-bold flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-tertiary-container animate-pulse"></span>
                Confirmed & Optimized
              </span>
            </div>

            {/* Visit Details */}
            <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-full bg-primary-container text-white flex items-center justify-center font-bold text-lg shadow-sm">
                  <ChefHat className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-label-lg font-bold text-on-surface">Chef Meenakshi Iyer</h3>
                  <p className="font-body-sm text-xs text-on-surface-variant">Senior Culinary Partner • 4.9 ★</p>
                  <span className="inline-block px-2 py-0.5 rounded-md bg-secondary-fixed text-on-secondary-fixed font-label-sm text-[10px] font-semibold mt-1">
                    Specialist: South Indian & North Indian
                  </span>
                </div>
              </div>

              <div className="text-right flex flex-col md:items-end">
                <span className="text-xs font-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                  Today's Dinner Window
                </span>
                <span className="font-label-lg text-lg font-extrabold text-primary">07:30 PM - 08:30 PM</span>
                <span className="text-[11px] text-tertiary font-medium">Walking Transit Buffer: 5 mins</span>
              </div>
            </div>

            {/* Meal Items to be Cooked */}
            <div className="mt-4">
              <span className="block font-label-sm text-xs text-on-surface-variant font-bold uppercase tracking-wider mb-2">
                Pre-Approved Recipe Plan (3 Items)
              </span>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1.5 rounded-xl bg-white border border-surface-container-high font-body-sm text-xs font-semibold text-on-surface shadow-xs">
                  🥣 Paneer Butter Masala (Medium Spice)
                </span>
                <span className="px-3 py-1.5 rounded-xl bg-white border border-surface-container-high font-body-sm text-xs font-semibold text-on-surface shadow-xs">
                  🫓 Fresh Wheat Phulkas (10 Pcs)
                </span>
                <span className="px-3 py-1.5 rounded-xl bg-white border border-surface-container-high font-body-sm text-xs font-semibold text-on-surface shadow-xs">
                  🍲 Yellow Dal Tadka (Cumin & Ghee Tempering)
                </span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-surface-container-high flex items-center justify-between">
            <Link
              to="/household/tracker"
              className="text-xs font-label-md text-primary font-bold hover:underline flex items-center gap-1.5"
            >
              <span>Open Live Shift Arrival Tracker</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/household/dietary"
              className="text-xs font-label-md text-on-surface-variant hover:text-on-surface"
            >
              Modify Kitchen Directives →
            </Link>
          </div>
        </div>

        {/* Package & Subscription Summary */}
        <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-secondary-fixed text-secondary flex items-center justify-center font-bold">
                  <Package className="w-4 h-4" />
                </div>
                <h2 className="font-headline-sm text-lg font-bold text-on-surface">Your Package Plan</h2>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-primary-fixed text-primary font-label-sm text-[10px] font-bold">
                Active
              </span>
            </div>

            <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container mb-4">
              <span className="font-label-sm text-[11px] text-on-surface-variant uppercase tracking-wider font-bold">
                12-Slot Flexi Bi-Weekly
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="font-display-lg text-3xl font-extrabold text-on-surface">
                  {activeSubscription?.remaining_visits ?? 8}
                </span>
                <span className="text-xs text-on-surface-variant font-label-md">
                  visits remaining of {activeSubscription?.total_entitled_visits ?? 12}
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-surface-container-high h-2 rounded-full mt-3 overflow-hidden">
                <div
                  className="bg-primary h-full rounded-full transition-all duration-500"
                  style={{ width: "66%" }}
                ></div>
              </div>
            </div>

            <div className="flex flex-col gap-2 text-xs font-body-sm text-on-surface-variant">
              <div className="flex justify-between">
                <span>Validity:</span>
                <span className="font-semibold text-on-surface">Valid till 30 Nov 2026</span>
              </div>
              <div className="flex justify-between">
                <span>Preferred Slots:</span>
                <span className="font-semibold text-on-surface">Mon, Wed, Fri (Dinner)</span>
              </div>
              <div className="flex justify-between">
                <span>Vacation Pause Available:</span>
                <span className="font-semibold text-tertiary">Up to 7 Days</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-surface-container-high">
            <Link
              to="/household/packages"
              className="btn-glass-secondary w-full py-2.5 rounded-xl font-label-md text-xs font-bold text-center block"
            >
              Manage Subscription & Pause Hold
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Action Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/household/menu"
          className="surface-glass rounded-2xl p-5 border border-white hover:border-primary/40 hover:shadow-glass-elevated transition-all flex items-center gap-4 group"
        >
          <div className="w-12 h-12 rounded-xl bg-primary-fixed text-primary flex items-center justify-center group-hover:scale-105 transition-transform">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-label-lg font-bold text-on-surface group-hover:text-primary transition-colors">
              Explore 16 Cuisines
            </h3>
            <p className="font-body-sm text-xs text-on-surface-variant mt-0.5">
              Browse dishes & discover cooks who specialize in them.
            </p>
          </div>
        </Link>

        <Link
          to="/household/dietary"
          className="surface-glass rounded-2xl p-5 border border-white hover:border-primary/40 hover:shadow-glass-elevated transition-all flex items-center gap-4 group"
        >
          <div className="w-12 h-12 rounded-xl bg-tertiary-fixed text-tertiary flex items-center justify-center group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-label-lg font-bold text-on-surface group-hover:text-primary transition-colors">
              Dietary & Allergen Vault
            </h3>
            <p className="font-body-sm text-xs text-on-surface-variant mt-0.5">
              Fine-tune spice levels, oil limits, and family restrictions.
            </p>
          </div>
        </Link>

        <Link
          to="/household/safety"
          className="surface-glass rounded-2xl p-5 border border-white hover:border-error/40 hover:shadow-glass-elevated transition-all flex items-center gap-4 group"
        >
          <div className="w-12 h-12 rounded-xl bg-error-container text-error flex items-center justify-center group-hover:scale-105 transition-transform">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-label-lg font-bold text-on-surface group-hover:text-error transition-colors">
              Safety Center & SOS
            </h3>
            <p className="font-body-sm text-xs text-on-surface-variant mt-0.5">
              Emergency contacts, India 112 hotline, and incident reporting.
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
};

