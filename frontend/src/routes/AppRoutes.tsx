import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/useAuthStore";
import { AppLayout } from "@/components/common/AppLayout";

// Auth Pages
import { PortalSelector } from "@/pages/auth/PortalSelector";
import { HouseholdLogin } from "@/pages/auth/HouseholdLogin";
import { HouseholdRegister } from "@/pages/auth/HouseholdRegister";
import { CookLogin } from "@/pages/auth/CookLogin";
import { CookRegister } from "@/pages/auth/CookRegister";
import { AdminLogin } from "@/pages/auth/AdminLogin";
import { ForgotPassword } from "@/pages/auth/ForgotPassword";

// Household Pages
import { HouseholdHome } from "@/pages/household/HouseholdHome";
import { SmartSlotBooking } from "@/pages/household/SmartSlotBooking";
import { MealMenu } from "@/pages/household/MealMenu";
import { LiveShiftTracker } from "@/pages/household/LiveShiftTracker";
import { PlanSubscription } from "@/pages/household/PlanSubscription";
import { DietaryVault } from "@/pages/household/DietaryVault";
import { HouseholdSafetyCenter } from "@/pages/household/HouseholdSafetyCenter";

// Cook Pages
import { CookHome } from "@/pages/cook/CookHome";
import { DailyShiftRoster } from "@/pages/cook/DailyShiftRoster";
import { ActiveShiftCockpit } from "@/pages/cook/ActiveShiftCockpit";
import { DishRepertoire } from "@/pages/cook/DishRepertoire";
import { CookEarnings } from "@/pages/cook/CookEarnings";

// Admin Pages
import { AdminDashboard } from "@/pages/admin/AdminDashboard";
import { CookFleetOversight } from "@/pages/admin/CookFleetOversight";
import { IncidentVault } from "@/pages/admin/IncidentVault";
import { MasterScheduleBoard } from "@/pages/admin/MasterScheduleBoard";
import { HouseholdOversight } from "@/pages/admin/HouseholdOversight";
import { AuditTrails } from "@/pages/admin/AuditTrails";

// Route Guard Component
const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles?: string[];
}> = ({ children }) => {
  const { user } = useAuthStore();

  if (!user) {
    return <Navigate to="/household/login" replace />;
  }

  return <AppLayout>{children}</AppLayout>;
};

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Landing & Auth Gates */}
      <Route path="/" element={<PortalSelector />} />
      <Route path="/household/login" element={<HouseholdLogin />} />
      <Route path="/household/register" element={<HouseholdRegister />} />
      <Route path="/cook/login" element={<CookLogin />} />
      <Route path="/cook/register" element={<CookRegister />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* Household Portal */}
      <Route
        path="/household"
        element={
          <ProtectedRoute>
            <HouseholdHome />
          </ProtectedRoute>
        }
      />
      <Route
        path="/household/booking"
        element={
          <ProtectedRoute>
            <SmartSlotBooking />
          </ProtectedRoute>
        }
      />
      <Route
        path="/household/menu"
        element={
          <ProtectedRoute>
            <MealMenu />
          </ProtectedRoute>
        }
      />
      <Route
        path="/household/tracker"
        element={
          <ProtectedRoute>
            <LiveShiftTracker />
          </ProtectedRoute>
        }
      />
      <Route
        path="/household/packages"
        element={
          <ProtectedRoute>
            <PlanSubscription />
          </ProtectedRoute>
        }
      />
      <Route
        path="/household/dietary"
        element={
          <ProtectedRoute>
            <DietaryVault />
          </ProtectedRoute>
        }
      />
      <Route
        path="/household/safety"
        element={
          <ProtectedRoute>
            <HouseholdSafetyCenter />
          </ProtectedRoute>
        }
      />

      {/* Cook Portal */}
      <Route
        path="/cook"
        element={
          <ProtectedRoute>
            <CookHome />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cook/schedule"
        element={
          <ProtectedRoute>
            <DailyShiftRoster />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cook/shift-active"
        element={
          <ProtectedRoute>
            <ActiveShiftCockpit />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cook/repertoire"
        element={
          <ProtectedRoute>
            <DishRepertoire />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cook/earnings"
        element={
          <ProtectedRoute>
            <CookEarnings />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cook/safety"
        element={
          <ProtectedRoute>
            <HouseholdSafetyCenter />
          </ProtectedRoute>
        }
      />

      {/* Admin Portal */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/schedule"
        element={
          <ProtectedRoute>
            <MasterScheduleBoard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/cooks"
        element={
          <ProtectedRoute>
            <CookFleetOversight />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/incidents"
        element={
          <ProtectedRoute>
            <IncidentVault />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/households"
        element={
          <ProtectedRoute>
            <HouseholdOversight />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/audit"
        element={
          <ProtectedRoute>
            <AuditTrails />
          </ProtectedRoute>
        }
      />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

