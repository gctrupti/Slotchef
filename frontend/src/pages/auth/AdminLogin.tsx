import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/useAuthStore";
import { extractErrorMessage } from "@/api/client";
import { toast } from "sonner";
import { ShieldCheck, Lock, User, ArrowRight, Loader2, KeyRound } from "lucide-react";

const adminLoginSchema = z.object({
  identifier: z.string().min(3, "Please enter admin email or identifier"),
  password: z.string().min(1, "Password is required"),
});

type AdminLoginData = z.infer<typeof adminLoginSchema>;

export const AdminLogin: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaToken, setMfaToken] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<AdminLoginData>({
    resolver: zodResolver(adminLoginSchema),
  });

  const fillDemo = () => {
    setValue("identifier", "admin@greenmeadows.ops");
    setValue("password", "Admin1234!");
  };

  const onSubmit = async (data: AdminLoginData) => {
    try {
      setLoading(true);
      const res = await authApi.login({
        identifier: data.identifier,
        password: data.password,
      });

      if (res.mfa_required && res.mfa_token) {
        setMfaRequired(true);
        setMfaToken(res.mfa_token);
        toast.info("Step-Up Multi-Factor Authentication required for Admin access");
      } else if (res.user && res.access) {
        // Direct login if MFA is not enforced
        setAuth(res.user, res.access, res.refresh);
        toast.success(`Welcome to Ops Command, ${res.user.first_name || "Admin"}!`);
        navigate("/admin");
      }
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const onVerifyMFA = async () => {
    if (otpCode.length !== 6) {
      toast.error("Please enter the 6-digit MFA challenge code");
      return;
    }

    try {
      setLoading(true);
      const res = await authApi.verifyAdminMFA(mfaToken, otpCode);
      if (res.user && res.access) {
        setAuth(res.user, res.access, res.refresh);
        toast.success("Admin MFA verified. Entering Master Command Center...");
        navigate("/admin");
      }
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#131b2e] via-[#1a2238] to-[#0f172a] flex items-center justify-center p-4 md:p-8 font-sans text-white">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-6">
          <Link to="/" className="inline-flex items-center gap-2 mb-3">
            <div className="w-10 h-10 rounded-2xl bg-primary flex items-center justify-center text-white shadow-glow-primary">
              <ShieldCheck className="w-6 h-6" />
            </div>
          </Link>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-bold tracking-tight text-white">
            SlotChef Admin Master Command
          </h1>
          <p className="font-body-md text-xs md:text-sm text-surface-container-high mt-1">
            Gated operations scheduling, live KYC fleet oversight, and incident telemetry.
          </p>
        </div>

        {/* Card Shell */}
        <div className="surface-glass-dark rounded-2xl p-6 md:p-8 border border-white/10 shadow-2xl">
          {!mfaRequired ? (
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-label-md font-semibold text-surface-container-highest mb-1">
                  Administrator Identifier
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-surface-container-high absolute left-3 top-3" />
                  <input
                    {...register("identifier")}
                    type="text"
                    placeholder="admin@slotchef.test"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/10 border border-white/15 text-xs text-white placeholder-white/40 focus:border-primary focus:outline-none"
                  />
                </div>
                {errors.identifier && (
                  <p className="text-[11px] text-error-container mt-0.5">{errors.identifier.message}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-label-md font-semibold text-surface-container-highest mb-1">
                  Master Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-surface-container-high absolute left-3 top-3" />
                  <input
                    {...register("password")}
                    type="password"
                    placeholder="Enter admin password"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/10 border border-white/15 text-xs text-white placeholder-white/40 focus:border-primary focus:outline-none"
                  />
                </div>
                {errors.password && (
                  <p className="text-[11px] text-error-container mt-0.5">{errors.password.message}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-gradient-primary w-full py-3 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2 mt-2 shadow-glow-primary"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Authenticate Ops Command"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          ) : (
            <div className="flex flex-col items-center gap-5 py-2">
              <div className="w-12 h-12 rounded-full bg-primary/20 text-primary flex items-center justify-center">
                <KeyRound className="w-6 h-6 text-primary-fixed" />
              </div>

              <div className="text-center">
                <h3 className="font-headline-sm text-lg font-bold">Step-Up MFA Challenge</h3>
                <p className="font-body-sm text-xs text-white/70 mt-1 max-w-xs">
                  Enter the 6-digit challenge code sent to your verified administrator contact channel.
                </p>
              </div>

              <input
                type="text"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                placeholder="123456"
                className="w-40 text-center text-2xl font-mono font-bold tracking-widest py-2 rounded-xl bg-white/10 border border-white/20 text-white focus:border-primary focus:outline-none"
              />

              <button
                type="button"
                onClick={onVerifyMFA}
                disabled={loading}
                className="btn-gradient-primary w-full py-3 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2 shadow-glow-primary"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Verify MFA & Access Command"}
                <ShieldCheck className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={() => setMfaRequired(false)}
                className="text-xs text-white/60 hover:text-white"
              >
                ← Back to Password Sign-In
              </button>
            </div>
          )}

          {/* Quick Demo Helper */}
          <div
            onClick={fillDemo}
            className="mt-5 p-3 rounded-xl bg-white/5 border border-white/10 text-[11px] text-white/70 cursor-pointer hover:bg-white/10 transition-all"
            title="Click to auto-fill credentials"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-primary">Quick Ops Demo:</span>
              <span className="text-[10px] bg-primary/20 text-primary px-2 py-0.5 rounded-full font-bold">Click to Auto-fill</span>
            </div>
            <div>
              <span>Email: <code className="font-mono text-white font-semibold">admin@greenmeadows.ops</code></span>
              <span className="mx-2">•</span>
              <span>Password: <code className="font-mono text-white font-semibold">Admin1234!</code></span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-white/10 text-center">
            <span className="text-[10px] font-label-sm text-white/40 uppercase tracking-widest">
              Restricted Area • All access attempts are recorded in immutable audit logs
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

