import React from "react";
import { BrowserRouter } from "react-router-dom";
import { AppRoutes } from "@/routes/AppRoutes";
import { Toaster } from "sonner";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppRoutes />
      <Toaster
        position="top-right"
        richColors
        closeButton
        toastOptions={{
          style: {
            borderRadius: "16px",
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: "13px",
            padding: "12px 16px",
          },
        }}
      />
    </BrowserRouter>
  );
};

