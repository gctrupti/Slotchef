import React, { useState } from "react";
import { toast } from "sonner";
import {
  ShieldAlert,
  AlertTriangle,
  Flame,
  Clock,
  PhoneCall,
  CheckCircle2,
  RefreshCw,
  Search,
  Users,
  Building,
} from "lucide-react";

export const IncidentVault: React.FC = () => {
  const [incidents, setIncidents] = useState([
    {
      id: "INC-1092",
      severity: "CRITICAL",
      category: "Cook Absence / Sudden Illness",
      household: "Sharma Household • Flat B-402",
      assignedCook: "Chef Meenakshi Iyer",
      reserveCook: "Chef Anand Deshmukh",
      slot: "Tonight, 07:30 PM",
      status: "RESERVE_DISPATCH_PENDING",
      description: "Assigned cook reported severe fever 45 mins prior to dinner shift. Automatic OR-Tools backup cook re-optimization triggered.",
    },
    {
      id: "INC-1091",
      severity: "MEDIUM",
      category: "Ingredient Cross-Contact Alert",
      household: "Verma Residence • Flat B-104",
      assignedCook: "Chef Anand Deshmukh",
      slot: "Today, 01:30 PM",
      status: "INVESTIGATING",
      description: "Household noted mustard seeds were present in pantry; cook requested confirmation against allergy directive before tempering.",
    },
  ]);

  const handleDispatchReserve = (id: string) => {
    setIncidents(
      incidents.map((inc) => (inc.id === id ? { ...inc, status: "RESERVE_DISPATCHED" } : inc))
    );
    toast.success("Emergency Reserve Chef Dispatched! Household notified with updated live tracker.");
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-error-container text-error font-label-sm text-[10px] font-bold uppercase tracking-wider">
              High-Priority Operations Queue
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• India 112 Protocol Active</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Kitchen Safety, Incident Vault & Emergency Dispatch
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Real-time incident resolution, sudden absence backup chef dispatching, and safety telemetry across all society nodes.
          </p>
        </div>

        <div className="p-3 rounded-2xl bg-white border border-error/30 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-error text-white flex items-center justify-center font-bold">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-label-sm uppercase font-bold text-error">Emergency Response</span>
            <span className="font-mono text-xs font-bold text-on-surface block">Dial 112 Direct Hotline</span>
          </div>
        </div>
      </div>

      {/* Incident Cards Queue */}
      <div className="flex flex-col gap-5">
        {incidents.map((inc) => (
          <div
            key={inc.id}
            className={`surface-glass rounded-2xl p-6 border shadow-glass flex flex-col gap-4 ${
              inc.severity === "CRITICAL" ? "border-error/40 bg-error-container/10" : "border-white"
            }`}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-surface-container-high pb-3">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-xs font-bold text-on-surface">{inc.id}</span>
                <span
                  className={`px-2.5 py-0.5 rounded-full font-label-sm text-[10px] font-bold uppercase ${
                    inc.severity === "CRITICAL" ? "bg-error text-white" : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {inc.severity}
                </span>
                <span className="font-headline-sm text-sm font-bold text-on-surface">{inc.category}</span>
              </div>

              <span className="font-mono text-xs font-bold text-on-surface-variant">{inc.slot}</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-body-md">
              <div>
                <span className="text-on-surface-variant block font-label-sm uppercase text-[10px]">
                  Affected Household:
                </span>
                <span className="font-bold text-on-surface">{inc.household}</span>
                <p className="text-on-surface-variant mt-2 leading-relaxed">{inc.description}</p>
              </div>

              <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container flex flex-col justify-between">
                <div>
                  <span className="text-on-surface-variant block font-label-sm uppercase text-[10px]">
                    Automatic Backup Recommendation:
                  </span>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="font-bold text-on-surface">{inc.reserveCook}</span>
                    <span className="px-2 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed text-[10px] font-bold">
                      Available (0 walking delay)
                    </span>
                  </div>
                </div>

                <div className="mt-4 flex gap-2">
                  {inc.status === "RESERVE_DISPATCH_PENDING" ? (
                    <button
                      onClick={() => handleDispatchReserve(inc.id)}
                      className="btn-gradient-primary w-full py-2.5 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Confirm Emergency Reserve Dispatch</span>
                    </button>
                  ) : (
                    <span className="text-xs font-bold text-tertiary flex items-center gap-1.5 py-2">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Reserve Chef Dispatched & Assigned</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

