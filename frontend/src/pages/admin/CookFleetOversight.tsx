import React, { useState } from "react";
import { toast } from "sonner";
import {
  Users,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Search,
  FileText,
  Building,
  ChefHat,
  Award,
  AlertCircle,
} from "lucide-react";

interface CookVerificationItem {
  id: string;
  name: string;
  phone: string;
  email: string;
  society: string;
  docType: string;
  maskedDocNumber: string;
  experienceYears: number;
  bgvStatus: "CLEAR" | "PENDING" | "FLAGGED";
  bgvPartner: string;
  skills: string[];
  status: "PENDING_REVIEW" | "VERIFIED" | "REJECTED";
}

export const CookFleetOversight: React.FC = () => {
  const [filter, setFilter] = useState<"all" | "pending" | "verified">("pending");
  const [search, setSearch] = useState("");

  const [cooks, setCooks] = useState<CookVerificationItem[]>([
    {
      id: "ck-101",
      name: "Rameshwar Prasad",
      phone: "+919876543201",
      email: "ramesh@cook.test",
      society: "Green Meadows Residency",
      docType: "Aadhaar Card",
      maskedDocNumber: "XXXXXXXX4892",
      experienceYears: 6,
      bgvStatus: "CLEAR",
      bgvPartner: "AuthBridge Verification",
      skills: ["South Indian", "North Indian", "Gujarati Thali"],
      status: "PENDING_REVIEW",
    },
    {
      id: "ck-102",
      name: "Sunita Devi",
      phone: "+919876543202",
      email: "sunita@cook.test",
      society: "Green Meadows Residency",
      docType: "Voter ID Card",
      maskedDocNumber: "XXXXXXXX7120",
      experienceYears: 8,
      bgvStatus: "CLEAR",
      bgvPartner: "IDfy Verification",
      skills: ["North Indian", "Punjabi", "Baking & Desserts"],
      status: "PENDING_REVIEW",
    },
    {
      id: "ck-103",
      name: "Chef Anand Deshmukh",
      phone: "+919876543203",
      email: "anand@cook.test",
      society: "Green Meadows Residency",
      docType: "PAN Card",
      maskedDocNumber: "XXXXXXXX9911",
      experienceYears: 10,
      bgvStatus: "CLEAR",
      bgvPartner: "AuthBridge Verification",
      skills: ["Continental", "Italian", "North Indian"],
      status: "VERIFIED",
    },
  ]);

  const handleDecision = (id: string, decision: "VERIFIED" | "REJECTED") => {
    setCooks(
      cooks.map((c) => (c.id === id ? { ...c, status: decision } : c))
    );
    if (decision === "VERIFIED") {
      toast.success("Cook Partner verified! Enabled for OR-Tools CP-SAT scheduling.");
    } else {
      toast.error("Cook verification rejected.");
    }
  };

  const filteredCooks = cooks.filter((c) => {
    const matchesFilter =
      filter === "all" ||
      (filter === "pending" && c.status === "PENDING_REVIEW") ||
      (filter === "verified" && c.status === "VERIFIED");
    const matchesSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.phone.includes(search);
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Fleet Compliance & KYC Vault
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• Authoritative Audit</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Cook Fleet Oversight & KYC Verification Command
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Review government identity credentials, background verification logs, and certified culinary capabilities before granting access to household kitchens.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-surface-container border border-surface-container-high">
          <button
            onClick={() => setFilter("pending")}
            className={`px-3 py-1.5 rounded-lg text-xs font-label-md font-bold transition-all ${
              filter === "pending" ? "bg-white text-on-surface shadow-xs" : "text-on-surface-variant"
            }`}
          >
            Pending Review
          </button>
          <button
            onClick={() => setFilter("verified")}
            className={`px-3 py-1.5 rounded-lg text-xs font-label-md font-bold transition-all ${
              filter === "verified" ? "bg-white text-on-surface shadow-xs" : "text-on-surface-variant"
            }`}
          >
            Active Verified
          </button>
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-label-md font-bold transition-all ${
              filter === "all" ? "bg-white text-on-surface shadow-xs" : "text-on-surface-variant"
            }`}
          >
            All Fleet
          </button>
        </div>
      </div>

      {/* Fleet Cards Grid */}
      <div className="flex flex-col gap-5">
        {filteredCooks.map((cook) => (
          <div
            key={cook.id}
            className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary-fixed text-primary flex items-center justify-center font-bold text-lg shrink-0">
                <ChefHat className="w-6 h-6" />
              </div>

              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-headline-sm text-base font-bold text-on-surface">{cook.name}</h3>
                  <span
                    className={`px-2 py-0.5 rounded-full font-label-sm text-[10px] font-bold uppercase ${
                      cook.status === "VERIFIED"
                        ? "bg-tertiary-fixed text-on-tertiary-fixed"
                        : cook.status === "REJECTED"
                        ? "bg-error-container text-error"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {cook.status.replace("_", " ")}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs text-on-surface-variant font-body-sm">
                  <span>📱 {cook.phone}</span>
                  <span>•</span>
                  <span>✉️ {cook.email}</span>
                  <span>•</span>
                  <span>{cook.experienceYears} Years Exp</span>
                </div>

                {/* Document Verification & BGV Badge */}
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  <div className="px-2.5 py-1 rounded-lg bg-surface-container-low border border-surface-container text-xs font-label-md flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-primary" />
                    <span>{cook.docType}:</span>
                    <span className="font-mono font-bold text-on-surface">{cook.maskedDocNumber}</span>
                  </div>

                  <div className="px-2.5 py-1 rounded-lg bg-tertiary-fixed/40 border border-tertiary-fixed text-xs font-label-md text-tertiary flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>BGV: {cook.bgvStatus} ({cook.bgvPartner})</span>
                  </div>
                </div>

                {/* Cooking skills */}
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {cook.skills.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-white border border-surface-container font-label-sm text-[10px] text-on-surface font-semibold"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Decision Buttons */}
            {cook.status === "PENDING_REVIEW" && (
              <div className="flex items-center gap-2 w-full md:w-auto">
                <button
                  onClick={() => handleDecision(cook.id, "REJECTED")}
                  className="btn-glass-secondary px-4 py-2 rounded-xl text-xs font-bold text-error hover:bg-error-container/30 flex items-center gap-1.5"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Reject</span>
                </button>
                <button
                  onClick={() => handleDecision(cook.id, "VERIFIED")}
                  className="btn-gradient-primary px-5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve & Verify</span>
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

