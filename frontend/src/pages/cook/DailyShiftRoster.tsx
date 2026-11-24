import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  CalendarDays,
  Clock,
  MapPin,
  CheckCircle2,
  AlertCircle,
  Play,
  ArrowRight,
  ShieldCheck,
  Footprints,
} from "lucide-react";

export const DailyShiftRoster: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState("2026-11-20");
  const navigate = useNavigate();

  const shifts = [
    {
      id: "sh-1",
      time: "07:30 AM - 08:30 AM",
      meal: "Breakfast Service",
      household: "Iyer Residence",
      flat: "Tower A • Flat 201",
      headcount: 3,
      menu: ["Steamed Idlis (8 Pcs)", "Coconut Chutney", "Filter Coffee"],
      status: "COMPLETED",
      transitMinutesToNext: 5,
    },
    {
      id: "sh-2",
      time: "12:30 PM - 01:30 PM",
      meal: "Lunch Service",
      household: "Verma Residence",
      flat: "Tower B • Flat 104",
      headcount: 4,
      menu: ["Yellow Dal Tadka", "Steamed Basmati Rice", "Aloo Gobi Dry", "Fresh Phulkas"],
      status: "COMPLETED",
      transitMinutesToNext: 4,
    },
    {
      id: "sh-3",
      time: "07:30 PM - 08:30 PM",
      meal: "Dinner Service",
      household: "Sharma Household",
      flat: "Tower B • Flat 402",
      headcount: 4,
      menu: ["Paneer Butter Masala", "Fresh Wheat Phulkas (10 Pcs)", "Yellow Dal Tadka"],
      status: "UPCOMING",
      transitMinutesToNext: 0,
    },
  ];

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-[10px] font-bold uppercase tracking-wider">
              OR-Tools Walking Corridor Optimizer
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• Zero Travel Outside Society</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Daily Schedule & Walking Corridor Roster
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            All your daily cooking visits are pre-sequenced by Google OR-Tools CP-SAT to guarantee minimal walking buffer between flats.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-2 rounded-xl bg-white border border-surface-container-high font-label-md text-xs font-semibold text-on-surface focus:border-secondary focus:outline-none"
          />
        </div>
      </div>

      {/* Roster Timeline List */}
      <div className="flex flex-col gap-5">
        {shifts.map((shift, idx) => (
          <React.Fragment key={shift.id}>
            <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col md:flex-row md:items-center justify-between gap-6 transition-all hover:border-secondary-container/50">
              <div className="flex items-start gap-4">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg shrink-0 ${
                    shift.status === "COMPLETED"
                      ? "bg-tertiary-fixed text-on-tertiary-fixed"
                      : "bg-secondary text-white shadow-sm"
                  }`}
                >
                  {shift.status === "COMPLETED" ? <CheckCircle2 className="w-6 h-6" /> : <Clock className="w-6 h-6" />}
                </div>

                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-extrabold text-on-surface">{shift.time}</span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full font-label-sm text-[10px] font-bold uppercase ${
                        shift.status === "COMPLETED"
                          ? "bg-tertiary-fixed text-on-tertiary-fixed"
                          : "bg-secondary-fixed text-on-secondary-fixed animate-pulse"
                      }`}
                    >
                      {shift.status}
                    </span>
                  </div>

                  <h3 className="font-headline-sm text-base font-bold text-on-surface">
                    {shift.meal} • {shift.household}
                  </h3>

                  <div className="flex items-center gap-2 text-xs text-on-surface-variant font-label-md">
                    <MapPin className="w-3.5 h-3.5 text-secondary" />
                    <span>{shift.flat}</span>
                    <span>•</span>
                    <span>{shift.headcount} Persons</span>
                  </div>

                  {/* Menu preview */}
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {shift.menu.map((m, mIdx) => (
                      <span
                        key={mIdx}
                        className="px-2.5 py-0.5 rounded-md bg-white border border-surface-container font-body-sm text-[11px] text-on-surface"
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="flex flex-col md:items-end gap-2">
                {shift.status === "UPCOMING" ? (
                  <button
                    onClick={() => navigate("/cook/shift-active")}
                    className="w-full md:w-auto px-5 py-2.5 rounded-xl bg-secondary text-white font-label-md text-xs font-bold flex items-center justify-center gap-2 shadow-md hover:bg-secondary/90 transition-colors"
                  >
                    <Play className="w-4 h-4 fill-current" />
                    <span>Open Active Cockpit</span>
                  </button>
                ) : (
                  <span className="text-xs text-tertiary font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Verified Completed • Payout ₹350 Credited</span>
                  </span>
                )}
              </div>
            </div>

            {/* Walking Transit Buffer Indicator */}
            {shift.transitMinutesToNext > 0 && (
              <div className="flex items-center justify-center gap-2 py-1 text-xs font-label-md text-on-surface-variant">
                <Footprints className="w-4 h-4 text-secondary" />
                <span className="font-semibold">{shift.transitMinutesToNext} Min Walking Corridor Transit</span>
                <span className="text-[11px] text-on-surface-variant/70">(Tower A to Tower B via Gated Walkway)</span>
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

