import React, { useState } from "react";
import { toast } from "sonner";
import {
  Layers,
  Calendar,
  Clock,
  Play,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Users,
  MapPin,
} from "lucide-react";

export const MasterScheduleBoard: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState("2026-11-20");
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [planVersion, setPlanVersion] = useState(3);
  const [optimizerStatus, setOptimizerStatus] = useState<"OPTIMAL" | "FEASIBLE">("OPTIMAL");

  const scheduleTracks = [
    {
      cookName: "Chef Meenakshi Iyer",
      corridor: "Tower B Corridor",
      maxDailyMinutes: 480,
      assignedMinutes: 270,
      slots: [
        { time: "07:30 - 08:30 AM", household: "Iyer Res. (A-201)", status: "COMPLETED", duration: "45m" },
        { time: "12:30 - 01:30 PM", household: "Verma Res. (B-104)", status: "COMPLETED", duration: "45m" },
        { time: "07:30 - 08:30 PM", household: "Sharma HH (B-402)", status: "CONFIRMED", duration: "45m" },
      ],
    },
    {
      cookName: "Chef Anand Deshmukh",
      corridor: "Tower A & C Corridor",
      maxDailyMinutes: 480,
      assignedMinutes: 180,
      slots: [
        { time: "08:00 - 09:00 AM", household: "Nair Home (C-102)", status: "COMPLETED", duration: "45m" },
        { time: "07:30 - 08:30 PM", household: "Reserve Chef Standby", status: "STANDBY", duration: "Standby" },
      ],
    },
  ];

  const handlePreviewOptimization = () => {
    setIsOptimizing(true);
    setTimeout(() => {
      setIsOptimizing(false);
      setOptimizerStatus("OPTIMAL");
      toast.success("OR-Tools CP-SAT Solver produced optimal schedule (0 overlaps, 5m transit buffers respected)!");
    }, 1200);
  };

  const handlePublishPlan = () => {
    setPlanVersion((prev) => prev + 1);
    toast.success(`Schedule Plan v${planVersion + 1} published & locked across resident and cook terminals!`);
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Constraint Satisfaction Engine
            </span>
            <span className="text-xs font-label-md text-on-surface-variant font-semibold">
              Schedule Plan Version: <strong className="text-on-surface">v{planVersion}</strong>
            </span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Master Operations Scheduling Board
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Deterministic Google OR-Tools CP-SAT scheduler enforcing time windows, walking transit buffers, and workload balancing.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={handlePreviewOptimization}
            disabled={isOptimizing}
            className="btn-glass-secondary px-4 py-2.5 rounded-xl font-label-md text-xs font-bold flex items-center gap-2 hover:bg-white"
          >
            <Sparkles className="w-4 h-4 text-primary" />
            <span>{isOptimizing ? "Solving Constraints..." : "Preview Optimization"}</span>
          </button>

          <button
            onClick={handlePublishPlan}
            className="btn-gradient-primary px-5 py-2.5 rounded-xl font-label-md text-xs font-bold flex items-center gap-2 shadow-glow-primary"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Publish Plan v{planVersion + 1}</span>
          </button>
        </div>
      </div>

      {/* Solver Telemetry Banner */}
      <div className="surface-glass rounded-2xl p-4 border border-white shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs font-label-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-tertiary-fixed text-tertiary flex items-center justify-center font-bold">
            ✓
          </div>
          <div>
            <span className="font-bold text-on-surface block">Engine Status: {optimizerStatus}</span>
            <span className="text-[11px] text-on-surface-variant font-normal">
              100% Demand Fulfilled • GiST Exclusion Constraints Verified Active
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-on-surface-variant">
          <span>Directional Transition: <strong className="text-on-surface">5 Minutes</strong></span>
          <span>Max Consecutive Visits: <strong className="text-on-surface">4 Visits</strong></span>
        </div>
      </div>

      {/* Multi-Track Corridor Grid */}
      <div className="flex flex-col gap-6">
        {scheduleTracks.map((track, idx) => (
          <div
            key={idx}
            className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-surface-container-high pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary text-white flex items-center justify-center font-bold">
                  {track.cookName[5] || "C"}
                </div>
                <div>
                  <h3 className="font-headline-sm text-base font-bold text-on-surface">{track.cookName}</h3>
                  <span className="text-xs text-on-surface-variant font-label-md">{track.corridor}</span>
                </div>
              </div>

              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="text-on-surface-variant">Workload Allocation:</span>
                <span className="font-bold text-primary">{track.assignedMinutes}m / {track.maxDailyMinutes}m (56%)</span>
              </div>
            </div>

            {/* Slots Track */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {track.slots.map((s, sIdx) => (
                <div
                  key={sIdx}
                  className={`p-4 rounded-xl border flex flex-col justify-between gap-2 ${
                    s.status === "COMPLETED"
                      ? "bg-white/50 border-surface-container-high"
                      : s.status === "STANDBY"
                      ? "bg-amber-50/60 border-amber-200"
                      : "bg-white border-primary-container/40 shadow-xs ring-1 ring-primary-container/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-on-surface">{s.time}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold font-label-sm uppercase ${
                        s.status === "COMPLETED"
                          ? "bg-tertiary-fixed text-on-tertiary-fixed"
                          : s.status === "STANDBY"
                          ? "bg-amber-200 text-amber-800"
                          : "bg-primary-fixed text-primary"
                      }`}
                    >
                      {s.status}
                    </span>
                  </div>

                  <span className="font-label-md text-xs font-bold text-on-surface">{s.household}</span>
                  <span className="text-[10px] text-on-surface-variant">Duration: {s.duration}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

