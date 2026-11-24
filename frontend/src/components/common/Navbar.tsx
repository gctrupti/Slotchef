import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/useAuthStore";
import { Utensils, Building2, Bell, LogOut, User as UserIcon, ShieldAlert } from "lucide-react";

export const Navbar: React.FC = () => {
  const { user, activePortal, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-white/60 shadow-[0_1px_8px_rgba(15,23,42,0.04)]">
      <div className="h-16 w-full px-6 flex items-center justify-between gap-4">
        {/* Brand / Logo */}
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-white shadow-[0_4px_12px_rgba(37,99,235,0.25)] transition-transform group-hover:scale-105">
              <Utensils className="w-5 h-5" />
            </div>
            <span className="font-headline-sm text-xl font-bold tracking-tight text-on-surface">
              Slot<span className="text-primary">Chef</span>
            </span>
          </Link>

          {/* Gated Society Indicator */}
          <div className="hidden xl:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-surface-container text-on-surface-variant font-label-md text-xs font-semibold">
            <Building2 className="w-4 h-4 text-primary" />
            <span>Green Meadows Residency (Node #04)</span>
          </div>
        </div>

        {/* Right Section: Notification & User Profile Badge */}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              {/* Notification Bell */}
              <button
                type="button"
                className="relative p-2 rounded-xl text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors"
                title="Notifications"
              >
                <Bell className="w-5 h-5" />
                <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-error ring-2 ring-white"></span>
              </button>

              {/* User Profile Pill */}
              <div className="flex items-center gap-2.5 pl-2 border-l border-surface-container-high">
                <div className="w-8 h-8 rounded-full bg-primary-container text-white flex items-center justify-center font-bold text-xs uppercase shadow-sm">
                  {user.first_name ? user.first_name[0] : <UserIcon className="w-4 h-4" />}
                </div>
                <div className="hidden sm:flex flex-col text-left">
                  <span className="font-label-md text-xs font-bold text-on-surface leading-tight">
                    {user.first_name ? `${user.first_name} ${user.last_name || ""}` : user.email.split("@")[0]}
                  </span>
                  <span className="font-body-sm text-[10px] text-on-surface-variant leading-none uppercase tracking-wider font-semibold mt-0.5">
                    {activePortal === "admin" ? "Ops Command" : activePortal === "cook" ? "Cook Partner" : "Resident"}
                  </span>
                </div>

                <button
                  onClick={handleLogout}
                  title="Sign Out"
                  className="p-1.5 rounded-lg text-on-surface-variant hover:text-error hover:bg-error-container/30 transition-colors ml-1"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/household/login"
                className="px-4 py-2 rounded-xl font-label-md text-xs font-semibold text-primary hover:bg-surface-container transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/household/register"
                className="btn-gradient-primary px-4 py-2 rounded-xl font-label-md text-xs font-bold"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

