import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/useAuthStore";
import { extractErrorMessage } from "@/api/client";
import { toast } from "sonner";
import { Utensils, Lock, User, ArrowRight, Loader2, KeyRound } from "lucide-react";

const loginSchema = z.object({
  identifier: z.string().min(3, "Please enter registered email address or phone number"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const HouseholdLogin: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const fillDemo = () => {
    setValue("identifier", "priya.sharma@example.com");
    setValue("password", "Resident1234!");
  };

  const onSubmit = async (data: LoginFormData) => {
    try {
      setLoading(true);
      const res = await authApi.login({
        identifier: data.identifier,
        password: data.password,
      });

      if (res.user && res.access) {
        setAuth(res.user, res.access, res.refresh);
        toast.success(`Welcome back, ${res.user.first_name || "Resident"}!`);
        navigate("/household");
      }
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#faf8ff] via-[#f0f4f8] to-[#eaedff] flex items-center justify-center p-4 md:p-8 font-sans">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-6">
          <Link to="/" className="inline-flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center text-white shadow-sm">
              <Utensils className="w-4 h-4" />
            </div>
            <span className="font-headline-sm text-xl font-bold tracking-tight text-on-surface">
              Slot<span className="text-primary">Chef</span>
            </span>
          </Link>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-bold text-on-surface">
            Resident Sign-In
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant mt-1">
            Access your household kitchen schedule and recurring cooking slots.
          </p>
        </div>

        {/* Card */}
        <div className="surface-glass rounded-2xl p-6 md:p-8 border border-white shadow-glass-elevated">
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div>
              <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                Registered Email or Mobile Phone
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-on-surface-variant absolute left-3 top-3" />
                <input
                  {...register("identifier")}
                  type="text"
                  placeholder="e.g. resident@godrej.test or +919876543210"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                />
              </div>
              {errors.identifier && (
                <p className="text-[11px] text-error mt-0.5">{errors.identifier.message}</p>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-label-md font-semibold text-on-surface">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-[11px] font-label-sm text-primary hover:underline font-semibold"
                >
                  Forgot Password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-on-surface-variant absolute left-3 top-3" />
                <input
                  {...register("password")}
                  type="password"
                  placeholder="Enter your password"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                />
              </div>
              {errors.password && (
                <p className="text-[11px] text-error mt-0.5">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-gradient-primary w-full py-3 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2 mt-2 shadow-glow-primary"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Sign In to Household"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Helper */}
          <div
            onClick={fillDemo}
            className="mt-5 p-3 rounded-xl bg-surface-container-low border border-surface-container text-[11px] text-on-surface-variant cursor-pointer hover:bg-surface-container transition-all"
            title="Click to auto-fill credentials"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-primary">Quick Demo Login:</span>
              <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-bold">Click to Auto-fill</span>
            </div>
            <div>
              <span>Email: <code className="font-mono text-on-surface font-semibold">priya.sharma@example.com</code></span>
              <span className="mx-2">•</span>
              <span>Password: <code className="font-mono text-on-surface font-semibold">Resident1234!</code></span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6 text-xs font-body-sm text-on-surface-variant">
          New to SlotChef?{" "}
          <Link to="/household/register" className="text-primary font-semibold hover:underline">
            Register your Household
          </Link>
        </div>
      </div>
    </div>
  );
};

