import React, { useState } from "react";
import { toast } from "sonner";
import {
  Users,
  Building,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Search,
  FileText,
  Package,
  Calendar,
  AlertCircle,
  Home,
  Eye,
} from "lucide-react";

interface HouseholdItem {
  id: string;
  residentName: string;
  phone: string;
  email: string;
  society: string;
  tower: string;
  flatNumber: string;
  planName: string;
  remainingVisits: number;
  totalVisits: number;
  docType: string;
  docUrl: string;
  verificationStatus: "VERIFIED" | "PENDING_REVIEW" | "REJECTED";
  isNocVerified: boolean;
  registeredDate: string;
}

export const HouseholdOversight: React.FC = () => {
  const [filter, setFilter] = useState<"all" | "pending" | "verified">("all");
  const [search, setSearch] = useState("");
  const [selectedHousehold, setSelectedHousehold] = useState<HouseholdItem | null>(null);

  const [households, setHouseholds] = useState<HouseholdItem[]>([
    {
      id: "hh-201",
      residentName: "Priya Sharma",
      phone: "+919876543210",
      email: "priya.sharma@example.com",
      society: "Green Meadows Residency",
      tower: "Tower B",
      flatNumber: "402",
      planName: "12-Slot Flexi Bi-Weekly",
      remainingVisits: 8,
      totalVisits: 12,
      docType: "Society Maintenance Bill / Agreement",
      docUrl: "https://docs.slotchef.test/proofs/hh-201-noc.pdf",
      verificationStatus: "VERIFIED",
      isNocVerified: true,
      registeredDate: "2026-10-15",
    },
    {
      id: "hh-202",
      residentName: "Vikram Malhotra",
      phone: "+919876543215",
      email: "vikram.m@example.com",
      society: "Green Meadows Residency",
      tower: "Tower A",
      flatNumber: "1004",
      planName: "Weekly Routine (6 Visits)",
      remainingVisits: 2,
      totalVisits: 6,
      docType: "Registered Rental Deed",
      docUrl: "https://docs.slotchef.test/proofs/hh-202-rent.pdf",
      verificationStatus: "PENDING_REVIEW",
      isNocVerified: false,
      registeredDate: "2026-11-02",
    },
    {
      id: "hh-203",
      residentName: "Ananya Deshmukh",
      phone: "+919876543230",
      email: "ananya.d@example.com",
      society: "Green Meadows Residency",
      tower: "Tower C",
      flatNumber: "701",
      planName: "Monthly Gourmet (24 Visits)",
      remainingVisits: 19,
      totalVisits: 24,
      docType: "Apartment Electricity Bill",
      docUrl: "https://docs.slotchef.test/proofs/hh-203-bescom.pdf",
      verificationStatus: "VERIFIED",
      isNocVerified: true,
      registeredDate: "2026-09-20",
    },
    {
      id: "hh-204",
      residentName: "Karthik Raja",
      phone: "+919876543245",
      email: "karthik.raja@example.com",
      society: "Green Meadows Residency",
      tower: "Tower D",
      flatNumber: "305",
      planName: "Pay Per Visit",
      remainingVisits: 1,
      totalVisits: 1,
      docType: "Move-In NOC Letter",
      docUrl: "https://docs.slotchef.test/proofs/hh-204-noc.pdf",
      verificationStatus: "PENDING_REVIEW",
      isNocVerified: false,
      registeredDate: "2026-11-10",
    },
  ]);

  const handleVerify = (id: string, decision: "VERIFIED" | "REJECTED") => {
    setHouseholds(
      households.map((h) =>
        h.id === id
          ? {
              ...h,
              verificationStatus: decision,
              isNocVerified: decision === "VERIFIED",
            }
          : h
      )
    );
    if (decision === "VERIFIED") {
      toast.success("Household residency verified and authorized for booking!");
    } else {
      toast.error("Household residency proof rejected. Resident notified.");
    }
    setSelectedHousehold(null);
  };

  const filtered = households.filter((h) => {
    const matchesFilter =
      filter === "all" ||
      (filter === "pending" && h.verificationStatus === "PENDING_REVIEW") ||
      (filter === "verified" && h.verificationStatus === "VERIFIED");
    const matchesSearch =
      h.residentName.toLowerCase().includes(search.toLowerCase()) ||
      h.flatNumber.toLowerCase().includes(search.toLowerCase()) ||
      h.phone.includes(search);
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-primary-container text-white font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Node #04 Resident Command
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• Green Meadows Community</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Household Oversight & Residency Verification
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Manage society flat occupancies, verify residency proofs, and monitor active meal plan entitlements.
          </p>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-on-surface-variant absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search resident, flat..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none w-48 md:w-60"
            />
          </div>
          <div className="flex bg-surface-container rounded-xl p-1 text-xs font-label-md font-semibold">
            <button
              onClick={() => setFilter("all")}
              className={`px-3 py-1 rounded-lg transition-all ${
                filter === "all" ? "bg-white text-on-surface shadow-xs" : "text-on-surface-variant"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter("pending")}
              className={`px-3 py-1 rounded-lg transition-all ${
                filter === "pending" ? "bg-white text-secondary shadow-xs" : "text-on-surface-variant"
              }`}
            >
              Pending NOC (2)
            </button>
            <button
              onClick={() => setFilter("verified")}
              className={`px-3 py-1 rounded-lg transition-all ${
                filter === "verified" ? "bg-white text-tertiary shadow-xs" : "text-on-surface-variant"
              }`}
            >
              Verified
            </button>
          </div>
        </div>
      </div>

      {/* Household Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((hh) => (
          <div
            key={hh.id}
            className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col justify-between hover:border-primary/40 transition-all"
          >
            <div>
              {/* Card Header */}
              <div className="flex items-start justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-xl bg-primary-fixed text-primary flex items-center justify-center font-bold">
                    <Home className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="font-headline-sm text-base font-bold text-on-surface">{hh.residentName}</h2>
                    <span className="text-xs text-on-surface-variant font-mono">
                      {hh.tower} • Flat {hh.flatNumber}
                    </span>
                  </div>
                </div>

                {hh.verificationStatus === "VERIFIED" ? (
                  <span className="px-2.5 py-1 rounded-full bg-tertiary/10 text-tertiary border border-tertiary/20 text-[10px] font-label-sm font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Verified
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full bg-secondary-fixed text-secondary border border-secondary/20 text-[10px] font-label-sm font-bold flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Pending NOC
                  </span>
                )}
              </div>

              {/* Plan & Entitlements */}
              <div className="p-3 rounded-xl bg-surface-container-low border border-surface-container flex flex-col gap-2 mb-4 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-on-surface-variant font-label-sm">
                    <Package className="w-3.5 h-3.5 text-primary" />
                    <span>Active Subscription</span>
                  </div>
                  <span className="font-bold text-on-surface">{hh.planName}</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-on-surface-variant">Remaining Visit Entitlements:</span>
                  <span className="font-mono font-bold text-primary">
                    {hh.remainingVisits} of {hh.totalVisits} visits
                  </span>
                </div>
                {/* Progress Bar */}
                <div className="w-full bg-surface-container-high h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-primary h-full rounded-full transition-all"
                    style={{ width: `${(hh.remainingVisits / hh.totalVisits) * 100}%` }}
                  />
                </div>
              </div>

              {/* Document details */}
              <div className="flex flex-col gap-1 text-xs mb-4">
                <div className="flex items-center justify-between text-on-surface-variant">
                  <span>Residency Proof:</span>
                  <span className="font-medium text-on-surface">{hh.docType}</span>
                </div>
                <div className="flex items-center justify-between text-on-surface-variant">
                  <span>Contact Phone:</span>
                  <span className="font-mono text-on-surface">{hh.phone}</span>
                </div>
                <div className="flex items-center justify-between text-on-surface-variant">
                  <span>Registered:</span>
                  <span className="text-on-surface">{hh.registeredDate}</span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="pt-3 border-t border-surface-container flex items-center justify-between gap-2">
              <button
                onClick={() => setSelectedHousehold(hh)}
                className="btn-glass-secondary px-3 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 flex-1 justify-center"
              >
                <Eye className="w-3.5 h-3.5 text-primary" />
                <span>Inspect Proof</span>
              </button>

              {hh.verificationStatus === "PENDING_REVIEW" && (
                <button
                  onClick={() => handleVerify(hh.id, "VERIFIED")}
                  className="px-3 py-2 rounded-xl bg-tertiary text-white font-label-md text-xs font-bold hover:bg-tertiary/90 flex items-center gap-1.5 shadow-sm"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Approve</span>
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Inspect Proof Modal */}
      {selectedHousehold && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md">
          <div className="surface-glass rounded-2xl p-6 md:p-8 max-w-lg w-full border border-white shadow-2xl flex flex-col gap-5">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-label-sm text-primary uppercase font-bold tracking-wider">
                  Household Verification Inspection
                </span>
                <h3 className="font-headline-sm text-xl font-bold text-on-surface mt-1">
                  {selectedHousehold.residentName} — Flat {selectedHousehold.flatNumber}
                </h3>
                <span className="text-xs text-on-surface-variant font-mono">
                  {selectedHousehold.tower}, {selectedHousehold.society}
                </span>
              </div>
              <button
                onClick={() => setSelectedHousehold(null)}
                className="p-1 rounded-lg text-on-surface-variant hover:bg-surface-container"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container flex flex-col gap-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-on-surface-variant font-medium">Document Type:</span>
                <span className="font-bold text-on-surface">{selectedHousehold.docType}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-on-surface-variant font-medium">Verification Status:</span>
                <span className="font-bold text-primary font-mono">{selectedHousehold.verificationStatus}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-on-surface-variant font-medium">Society NOC Verified:</span>
                <span className="font-bold text-tertiary">
                  {selectedHousehold.isNocVerified ? "YES (Society Confirmed)" : "NO (Awaiting Admin Review)"}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-white border border-surface-container flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-primary" />
                  <span className="font-mono text-[11px] truncate max-w-xs">{selectedHousehold.docUrl}</span>
                </div>
                <span className="px-2 py-0.5 rounded bg-surface-container font-label-sm text-[10px] font-semibold text-primary">
                  PDF / PNG
                </span>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => handleVerify(selectedHousehold.id, "REJECTED")}
                className="flex-1 py-2.5 rounded-xl border border-error/40 text-error hover:bg-error/10 text-xs font-bold transition-all"
              >
                Reject Proof
              </button>
              <button
                type="button"
                onClick={() => handleVerify(selectedHousehold.id, "VERIFIED")}
                className="flex-1 py-2.5 rounded-xl btn-gradient-primary text-xs font-bold shadow-sm"
              >
                Approve Residency
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

