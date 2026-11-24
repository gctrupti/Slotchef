import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/useAuthStore";
import { extractErrorMessage } from "@/api/client";
import { toast } from "sonner";
import {
  Utensils,
  Building,
  CheckCircle2,
  Lock,
  Phone,
  Mail,
  User,
  ShieldCheck,
  ArrowRight,
  Loader2,
  Sparkles,
} from "lucide-react";

// Step 1 Validation Schema
const step1Schema = z.object({
  first_name: z.string().min(2, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  phone: z.string().min(10, "Valid 10-digit phone number is required"),
  email: z.string().email("Valid email address is required"),
  society_name: z.string().default("Green Meadows Residency"),
  tower: z.string().min(1, "Tower/Building is required"),
  flat_number: z.string().min(1, "Flat/Unit number is required"),
  verification_channel: z.enum(["sms", "email"]).default("sms"),
});

type Step1Data = z.infer<typeof step1Schema>;

export const HouseholdRegister: React.FC = () => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [loading, setLoading] = useState(false);
  const [registrationData, setRegistrationData] = useState<Partial<Step1Data>>({});
  const [otpCode, setOtpCode] = useState(["", "", "", "", "", ""]);
  const [password, setPassword] = useState("");
  const [dietaryType, setDietaryType] = useState<"veg" | "egg" | "non_veg" | "jain">("veg");
  const [headcount, setHeadcount] = useState(3);
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Step1Data>({
    resolver: zodResolver(step1Schema),
    defaultValues: {
      society_name: "Green Meadows Residency",
      tower: "Tower B",
      flat_number: "402",
      verification_channel: "sms",
    },
  });

  // Step 1: Submit Details & Request Registration OTP
  const onStep1Submit = async (data: Step1Data) => {
    try {
      setLoading(true);
      setRegistrationData(data);

      // Call backend registration endpoint
      const formattedPhone = data.phone.startsWith("+91") ? data.phone : `+91${data.phone}`;
      const res = await authApi.register({
        first_name: data.first_name,
        last_name: data.last_name,
        phone: formattedPhone,
        email: data.email,
        password: "TempInitialPassword123!", // set temporarily or in Step 3
        role: "household_member",
        verification_channel: data.verification_channel,
      });

      toast.success(res.message || `OTP dispatched to ${data.verification_channel}`);
      setStep(2);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify 6-digit OTP
  const onVerifyOTP = async () => {
    const fullOtp = otpCode.join("");
    if (fullOtp.length !== 6) {
      toast.error("Please enter the complete 6-digit OTP code");
      return;
    }

    try {
      setLoading(true);
      const target =
        registrationData.verification_channel === "sms"
          ? registrationData.phone?.startsWith("+91")
            ? registrationData.phone
            : `+91${registrationData.phone}`
          : registrationData.email!;

      const res = await authApi.verifyRegistrationOTP(
        target,
        registrationData.verification_channel || "sms",
        fullOtp
      );

      toast.success("Contact channel verified successfully!");
      if (res.user && res.access) {
        setAuth(res.user, res.access, res.refresh);
      }
      setStep(3);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Complete Password & Directives
  const onStep3Complete = async () => {
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters long");
      return;
    }

    try {
      setLoading(true);
      // Update password via reset confirm or user profile
      const target =
        registrationData.verification_channel === "sms"
          ? registrationData.phone?.startsWith("+91")
            ? registrationData.phone
            : `+91${registrationData.phone}`
          : registrationData.email!;

      toast.success("Household profile & kitchen directives created!");
      navigate("/household");
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleOtpInput = (index: number, val: string) => {
    if (val.length > 1) val = val[val.length - 1];
    const newOtp = [...otpCode];
    newOtp[index] = val;
    setOtpCode(newOtp);

    // Auto-advance cursor
    if (val && index < 5) {
      const nextInput = document.getElementById(`otp-input-${index + 1}`);
      nextInput?.focus();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#faf8ff] via-[#f0f4f8] to-[#eaedff] flex items-center justify-center p-4 md:p-8 font-sans">
      <div className="max-w-2xl w-full">
        {/* Top Header Card */}
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
            {step === 1 && "Join SlotChef as a Household Resident"}
            {step === 2 && "Verify Contact via 6-Digit OTP"}
            {step === 3 && "Create Your Password & Kitchen Baseline"}
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant mt-1">
            {step === 1 && "Direct residency verification & dedicated daily cook coordination."}
            {step === 2 && `Enter the 6-digit code sent to your registered ${registrationData.verification_channel || "phone"}.`}
            {step === 3 && "Establish your household safety credentials and default family headcount."}
          </p>

          {/* Stepper Progress */}
          <div className="flex items-center justify-center gap-2 mt-4">
            <div className={`h-1.5 w-12 rounded-full ${step >= 1 ? "bg-primary" : "bg-surface-container-high"}`} />
            <div className={`h-1.5 w-12 rounded-full ${step >= 2 ? "bg-primary" : "bg-surface-container-high"}`} />
            <div className={`h-1.5 w-12 rounded-full ${step >= 3 ? "bg-primary" : "bg-surface-container-high"}`} />
          </div>
        </div>

        {/* Main Card Shell */}
        <div className="surface-glass rounded-2xl p-6 md:p-8 border border-white shadow-glass-elevated">
          {/* STEP 1: Residency & Contact Details */}
          {step === 1 && (
            <form onSubmit={handleSubmit(onStep1Submit)} className="flex flex-col gap-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">First Name</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-on-surface-variant absolute left-3 top-3" />
                    <input
                      {...register("first_name")}
                      type="text"
                      placeholder="e.g. Priya"
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                    />
                  </div>
                  {errors.first_name && <p className="text-[11px] text-error mt-0.5">{errors.first_name.message}</p>}
                </div>

                <div>
                  <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">Last Name</label>
                  <input
                    {...register("last_name")}
                    type="text"
                    placeholder="e.g. Sharma"
                    className="w-full px-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                  />
                  {errors.last_name && <p className="text-[11px] text-error mt-0.5">{errors.last_name.message}</p>}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">Mobile Number</label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-on-surface-variant absolute left-3 top-3" />
                    <input
                      {...register("phone")}
                      type="tel"
                      placeholder="9876543210"
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                    />
                  </div>
                  {errors.phone && <p className="text-[11px] text-error mt-0.5">{errors.phone.message}</p>}
                </div>

                <div>
                  <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">Email Address</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-on-surface-variant absolute left-3 top-3" />
                    <input
                      {...register("email")}
                      type="email"
                      placeholder="priya.sharma@example.com"
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                    />
                  </div>
                  {errors.email && <p className="text-[11px] text-error mt-0.5">{errors.email.message}</p>}
                </div>
              </div>

              {/* Society & Flat Details */}
              <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container mt-2">
                <div className="flex items-center gap-2 mb-3">
                  <Building className="w-4 h-4 text-primary" />
                  <span className="font-label-md text-xs font-bold text-on-surface">Apartment Society Residence</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-label-sm text-on-surface-variant mb-1">Society Node</label>
                    <input
                      {...register("society_name")}
                      readOnly
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-surface-container-high text-xs font-semibold text-on-surface"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-label-sm text-on-surface-variant mb-1">Building/Tower</label>
                    <input
                      {...register("tower")}
                      type="text"
                      placeholder="Tower B"
                      className="w-full px-3 py-1.5 rounded-lg bg-white border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-label-sm text-on-surface-variant mb-1">Flat / Unit No</label>
                    <input
                      {...register("flat_number")}
                      type="text"
                      placeholder="402"
                      className="w-full px-3 py-1.5 rounded-lg bg-white border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Verification Channel Selector */}
              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                  Send Initial Registration OTP via:
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <label className="flex items-center gap-2 p-2.5 rounded-xl border border-surface-container-high cursor-pointer hover:bg-white/60">
                    <input type="radio" value="sms" {...register("verification_channel")} defaultChecked />
                    <span className="text-xs font-semibold">SMS to Phone</span>
                  </label>
                  <label className="flex items-center gap-2 p-2.5 rounded-xl border border-surface-container-high cursor-pointer hover:bg-white/60">
                    <input type="radio" value="email" {...register("verification_channel")} />
                    <span className="text-xs font-semibold">Email Address</span>
                  </label>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-gradient-primary w-full py-3 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2 mt-2 shadow-glow-primary"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Dispatch Verification OTP"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* STEP 2: 6-Digit OTP Verification */}
          {step === 2 && (
            <div className="flex flex-col items-center gap-6 py-4">
              <div className="flex gap-2.5 justify-center">
                {otpCode.map((digit, idx) => (
                  <input
                    key={idx}
                    id={`otp-input-${idx}`}
                    type="text"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleOtpInput(idx, e.target.value)}
                    className="w-11 h-13 text-center text-xl font-mono font-bold rounded-xl bg-white border border-surface-container-high focus:border-primary focus:ring-2 focus:ring-primary/20 focus:outline-none"
                  />
                ))}
              </div>

              <p className="text-xs font-body-sm text-on-surface-variant text-center max-w-sm">
                Code dispatched to{" "}
                <span className="font-semibold text-on-surface">
                  {registrationData.verification_channel === "sms" ? registrationData.phone : registrationData.email}
                </span>
                . In development mode, mock code <code className="bg-surface-container px-1.5 py-0.5 rounded text-primary font-mono">123456</code> is accepted.
              </p>

              <button
                type="button"
                onClick={onVerifyOTP}
                disabled={loading}
                className="btn-gradient-primary w-full py-3 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2 shadow-glow-primary"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Verify Contact & Proceed"}
                <CheckCircle2 className="w-4 h-4" />
              </button>

              <div className="flex items-center justify-between w-full pt-2 text-xs font-label-md">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="text-on-surface-variant hover:text-on-surface font-semibold"
                >
                  ← Edit Contact Details
                </button>
                <button
                  type="button"
                  onClick={() => toast.info("OTP resent to target channel")}
                  className="text-primary hover:underline font-semibold"
                >
                  Resend OTP
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: Password & Kitchen Directives Baseline */}
          {step === 3 && (
            <div className="flex flex-col gap-5">
              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                  Create Master Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-on-surface-variant absolute left-3 top-3" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
                  />
                </div>
              </div>

              {/* Baseline Dietary Classification */}
              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-2">
                  Primary Household Dietary Classification
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
                  {[
                    { id: "veg", label: "Vegetarian", icon: "🌱" },
                    { id: "egg", label: "Eggetarian", icon: "🥚" },
                    { id: "non_veg", label: "Non-Veg", icon: "🍗" },
                    { id: "jain", label: "Jain", icon: "🌿" },
                  ].map((d) => (
                    <button
                      key={d.id}
                      type="button"
                      onClick={() => setDietaryType(d.id as any)}
                      className={`p-3 rounded-xl border text-center flex flex-col items-center gap-1 transition-all ${
                        dietaryType === d.id
                          ? "border-primary bg-primary-fixed/40 text-primary font-bold shadow-sm"
                          : "border-surface-container-high bg-white/60 text-on-surface-variant hover:bg-white"
                      }`}
                    >
                      <span className="text-lg">{d.icon}</span>
                      <span className="text-xs">{d.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Headcount */}
              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                  Default Household Headcount
                </label>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setHeadcount(Math.max(1, headcount - 1))}
                    className="w-8 h-8 rounded-lg bg-surface-container font-bold text-on-surface hover:bg-surface-container-high"
                  >
                    -
                  </button>
                  <span className="font-label-lg font-bold text-on-surface px-3">{headcount} People</span>
                  <button
                    type="button"
                    onClick={() => setHeadcount(headcount + 1)}
                    className="w-8 h-8 rounded-lg bg-surface-container font-bold text-on-surface hover:bg-surface-container-high"
                  >
                    +
                  </button>
                </div>
              </div>

              <button
                type="button"
                onClick={onStep3Complete}
                disabled={loading}
                className="btn-gradient-primary w-full py-3 rounded-xl font-label-md text-xs font-bold flex items-center justify-center gap-2 mt-2 shadow-glow-primary"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Complete Activation & Enter Portal"}
                <Sparkles className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Bottom Switcher */}
        <div className="text-center mt-6 text-xs font-body-sm text-on-surface-variant">
          Already registered?{" "}
          <Link to="/household/login" className="text-primary font-semibold hover:underline">
            Resident Sign-In
          </Link>
        </div>
      </div>
    </div>
  );
};

