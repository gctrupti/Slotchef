import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/useAuthStore";
import {
  Home,
  CalendarDays,
  Clock,
  Package,
  ShieldAlert,
  Flame,
  ChefHat,
  Wallet,
  Sparkles,
  ClipboardList,
  Users,
  Settings,
  History,
  Activity,
  Layers,
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const { activePortal } = useAuthStore();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const householdNavItems = [
    { label: "Home & Dashboard", path: "/household", icon: Home },
    { label: "Smart Slot Booking", path: "/household/booking", icon: CalendarDays },
    { label: "Meal Menu & Cuisines", path: "/household/menu", icon: Flame },
    { label: "Live Shift Tracker", path: "/household/tracker", icon: Clock },
    { label: "Plan & Packages", path: "/household/packages", icon: Package },
    { label: "Dietary Vault", path: "/household/dietary", icon: Sparkles },
    { label: "Safety Center", path: "/household/safety", icon: ShieldAlert },
  ];

  const cookNavItems = [
    { label: "Cook Dashboard", path: "/cook", icon: Home },
    { label: "Daily Schedule Roster", path: "/cook/schedule", icon: CalendarDays },
    { label: "Active Shift Cockpit", path: "/cook/shift-active", icon: Activity },
    { label: "Dish Repertoire", path: "/cook/repertoire", icon: ChefHat },
    { label: "Earnings & Escrow", path: "/cook/earnings", icon: Wallet },
    { label: "Safety Center", path: "/cook/safety", icon: ShieldAlert },
  ];

  const adminNavItems = [
    { label: "Command Overview", path: "/admin", icon: Home },
    { label: "Master Schedule Board", path: "/admin/schedule", icon: Layers },
    { label: "Cook Fleet & KYC", path: "/admin/cooks", icon: Users },
    { label: "Incident Vault & SOS", path: "/admin/incidents", icon: ShieldAlert },
    { label: "Household Oversight", path: "/admin/households", icon: ClipboardList },
    { label: "Audit Trails", path: "/admin/audit", icon: History },
  ];

  const navItems =
    activePortal === "admin"
      ? adminNavItems
      : activePortal === "cook"
      ? cookNavItems
      : householdNavItems;

  const portalTitle =
    activePortal === "admin"
      ? "Admin Operations"
      : activePortal === "cook"
      ? "Cook Fleet Roster"
      : "Household Workflow";

  return (
    <aside className="fixed left-0 top-0 h-full w-64 pt-16 bg-white/70 backdrop-blur-xl z-40 flex flex-col justify-between border-r border-surface-container-high/60 shadow-[0_1px_8px_rgba(15,23,42,0.03)]">
      <div className="px-4 py-6 flex flex-col gap-6 overflow-y-auto">
        <div className="flex flex-col gap-1.5">
          <div className="px-3 py-1 text-on-surface-variant font-label-sm text-[11px] uppercase tracking-wider font-bold">
            {portalTitle}
          </div>

          <nav className="flex flex-col gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-label-md text-xs font-semibold transition-all ${
                    active
                      ? "bg-primary-container text-white shadow-[0_4px_12px_rgba(37,99,235,0.25)]"
                      : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? "text-white" : "text-primary"}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Safety Shield Footer Badge */}
      <div className="p-4 border-t border-surface-container-high/60">
        <div className="p-3 rounded-xl bg-surface-container-low border border-surface-container flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-tertiary-container flex items-center justify-center text-white shrink-0">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <span className="font-label-sm text-[11px] font-bold text-on-surface">Safety Shield 100%</span>
            <span className="font-body-sm text-[10px] text-on-surface-variant">Verified hygiene & SOS active</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

