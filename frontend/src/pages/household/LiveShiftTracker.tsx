import React, { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  Clock,
  ChefHat,
  CheckCircle2,
  ShieldCheck,
  AlertTriangle,
  PhoneCall,
  Flame,
  ArrowRight,
  Sparkles,
  MapPin,
  Check,
} from "lucide-react";

export const LiveShiftTracker: React.FC = () => {
  const [arrivalConfirmed, setArrivalConfirmed] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(3); // 3 = Stepping into residence

  const steps = [
    { id: 1, title: "Society Security Gate Check-In", time: "07:22 PM", desc: "Biometric pass verified at Green Meadows Main Gate" },
    { id: 2, title: "Tower B Elevator Transit", time: "07:26 PM", desc: "Corridor walking transit in progress" },
    { id: 3, title: "Stepping into Household Residence", time: "07:29 PM", desc: "Arrival at Flat 402 doorbell" },
    { id: 4, title: "Active Culinary SOP Execution", time: "07:32 PM", desc: "Prep, cooking phulkas & simmering paneer masala" },
    { id: 5, title: "Kitchen Sanitization & Sign-Off", time: "08:15 PM", desc: "Station clean, gas knob check & visit completed" },
  ];

  const handleConfirmArrival = () => {
    setArrivalConfirmed(true);
    setCurrentStep(4);
    toast.success("Arrival confirmed! Cook shift transitioned to Active Culinary SOP.");
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Top Banner with Real-Time Arc Status */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-primary/10 via-secondary-fixed/40 to-surface-container-high border border-white/80 shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-label-sm text-xs text-primary font-bold uppercase tracking-wider">
              Live Shift Readiness Stream
            </span>
            <span className="text-xs text-on-surface-variant font-label-md">• Booking #SC-BK-4091</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Chef Meenakshi Iyer is stepping into Tower B lobby
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant mt-1">
            Estimated walking arrival at Flat 402 in <span className="font-bold text-on-surface">2 minutes</span>.
          </p>
        </div>

        {/* Arrival Confirmation Trigger Button */}
        <div>
          {!arrivalConfirmed ? (
            <button
              onClick={handleConfirmArrival}
              className="btn-gradient-primary px-5 py-3 rounded-xl font-label-md text-xs font-bold flex items-center gap-2 shadow-glow-primary"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Confirm Arrival at Residence</span>
            </button>
          ) : (
            <div className="px-4 py-2.5 rounded-xl bg-tertiary-fixed text-on-tertiary-fixed font-label-md text-xs font-bold flex items-center gap-2">
              <Check className="w-4 h-4 text-tertiary-container" />
              <span>Arrival Confirmed • Cooking Active</span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Step-by-Step Arrival Progression Arc (2 Cols) */}
        <div className="lg:col-span-2 surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              <h2 className="font-headline-sm text-base font-bold text-on-surface">
                Step-by-Step Arrival & Shift Arc
              </h2>
            </div>
            <span className="font-label-sm text-xs text-on-surface-variant font-bold uppercase">
              Slot: 07:30 PM - 08:30 PM
            </span>
          </div>

          <div className="flex flex-col gap-4 relative">
            {/* Step Timeline */}
            {steps.map((st) => {
              const isPast = st.id < currentStep;
              const isCurrent = st.id === currentStep;

              return (
                <div key={st.id} className="flex items-start gap-4">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-label-md text-xs font-bold transition-all ${
                        isPast
                          ? "bg-tertiary text-white"
                          : isCurrent
                          ? "bg-primary text-white ring-4 ring-primary/20 animate-pulse"
                          : "bg-surface-container text-on-surface-variant"
                      }`}
                    >
                      {isPast ? <Check className="w-4 h-4" /> : st.id}
                    </div>
                    {st.id < steps.length && (
                      <div className={`w-0.5 h-10 ${isPast ? "bg-tertiary" : "bg-surface-container-high"}`} />
                    )}
                  </div>

                  <div className="flex-1 pb-2">
                    <div className="flex items-center justify-between">
                      <h3
                        className={`font-label-md text-xs font-bold ${
                          isCurrent ? "text-primary" : "text-on-surface"
                        }`}
                      >
                        {st.title}
                      </h3>
                      <span className="font-mono text-xs text-on-surface-variant font-medium">{st.time}</span>
                    </div>
                    <p className="font-body-sm text-xs text-on-surface-variant mt-0.5">{st.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Kitchen Station Readiness Stream */}
          <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container flex flex-col gap-3">
            <span className="font-label-sm text-xs font-bold text-on-surface uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-tertiary" />
              <span>Kitchen Station Readiness Stream</span>
            </span>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-body-sm">
              <div className="p-2.5 rounded-lg bg-white border border-surface-container-high flex items-center gap-2">
                <Check className="w-4 h-4 text-tertiary" />
                <span>Sanitization Protocol 100%</span>
              </div>
              <div className="p-2.5 rounded-lg bg-white border border-surface-container-high flex items-center gap-2">
                <Check className="w-4 h-4 text-tertiary" />
                <span>Gas & Induction Checked</span>
              </div>
              <div className="p-2.5 rounded-lg bg-white border border-surface-container-high flex items-center gap-2">
                <Check className="w-4 h-4 text-tertiary" />
                <span>Dietary Directives Loaded</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Cook Card & Active Menu */}
        <div className="flex flex-col gap-6">
          {/* Cook Profile Card */}
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col justify-between gap-5">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-label-md uppercase tracking-wider text-on-surface-variant font-bold">
                  Assigned Chef Partner
                </span>
                <span className="px-2 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-[10px] font-bold">
                  On-Duty
                </span>
              </div>

              <div className="flex items-center gap-3.5 mb-4">
                <img
                  src="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80"
                  alt="Chef Meenakshi"
                  className="w-14 h-14 rounded-2xl object-cover border border-white shadow-sm"
                />
                <div>
                  <div className="flex items-center gap-1.5">
                    <h3 className="font-label-lg font-bold text-on-surface">Chef Meenakshi Iyer</h3>
                    <ShieldCheck className="w-4 h-4 text-primary" />
                  </div>
                  <p className="text-xs text-on-surface-variant">Senior Culinary Partner • 4.9 ★</p>
                  <p className="text-[11px] text-tertiary font-medium">Biometric ID: #GM-CK-104</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <a
                  href="tel:+919876543210"
                  className="btn-glass-secondary flex-1 py-2 rounded-xl font-label-md text-xs font-bold text-center flex items-center justify-center gap-1.5"
                >
                  <PhoneCall className="w-4 h-4 text-primary" />
                  <span>Call Chef</span>
                </a>
                <Link
                  to="/household/safety"
                  className="btn-glass-secondary p-2 rounded-xl text-error hover:bg-error-container/30"
                  title="Trigger SOS or Safety Report"
                >
                  <AlertTriangle className="w-4 h-4" />
                </Link>
              </div>
            </div>

            {/* Menu Items to be Cooked */}
            <div className="pt-4 border-t border-surface-container-high">
              <span className="block text-[11px] font-label-sm uppercase tracking-wider text-on-surface-variant font-bold mb-2">
                Dinner Service Recipe List:
              </span>
              <div className="flex flex-col gap-1.5 text-xs font-body-md text-on-surface">
                <div className="flex items-center justify-between p-2 rounded-lg bg-white border border-surface-container">
                  <span>Paneer Butter Masala</span>
                  <span className="text-[11px] text-primary font-semibold">Medium Spice</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-white border border-surface-container">
                  <span>Fresh Wheat Phulkas (10 Pcs)</span>
                  <span className="text-[11px] text-primary font-semibold">Organic Ghee</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-white border border-surface-container">
                  <span>Yellow Dal Tadka</span>
                  <span className="text-[11px] text-primary font-semibold">Cumin & Garlic</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

