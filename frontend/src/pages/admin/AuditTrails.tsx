import React, { useState } from "react";
import {
  History,
  ShieldCheck,
  Search,
  Filter,
  Calendar,
  User,
  ArrowRight,
  Code,
  CheckCircle2,
  AlertTriangle,
  Layers,
  FileText,
  XCircle,
} from "lucide-react";

interface AuditEntry {
  id: string;
  actorEmail: string;
  actorName: string;
  action: string;
  entityType: string;
  entityId: string;
  reason: string;
  createdAt: string;
  beforeState: Record<string, unknown> | null;
  afterState: Record<string, unknown> | null;
}

export const AuditTrails: React.FC = () => {
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);

  const [auditLogs] = useState<AuditEntry[]>([
    {
      id: "aud-901",
      actorEmail: "admin@greenmeadows.ops",
      actorName: "Platform Commander",
      action: "schedule.plan_committed",
      entityType: "SchedulePlan",
      entityId: "plan-20270215-v1",
      reason: "CP-SAT multi-track schedule published for Green Meadows 2027-02-15",
      createdAt: "2026-11-14T08:30:00Z",
      beforeState: { status: "DRAFT", unassigned_count: 2 },
      afterState: { status: "COMMITTED", total_shifts: 68, version: 1 },
    },
    {
      id: "aud-902",
      actorEmail: "ops@slotchef.io",
      actorName: "Incident Dispatcher",
      action: "incident.backup_chef_dispatched",
      entityType: "BackupProposal",
      entityId: "bp-8841",
      reason: "Cook absence reported (vehicle breakdown). Automated CP-SAT backup chef Bob assigned.",
      createdAt: "2026-11-14T07:15:22Z",
      beforeState: { original_cook_id: "ck-101", status: "PENDING" },
      afterState: { backup_cook_id: "ck-104", status: "ACCEPTED", new_plan_version: 2 },
    },
    {
      id: "aud-903",
      actorEmail: "admin@greenmeadows.ops",
      actorName: "Platform Commander",
      action: "household.verification_reviewed",
      entityType: "HouseholdVerificationProfile",
      entityId: "ver-hh-201",
      reason: "Flat 402 Tower B residency agreement verified with society office NOC.",
      createdAt: "2026-11-13T16:45:10Z",
      beforeState: { status: "IN_REVIEW", society_noc_verified: false },
      afterState: { status: "VERIFIED", society_noc_verified: true },
    },
    {
      id: "aud-904",
      actorEmail: "finance@slotchef.io",
      actorName: "Automated Escrow Engine",
      action: "finance.cook_payout_processed",
      entityType: "CookPayout",
      entityId: "po-7712",
      reason: "Weekly net shift earnings payout dispatched via Razorpay Route payout ledger.",
      createdAt: "2026-11-13T12:00:00Z",
      beforeState: { status: "PENDING", gross_amount: "14800.00" },
      afterState: { status: "DISPATCHED", net_payout: "14060.00", commission: "740.00" },
    },
    {
      id: "aud-905",
      actorEmail: "priya.sharma@example.com",
      actorName: "Priya Sharma (Resident)",
      action: "booking.created",
      entityType: "BookingRequest",
      entityId: "bk-5509",
      reason: "South Indian Dinner (Masala Dosa + Sambar) requested for 2027-02-15 19:30.",
      createdAt: "2026-11-13T10:11:45Z",
      beforeState: null,
      afterState: { service_date: "2027-02-15", meal_type: "dinner", estimated_duration: 60 },
    },
  ]);

  const filtered = auditLogs.filter((entry) => {
    const matchesSearch =
      entry.action.toLowerCase().includes(search.toLowerCase()) ||
      entry.entityType.toLowerCase().includes(search.toLowerCase()) ||
      entry.actorEmail.toLowerCase().includes(search.toLowerCase()) ||
      entry.reason.toLowerCase().includes(search.toLowerCase());
    const matchesAction = actionFilter === "all" || entry.action.startsWith(actionFilter);
    return matchesSearch && matchesAction;
  });

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-primary-container text-white font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Immutable Governance
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• PostgreSQL Audit Log</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Security & System Audit Trails
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Tamper-proof chronological records of scheduling overrides, incident dispatches, financial payouts, and verification approvals.
          </p>
        </div>

        {/* Search & Action Filter */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-on-surface-variant absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search actions, emails..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none w-48 md:w-60"
            />
          </div>

          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-white border border-surface-container-high text-xs font-label-md font-semibold text-on-surface focus:border-primary focus:outline-none"
          >
            <option value="all">All Operations</option>
            <option value="schedule">Scheduling (CP-SAT)</option>
            <option value="incident">Incidents & Dispatches</option>
            <option value="household">Household Verification</option>
            <option value="finance">Finance & Payouts</option>
            <option value="booking">Bookings</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="surface-glass rounded-2xl border border-white shadow-glass overflow-hidden">
        <div className="p-4 border-b border-surface-container flex items-center justify-between text-xs font-label-md text-on-surface-variant">
          <span className="font-bold text-on-surface">Verified System Events ({filtered.length})</span>
          <span className="text-[11px] text-tertiary flex items-center gap-1 font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            Cryptographic Integrity Verified
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-body-md">
            <thead className="bg-surface-container-low border-b border-surface-container text-on-surface-variant font-label-sm uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-5 py-3.5">Timestamp</th>
                <th className="px-5 py-3.5">Action Event</th>
                <th className="px-5 py-3.5">Target Entity</th>
                <th className="px-5 py-3.5">Actor / Origin</th>
                <th className="px-5 py-3.5">Audit Note</th>
                <th className="px-5 py-3.5 text-right">State Diff</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container">
              {filtered.map((log) => (
                <tr key={log.id} className="hover:bg-surface-container-low/60 transition-colors">
                  <td className="px-5 py-4 font-mono text-[11px] text-on-surface-variant whitespace-nowrap">
                    {new Date(log.createdAt).toLocaleString()}
                  </td>
                  <td className="px-5 py-4">
                    <span className="px-2.5 py-1 rounded-md bg-primary-fixed text-primary font-mono font-bold text-[11px]">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-5 py-4 font-medium text-on-surface">
                    <span className="font-semibold block">{log.entityType}</span>
                    <span className="text-[10px] font-mono text-on-surface-variant">{log.entityId}</span>
                  </td>
                  <td className="px-5 py-4">
                    <span className="font-semibold text-on-surface block">{log.actorName}</span>
                    <span className="text-[10px] font-mono text-on-surface-variant">{log.actorEmail}</span>
                  </td>
                  <td className="px-5 py-4 text-on-surface-variant max-w-xs truncate">{log.reason}</td>
                  <td className="px-5 py-4 text-right">
                    <button
                      onClick={() => setSelectedEntry(log)}
                      className="btn-glass-secondary px-3 py-1.5 rounded-lg text-xs font-bold text-primary flex items-center gap-1.5 ml-auto"
                    >
                      <Code className="w-3.5 h-3.5" />
                      <span>Inspect Diff</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* JSON Diff Inspector Modal */}
      {selectedEntry && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md">
          <div className="surface-glass rounded-2xl p-6 md:p-8 max-w-2xl w-full border border-white shadow-2xl flex flex-col gap-5">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-label-sm text-primary uppercase font-bold tracking-wider">
                  Audit Snapshot Inspector
                </span>
                <h3 className="font-headline-sm text-lg font-bold text-on-surface mt-1">
                  Event: <span className="font-mono text-primary">{selectedEntry.action}</span>
                </h3>
                <span className="text-xs text-on-surface-variant font-mono">
                  Target: {selectedEntry.entityType} ({selectedEntry.entityId})
                </span>
              </div>
              <button
                onClick={() => setSelectedEntry(null)}
                className="p-1 rounded-lg text-on-surface-variant hover:bg-surface-container"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs font-body-sm text-on-surface-variant bg-surface-container-low p-3 rounded-xl border border-surface-container">
              {selectedEntry.reason}
            </p>

            {/* Side-by-Side Diff */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <span className="text-[11px] font-label-sm font-bold text-error uppercase">Before State:</span>
                <pre className="p-3 rounded-xl bg-slate-900 text-slate-100 font-mono text-[11px] overflow-x-auto max-h-48">
                  {selectedEntry.beforeState
                    ? JSON.stringify(selectedEntry.beforeState, null, 2)
                    : "// No prior state (Created)"}
                </pre>
              </div>

              <div className="flex flex-col gap-1.5">
                <span className="text-[11px] font-label-sm font-bold text-tertiary uppercase">After State:</span>
                <pre className="p-3 rounded-xl bg-slate-900 text-emerald-400 font-mono text-[11px] overflow-x-auto max-h-48">
                  {JSON.stringify(selectedEntry.afterState, null, 2)}
                </pre>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedEntry(null)}
                className="btn-gradient-primary px-5 py-2 rounded-xl text-xs font-bold"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

