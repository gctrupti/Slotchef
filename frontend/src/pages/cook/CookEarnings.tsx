import React, { useState } from "react";
import { toast } from "sonner";
import {
  Wallet,
  ArrowUpRight,
  TrendingUp,
  CreditCard,
  Banknote,
  CheckCircle2,
  Clock,
  Download,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const earningsData = [
  { day: "Mon", amount: 1050 },
  { day: "Tue", amount: 1400 },
  { day: "Wed", amount: 1050 },
  { day: "Thu", amount: 700 },
  { day: "Fri", amount: 1400 },
  { day: "Sat", amount: 1750 },
  { day: "Sun", amount: 1400 },
];

export const CookEarnings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"all" | "completed" | "tips">("all");

  const transactions = [
    { id: "TX-901", date: "Today, 08:30 PM", household: "Sharma Household (B-402)", type: "Dinner Service", amount: 350, mode: "Online / Escrow", status: "PENDING_SETTLEMENT" },
    { id: "TX-900", date: "Today, 01:30 PM", household: "Verma Residence (B-104)", type: "Lunch Service", amount: 350, mode: "Cash Collected", status: "CASH_CONFIRMED" },
    { id: "TX-899", date: "Today, 08:30 AM", household: "Iyer Residence (A-201)", type: "Breakfast Service", amount: 350, mode: "Online / Escrow", status: "SETTLED" },
    { id: "TX-898", date: "Yesterday", household: "Gupta Family (A-502)", type: "Dinner Service", amount: 350, mode: "Online / Escrow", status: "SETTLED" },
    { id: "TX-897", date: "Yesterday", household: "Menon Home (B-301)", type: "Lunch Service", amount: 400, mode: "Online (+₹50 Tip)", status: "SETTLED" },
  ];

  const handleRequestPayout = () => {
    toast.success("Bank transfer initiated for ₹28,450 to your registered ICICI Bank account!");
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Weekly Escrow Clearing
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• 100% Guaranteed Payout</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Partner Earnings & Escrow Payouts
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Track your per-visit cooking compensation, cash-on-delivery reconciliation, and automated bank settlements.
          </p>
        </div>

        <button
          onClick={handleRequestPayout}
          className="btn-gradient-primary px-5 py-2.5 rounded-xl font-label-md text-xs font-bold flex items-center gap-2 shadow-glow-primary"
        >
          <ArrowUpRight className="w-4 h-4" />
          <span>Request Instant Payout</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Available for Payout
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-secondary font-mono">₹28,450</span>
          </div>
          <span className="text-[10px] text-tertiary font-semibold block mt-1">✓ Escrow cleared</span>
        </div>

        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            This Week's Gross
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-on-surface font-mono">₹8,750</span>
          </div>
          <span className="text-[10px] text-secondary font-semibold block mt-1">+18% vs last week</span>
        </div>

        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Cash in Hand Collected
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-on-surface font-mono">₹700</span>
          </div>
          <span className="text-[10px] text-on-surface-variant block mt-1">Commission deducted at source</span>
        </div>

        <div className="surface-glass rounded-2xl p-5 border border-white shadow-glass">
          <span className="text-[11px] font-label-sm text-on-surface-variant uppercase font-bold tracking-wider">
            Completed Visits
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="font-display-lg text-3xl font-extrabold text-tertiary font-mono">81</span>
          </div>
          <span className="text-[10px] text-on-surface-variant block mt-1">100% on-time execution</span>
        </div>
      </div>

      {/* Chart Section */}
      <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-secondary" />
            <h2 className="font-headline-sm text-base font-bold text-on-surface">Weekly Earnings Velocity (₹)</h2>
          </div>
          <span className="font-mono text-xs text-on-surface-variant font-bold">14 Nov - 20 Nov 2026</span>
        </div>

        <div className="h-64 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={earningsData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e7ff" />
              <XAxis dataKey="day" stroke="#737686" fontSize={12} tickLine={false} />
              <YAxis stroke="#737686" fontSize={12} tickLine={false} tickFormatter={(v) => `₹${v}`} />
              <Tooltip
                formatter={(val: number) => [`₹${val}`, "Earnings"]}
                contentStyle={{
                  backgroundColor: "rgba(255, 255, 255, 0.95)",
                  borderRadius: "12px",
                  border: "1px solid #c3c6d7",
                }}
              />
              <Bar dataKey="amount" fill="#00668a" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Transaction History Table */}
      <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="font-headline-sm text-base font-bold text-on-surface">Recent Visit Settlements</h2>
          <button
            onClick={() => toast.info("Exporting CSV...")}
            className="text-xs font-label-md text-secondary font-bold hover:underline flex items-center gap-1"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Statement</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-surface-container-high text-on-surface-variant font-label-sm uppercase tracking-wider">
                <th className="py-2.5 px-3">Reference</th>
                <th className="py-2.5 px-3">Time</th>
                <th className="py-2.5 px-3">Household</th>
                <th className="py-2.5 px-3">Service</th>
                <th className="py-2.5 px-3">Amount</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container-high/60 font-body-md">
              {transactions.map((t) => (
                <tr key={t.id} className="hover:bg-white/60 transition-colors">
                  <td className="py-3 px-3 font-mono font-bold text-on-surface">{t.id}</td>
                  <td className="py-3 px-3 text-on-surface-variant">{t.date}</td>
                  <td className="py-3 px-3 font-semibold text-on-surface">{t.household}</td>
                  <td className="py-3 px-3 text-on-surface-variant">{t.type}</td>
                  <td className="py-3 px-3 font-mono font-bold text-secondary">₹{t.amount}.00</td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-label-sm uppercase ${
                        t.status === "SETTLED"
                          ? "bg-tertiary-fixed text-on-tertiary-fixed"
                          : t.status === "CASH_CONFIRMED"
                          ? "bg-secondary-fixed text-on-secondary-fixed"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {t.status.replace("_", " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

