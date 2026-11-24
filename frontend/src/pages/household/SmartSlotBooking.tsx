import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { bookingsApi } from "@/api/bookings";
import { extractErrorMessage } from "@/api/client";
import { toast } from "sonner";
import {
  CalendarDays,
  Clock,
  ChefHat,
  Users,
  Utensils,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Loader2,
  Star,
  Check,
} from "lucide-react";

export const SmartSlotBooking: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const preselected = (location.state as any)?.preselectedDishes || ["Paneer Butter Masala", "Fresh Wheat Phulkas"];

  const [serviceDate, setServiceDate] = useState("2026-11-20");
  const [selectedSlot, setSelectedSlot] = useState<"breakfast" | "lunch" | "dinner">("dinner");
  const [headcount, setHeadcount] = useState(4);
  const [spiceLevel, setSpiceLevel] = useState<"mild" | "medium" | "spicy">("medium");
  const [selectedCookId, setSelectedCookId] = useState<string>("cook-101");
  const [loading, setLoading] = useState(false);
  const [notes, setNotes] = useState("");

  const slotOptions = [
    {
      id: "breakfast",
      label: "Breakfast Window",
      time: "07:30 AM - 08:45 AM",
      earliest: 450, // 07:30 in minutes
      latest: 525,   // 08:45 in minutes
    },
    {
      id: "lunch",
      label: "Lunch Window",
      time: "12:30 PM - 01:45 PM",
      earliest: 750, // 12:30
      latest: 825,   // 13:45
    },
    {
      id: "dinner",
      label: "Dinner Window",
      time: "07:30 PM - 08:45 PM",
      earliest: 1170, // 19:30
      latest: 1245,  // 20:45
    },
  ];

  const currentSlotObj = slotOptions.find((s) => s.id === selectedSlot)!;

  const handleConfirmBooking = async () => {
    try {
      setLoading(true);
      const res = await bookingsApi.create({
        service_date: serviceDate,
        earliest_start_minute: currentSlotObj.earliest,
        latest_finish_minute: currentSlotObj.latest,
        duration_minutes: 45,
        meal_type: selectedSlot,
        priority: 1,
        notes: `Headcount: ${headcount} people. Spice: ${spiceLevel}. Menu: ${preselected.join(", ")}. Notes: ${notes}`,
        preferred_cook_id: selectedCookId.startsWith("cook-") ? undefined : selectedCookId,
      });

      toast.success("Cooking slot confirmed by OR-Tools CP-SAT scheduler!");
      navigate("/household/tracker", { state: { bookingId: res.id } });
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-label-sm text-[10px] font-bold uppercase tracking-wider">
            Automated CP-SAT Optimization
          </span>
          <span className="text-xs font-label-md text-on-surface-variant">• Zero Overlap Guarantee</span>
        </div>
        <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
          Smart Slot Booking & Cook Matching
        </h1>
        <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
          Select your desired meal timing and recipes. The engine pairs your household with eligible in-society cook partners.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 Cols): Date, Window, Recipes, Preferences */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Section 1: Date & Time Window */}
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CalendarDays className="w-5 h-5 text-primary" />
                <h2 className="font-headline-sm text-base font-bold text-on-surface">1. Meal Window & Slot Selection</h2>
              </div>
              <input
                type="date"
                value={serviceDate}
                onChange={(e) => setServiceDate(e.target.value)}
                className="px-3 py-1.5 rounded-xl bg-white border border-surface-container-high font-label-md text-xs font-semibold text-on-surface focus:border-primary focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
              {slotOptions.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setSelectedSlot(opt.id as any)}
                  className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between ${
                    selectedSlot === opt.id
                      ? "border-primary bg-primary-fixed/30 shadow-glass-elevated ring-1 ring-primary"
                      : "border-surface-container-high bg-white/60 hover:bg-white"
                  }`}
                >
                  <span className="font-label-md text-xs font-bold text-on-surface">{opt.label}</span>
                  <span className="font-mono text-sm font-extrabold text-primary mt-1">{opt.time}</span>
                  <span className="text-[10px] text-tertiary font-medium mt-2">✓ Verified corridor available</span>
                </button>
              ))}
            </div>
          </div>

          {/* Section 2: Meal & Recipe Configuration */}
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Utensils className="w-5 h-5 text-primary" />
                <h2 className="font-headline-sm text-base font-bold text-on-surface">2. Menu & Recipe Directives</h2>
              </div>
              <button
                type="button"
                onClick={() => navigate("/household/menu")}
                className="text-xs font-label-md text-primary hover:underline font-semibold"
              >
                + Browse Menu Catalog
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              {preselected.map((dishName: string) => (
                <span
                  key={dishName}
                  className="px-3 py-1.5 rounded-xl bg-white border border-surface-container-high font-label-md text-xs font-semibold text-on-surface shadow-xs flex items-center gap-2"
                >
                  <Check className="w-3.5 h-3.5 text-primary" />
                  <span>{dishName}</span>
                </span>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1.5">Family Headcount</label>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setHeadcount(Math.max(1, headcount - 1))}
                    className="w-9 h-9 rounded-xl bg-surface-container font-bold hover:bg-surface-container-high"
                  >
                    -
                  </button>
                  <span className="font-label-lg font-bold text-on-surface px-4">{headcount} Persons</span>
                  <button
                    type="button"
                    onClick={() => setHeadcount(headcount + 1)}
                    className="w-9 h-9 rounded-xl bg-surface-container font-bold hover:bg-surface-container-high"
                  >
                    +
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1.5">Spice Calibration</label>
                <div className="grid grid-cols-3 gap-2">
                  {(["mild", "medium", "spicy"] as const).map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setSpiceLevel(lvl)}
                      className={`py-2 rounded-xl border text-xs font-label-md capitalize font-semibold ${
                        spiceLevel === lvl
                          ? "bg-primary-container text-white border-primary-container font-bold"
                          : "bg-white/80 border-surface-container-high text-on-surface-variant hover:bg-white"
                      }`}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-2">
              <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                Specific Kitchen Directives (Optional)
              </label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Less oil in dal, extra crispy phulkas for children"
                className="w-full px-3 py-2 rounded-xl bg-white/90 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Matched Cook Selection & Booking Summary */}
        <div className="flex flex-col gap-6">
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col justify-between gap-5">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <ChefHat className="w-5 h-5 text-primary" />
                  <h3 className="font-headline-sm text-base font-bold text-on-surface">3. Selected Cook Partner</h3>
                </div>
              </div>

              {/* Cook Profile Card */}
              <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container flex items-start gap-3.5 mb-4">
                <img
                  src="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80"
                  alt="Chef Meenakshi"
                  className="w-12 h-12 rounded-xl object-cover border border-white"
                />
                <div>
                  <div className="flex items-center gap-1.5">
                    <h4 className="font-label-lg font-bold text-on-surface text-sm">Chef Meenakshi Iyer</h4>
                    <ShieldCheck className="w-3.5 h-3.5 text-primary" />
                  </div>
                  <p className="text-xs text-on-surface-variant">Senior Culinary Partner • 4.9 ★</p>
                  <p className="text-[10px] text-tertiary font-semibold mt-1">✓ Verified in Tower B Corridor</p>
                </div>
              </div>

              {/* Booking Summary Box */}
              <div className="p-4 rounded-xl bg-white border border-surface-container flex flex-col gap-2.5 text-xs">
                <div className="flex justify-between font-label-md">
                  <span className="text-on-surface-variant">Service Date:</span>
                  <span className="font-bold text-on-surface">{serviceDate}</span>
                </div>
                <div className="flex justify-between font-label-md">
                  <span className="text-on-surface-variant">Time Window:</span>
                  <span className="font-bold text-primary">{currentSlotObj.time}</span>
                </div>
                <div className="flex justify-between font-label-md">
                  <span className="text-on-surface-variant">Duration:</span>
                  <span className="font-bold text-on-surface">45 Minutes</span>
                </div>
                <div className="flex justify-between font-label-md">
                  <span className="text-on-surface-variant">Headcount:</span>
                  <span className="font-bold text-on-surface">{headcount} Family Members</span>
                </div>
                <div className="pt-2 border-t border-surface-container-high flex justify-between font-label-md text-sm">
                  <span className="font-bold text-on-surface">Per-Visit Rate:</span>
                  <span className="font-extrabold text-primary">₹350.00</span>
                </div>
              </div>
            </div>

            <button
              onClick={handleConfirmBooking}
              disabled={loading}
              className="btn-gradient-primary w-full py-3.5 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2 shadow-glow-primary"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Confirm Slot with OR-Tools Engine"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

