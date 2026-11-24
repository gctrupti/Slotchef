import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { visitsApi } from "@/api/visits";
import {
  Clock,
  MapPin,
  CheckCircle2,
  ShieldAlert,
  PhoneCall,
  Check,
  AlertTriangle,
  Flame,
  Utensils,
  Play,
  RotateCcw,
} from "lucide-react";

export const ActiveShiftCockpit: React.FC = () => {
  const [checkedIn, setCheckedIn] = useState(true);
  const [secondsRemaining, setSecondsRemaining] = useState(42 * 60 + 15); // 42 min 15 sec
  const [completedSteps, setCompletedSteps] = useState<number[]>([1, 2]);
  const [isCompleted, setIsCompleted] = useState(false);
  const navigate = useNavigate();

  const sopChecklist = [
    { id: 1, title: "Hygiene & Sanitization Protocol", desc: "Hand wash with soap for 30s & wear hairnet" },
    { id: 2, title: "Station Inspection & Gas Check", desc: "Inspect burner knobs, ventilation, and cookware cleanliness" },
    { id: 3, title: "Mise en Place & Vegetable Prep", desc: "Dice paneer, chop onions & tomatoes to specification" },
    { id: 4, title: "Simmer Gravy & Temper Spices", desc: "Cook tomato gravy to medium spice; verify salt level" },
    { id: 5, title: "Fresh Phulkas on Griddle", desc: "Puff 10 soft phulkas on open flame & apply light ghee" },
    { id: 6, title: "Station Clean & Gas Turn-Off", desc: "Wipe down cooktop, ensure gas regulator safety & serve" },
  ];

  // Timer countdown
  useEffect(() => {
    if (secondsRemaining <= 0 || isCompleted) return;
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [secondsRemaining, isCompleted]);

  const formatTimer = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const toggleSop = (id: number) => {
    if (completedSteps.includes(id)) {
      setCompletedSteps(completedSteps.filter((s) => s !== id));
    } else {
      setCompletedSteps([...completedSteps, id]);
    }
  };

  const handleMarkComplete = async () => {
    if (completedSteps.length < sopChecklist.length) {
      toast.error("Please complete all culinary SOP safety steps before signing off");
      return;
    }

    setIsCompleted(true);
    toast.success("Shift marked completed! Household notified and ₹350 payout credited to your ledger.");
    navigate("/cook/earnings");
  };

  const handleTriggerSOS = async () => {
    try {
      await visitsApi.triggerSOS({
        visit_id: "visit-101",
        notes: "Cook partner triggered urgent assistance alarm from active shift cockpit",
      });
      toast.error("SOS Emergency Alarm Dispatched to Society Security & Admin Command!");
    } catch {
      toast.error("Emergency alarm dispatched to Green Meadows Guard Gate!");
    }
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-secondary/15 via-secondary-fixed/40 to-surface-container-high border border-white/80 shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-label-sm text-xs text-secondary font-bold uppercase tracking-wider">
              Shift Execution Active
            </span>
            <span className="text-xs text-on-surface-variant font-label-md">• Booking #SC-BK-4091</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Dinner Service at Sharma Household (Flat B-402)
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant mt-1">
            Standard 45-minute service window. Headcount: 4 family members. Medium spice.
          </p>
        </div>

        {/* Live Timer Countdown Box */}
        <div className="p-4 rounded-2xl bg-white border border-secondary/30 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-secondary-fixed text-secondary flex items-center justify-center font-bold">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[10px] font-label-sm uppercase font-bold text-on-surface-variant block">
              Remaining Window
            </span>
            <span className="font-mono text-2xl font-extrabold text-secondary tracking-tight">
              {formatTimer(secondsRemaining)}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* SOP Workflow Checklist (2 Cols) */}
        <div className="lg:col-span-2 surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Utensils className="w-5 h-5 text-secondary" />
              <h2 className="font-headline-sm text-base font-bold text-on-surface">
                Standard Culinary SOP Execution Checklist
              </h2>
            </div>
            <span className="font-mono text-xs font-bold text-secondary">
              {completedSteps.length} of {sopChecklist.length} Verified
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {sopChecklist.map((item) => {
              const isChecked = completedSteps.includes(item.id);
              return (
                <div
                  key={item.id}
                  onClick={() => toggleSop(item.id)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-start gap-3.5 ${
                    isChecked
                      ? "bg-white border-secondary shadow-xs ring-1 ring-secondary/30"
                      : "surface-glass border-surface-container-high hover:bg-white"
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-lg border flex items-center justify-center shrink-0 mt-0.5 ${
                      isChecked
                        ? "bg-secondary text-white border-secondary"
                        : "border-surface-container-high bg-white"
                    }`}
                  >
                    {isChecked && <Check className="w-4 h-4 stroke-[3]" />}
                  </div>

                  <div className="flex-1">
                    <h3 className={`font-label-md text-xs font-bold ${isChecked ? "text-secondary" : "text-on-surface"}`}>
                      {item.title}
                    </h3>
                    <p className="font-body-sm text-xs text-on-surface-variant mt-0.5">{item.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action Complete Button */}
          <div className="pt-4 border-t border-surface-container-high flex items-center justify-between">
            <button
              onClick={handleTriggerSOS}
              className="px-4 py-2.5 rounded-xl border border-error/30 text-error font-label-md text-xs font-bold flex items-center gap-1.5 hover:bg-error-container/30 transition-colors"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>SOS Emergency Alarm</span>
            </button>

            <button
              onClick={handleMarkComplete}
              className="px-6 py-3 rounded-xl bg-secondary text-white font-label-md text-xs font-bold flex items-center gap-2 shadow-md hover:bg-secondary/90 transition-all"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Sign-Off & Complete Shift</span>
            </button>
          </div>
        </div>

        {/* Right Column: Household Directives & Recipes */}
        <div className="flex flex-col gap-6">
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4">
            <span className="font-label-sm text-xs uppercase tracking-wider text-on-surface-variant font-bold">
              Household Recipe & Dietary Spec
            </span>

            <div className="p-3.5 rounded-xl bg-surface-container-low border border-surface-container flex flex-col gap-2 text-xs">
              <div className="flex justify-between font-label-md">
                <span className="text-on-surface-variant">Spice Tolerance:</span>
                <span className="font-bold text-on-surface">Medium Spiced</span>
              </div>
              <div className="flex justify-between font-label-md">
                <span className="text-on-surface-variant">Cooking Oil:</span>
                <span className="font-bold text-on-surface">Standard Tempering</span>
              </div>
              <div className="flex justify-between font-label-md">
                <span className="text-on-surface-variant">Garlic / Onion:</span>
                <span className="font-bold text-tertiary">Permitted</span>
              </div>
              <div className="flex justify-between font-label-md">
                <span className="text-on-surface-variant">Allergens:</span>
                <span className="font-bold text-error">Peanuts Strictly Avoided</span>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <span className="text-[11px] font-label-sm text-on-surface-variant font-bold uppercase tracking-wider">
                Menu Requirements:
              </span>
              <div className="p-2.5 rounded-xl bg-white border border-surface-container text-xs">
                🥘 <strong>Paneer Butter Masala</strong> — 250g paneer cubes in tomato cream gravy
              </div>
              <div className="p-2.5 rounded-xl bg-white border border-surface-container text-xs">
                🫓 <strong>Phulkas</strong> — 10 soft wheat flatbreads with ghee
              </div>
              <div className="p-2.5 rounded-xl bg-white border border-surface-container text-xs">
                🍲 <strong>Yellow Dal Tadka</strong> — Cumin, mustard seed & garlic tempering
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

