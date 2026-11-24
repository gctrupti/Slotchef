import React from "react";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { useAuthStore } from "@/store/useAuthStore";

interface AppLayoutProps {
  children: React.ReactNode;
  showSidebar?: boolean;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children, showSidebar = true }) => {
  const { user } = useAuthStore();
  const displaySidebar = showSidebar && !!user;

  return (
    <div className="min-h-screen bg-background flex flex-col font-sans">
      <Navbar />
      <div className="flex flex-1 pt-16">
        {displaySidebar && <Sidebar />}
        <main className={`flex-1 w-full transition-all duration-300 ${displaySidebar ? "pl-64" : ""}`}>
          <div className="p-6 md:p-8 max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

