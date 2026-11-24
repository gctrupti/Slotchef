import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth";
import { extractErrorMessage } from "@/api/client";
import { toast } from "sonner";
import { Utensils, Lock, KeyRound, ArrowRight, Loader2, CheckCircle2 } from "lucide-react";

export const ForgotPassword: React.FC = () => {
  const [step, setStep] = useState<1 | 2>(1);
  const [target, setTarget] = useState("");
  const [channel, setChannel] = useState<"sms" | "email">("email");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!target) {
      toast.error("Please enter your registered email address or mobile phone");
      return;
    }

    try {
      setLoading(true);
      await authApi.requestPasswordReset(target, channel);
      toast.success(`Password reset OTP sent to ${target}`);
      setStep(2);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otp.length !== 6) {
      toast.error("Please enter the 6-digit OTP");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("New password must be at least 8 characters long");
      return;
    }

    try {
      setLoading(true);
      await authApi.confirmPasswordReset(target, channel, otp, newPassword);
      toast.success("Password successfully updated! Please sign in with your new credentials.");
      navigate("/household/login");
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#faf8ff] via-[#f0f4f8] to-[#eaedff] flex items-center justify-center p-4 md:p-8 font-sans">
      <div className="max-w-md w-full">
        <div className="text-center mb-6">
          <Link to="/" className="inline-flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center text-white shadow-sm">
              <Utensils className="w-4 h-4" />
            </div>
            <span className="font-headline-sm text-xl font-bold tracking-tight text-on-surface">
              Slot<span className="text-primary">Chef</span>
            </span>
          </Link>
          <h1 className="font-headline-lg text-2xl font-bold text-on-surface">Reset Password</h1>
          <p className="font-body-md text-xs text-on-surface-variant mt-1">
            Verify your registered contact channel to securely update credentials.
          </p>
        </div>

        <div className="surface-glass rounded-2xl p-6 md:p-8 border border-white shadow-glass-elevated">
          {step === 1 ? (
            <form onSubmit={handleRequestOtp} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                  Registered Contact Target
                </label>
                <input
                  type="text"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  placeholder="e.g. resident@godrej.test or +919876543210"
                  className="w-full px-3 py-2.5 rounded-xl bg-white border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                  Delivery Channel
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <label className="flex items-center gap-2 p-2.5 rounded-xl border border-surface-container-high cursor-pointer hover:bg-white/60">
                    <input
                      type="radio"
                      name="channel"
                      value="email"
                      checked={channel === "email"}
                      onChange={() => setChannel("email")}
                    />
                    <span className="text-xs font-semibold">Email OTP</span>
                  </label>
                  <label className="flex items-center gap-2 p-2.5 rounded-xl border border-surface-container-high cursor-pointer hover:bg-white/60">
                    <input
                      type="radio"
                      name="channel"
                      value="sms"
                      checked={channel === "sms"}
                      onChange={() => setChannel("sms")}
                    />
                    <span className="text-xs font-semibold">SMS to Phone</span>
                  </label>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-gradient-primary w-full py-3 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2 mt-2 shadow-glow-primary"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Dispatch Reset OTP"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          ) : (
            <form onSubmit={handleConfirmReset} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                  6-Digit OTP Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="123456"
                  className="w-full text-center text-xl font-mono font-bold tracking-widest py-2 rounded-xl bg-white border border-surface-container-high focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="w-full px-3 py-2 rounded-xl bg-white border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-gradient-primary w-full py-3 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2 shadow-glow-primary"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save New Password"}
                <CheckCircle2 className="w-4 h-4" />
              </button>
            </form>
          )}

          <div className="text-center mt-5 text-xs font-label-md">
            <Link to="/household/login" className="text-on-surface-variant hover:text-on-surface">
              ← Return to Sign-In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

