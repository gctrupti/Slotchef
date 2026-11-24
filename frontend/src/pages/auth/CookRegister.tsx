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
  ChefHat,
  Building,
  CheckCircle2,
  Lock,
  Phone,
  Mail,
  User,
  ShieldCheck,
  ArrowRight,
  Loader2,
  Award,
} from "lucide-react";

const cookStep1Schema = z.object({
  first_name: z.string().min(2, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  phone: z.string().min(10, "Valid 10-digit mobile number is required"),
  email: z.string().email("Valid email address is required"),
  society_name: z.string().default("Green Meadows Residency"),
  years_experience: z.string().default("5"),
  verification_channel: z.enum(["sms", "email"]).default("sms"),
});

type CookStep1Data = z.infer<typeof cookStep1Schema>;

export const CookRegister: React.FC = () => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [loading, setLoading] = useState(false);
  const [cookData, setCookData] = useState<Partial<CookStep1Data>>({});
  const [otpCode, setOtpCode] = useState(["", "", "", "", "", ""]);
  const [password, setPassword] = useState("");
  const [specializations, setSpecializations] = useState<string[]>([
    "South Indian",
    "North Indian",
  ]);
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CookStep1Data>({
    resolver: zodResolver(cookStep1Schema),
    defaultValues: {
      society_name: "Green Meadows Residency",
      years_experience: "5",
      verification_channel: "sms",
    },
  });

  const onStep1Submit = async (data: CookStep1Data) => {
    try {
      setLoading(true);
      setCookData(data);
      const formattedPhone = data.phone.startsWith("+91") ? data.phone : `+91${data.phone}`;

      const res = await authApi.register({
        first_name: data.first_name,
        last_name: data.last_name,
        phone: formattedPhone,
        email: data.email,
        password: "TempInitialPassword123!",
        role: "cook",
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

  const onVerifyOTP = async () => {
    const fullOtp = otpCode.join("");
    if (fullOtp.length !== 6) {
      toast.error("Please enter the complete 6-digit OTP");
      return;
    }

    try {
      setLoading(true);
      const target =
        cookData.verification_channel === "sms"
          ? cookData.phone?.startsWith("+91")
            ? cookData.phone
            : `+91${cookData.phone}`
          : cookData.email!;

      const res = await authApi.verifyRegistrationOTP(
        target,
        cookData.verification_channel || "sms",
        fullOtp
      );

      toast.success("Mobile phone verified successfully!");
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

  const onStep3Complete = async () => {
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    toast.success("Cook Partner onboarding profile created!");
    navigate("/cook");
  };

  const toggleSpecialization = (cuisine: string) => {
    if (specializations.includes(cuisine)) {
      setSpecializations(specializations.filter((c) => c !== cuisine));
    } else {
      setSpecializations([...specializations, cuisine]);
    }
  };

  const handleOtpInput = (index: number, val: string) => {
    if (val.length > 1) val = val[val.length - 1];
    const newOtp = [...otpCode];
    newOtp[index] = val;
    setOtpCode(newOtp);

    if (val && index < 5) {
      document.getElementById(`cook-otp-${index + 1}`)?.focus();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#faf8ff] via-[#f0f4f8] to-[#eaedff] flex items-center justify-center p-4 md:p-8 font-sans">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-6">
          <Link to="/" className="inline-flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-xl bg-secondary flex items-center justify-center text-white shadow-sm">
              <ChefHat className="w-4 h-4" />
            </div>
            <span className="font-headline-sm text-xl font-bold tracking-tight text-on-surface">
              Slot<span className="text-secondary">Chef</span>
            </span>
          </Link>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-bold text-on-surface">
            {step === 1 && "Join as Certified Cook Partner"}
            {step === 2 && "Cook Partner Mobile Verification"}
            {step === 3 && "Password & Cooking Specializations"}
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant mt-1">
            {step === 1 && "Zero travel outside society, guaranteed weekly payouts, and ₹2 Lakh insurance."}
            {step === 2 && "Verify your registered mobile number for schedule dispatches."}
            {step === 3 && "Select your culinary specializations and establish security credentials."}
          </p>

          <div className="flex items-center justify-center gap-2 mt-4">
            <div className={`h-1.5 w-12 rounded-full ${step >= 1 ? "bg-secondary" : "bg-surface-container-high"}`} />
            <div className={`h-1.5 w-12 rounded-full ${step >= 2 ? "bg-secondary" : "bg-surface-container-high"}`} />
            <div className={`h-1.5 w-12 rounded-full ${step >= 3 ? "bg-secondary" : "bg-surface-container-high"}`} />
          </div>
        </div>

        {/* Card Shell */}
        <div className="surface-glass rounded-2xl p-6 md:p-8 border border-white shadow-glass-elevated">
          {step === 1 && (
            <form onSubmit={handleSubmit(onStep1Submit)} className="flex flex-col gap-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">First Name</label>
                  <input
                    {...register("first_name")}
                    type="text"
                    placeholder="e.g. Ramesh"
                    className="w-full px-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-secondary focus:outline-none"
                  />
                  {errors.first_name && <p className="text-[11px] text-error mt-0.5">{errors.first_name.message}</p>}
                </div>

                <div>
                  <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">Last Name</label>
                  <input
                    {...register("last_name")}
                    type="text"
                    placeholder="e.g. Kumar"
                    className="w-full px-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-secondary focus:outline-none"
                  />
                  {errors.last_name && <p className="text-[11px] text-error mt-0.5">{errors.last_name.message}</p>}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">Mobile Number (SMS)</label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-on-surface-variant absolute left-3 top-3" />
                    <input
                      {...register("phone")}
                      type="tel"
                      placeholder="9876543210"
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-secondary focus:outline-none"
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
                      placeholder="cook@slotchef.test"
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-secondary focus:outline-none"
                    />
                  </div>
                  {errors.email && <p className="text-[11px] text-error mt-0.5">{errors.email.message}</p>}
                </div>
              </div>

              {/* Society Assignment & Experience */}
              <div className="p-4 rounded-xl bg-surface-container-low border border-surface-container mt-2">
                <div className="flex items-center gap-2 mb-3">
                  <Building className="w-4 h-4 text-secondary" />
                  <span className="font-label-md text-xs font-bold text-on-surface">Assigned Gated Society Network</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-label-sm text-on-surface-variant mb-1">Society Node</label>
                    <input
                      {...register("society_name")}
                      readOnly
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-surface-container-high text-xs font-semibold text-on-surface"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-label-sm text-on-surface-variant mb-1">Cooking Experience</label>
                    <select
                      {...register("years_experience")}
                      className="w-full px-3 py-1.5 rounded-lg bg-white border border-surface-container-high text-xs font-body-md focus:border-secondary focus:outline-none"
                    >
                      <option value="2">2 - 4 Years</option>
                      <option value="5">5 - 8 Years (Experienced)</option>
                      <option value="10">10+ Years (MasterChef Specialist)</option>
                    </select>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-secondary text-white font-label-md text-xs font-bold flex items-center justify-center gap-2 mt-2 shadow-md hover:bg-secondary/90 transition-colors"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Request Partner OTP Verification"}
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {step === 2 && (
            <div className="flex flex-col items-center gap-6 py-4">
              <div className="flex gap-2.5 justify-center">
                {otpCode.map((digit, idx) => (
                  <input
                    key={idx}
                    id={`cook-otp-${idx}`}
                    type="text"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleOtpInput(idx, e.target.value)}
                    className="w-11 h-13 text-center text-xl font-mono font-bold rounded-xl bg-white border border-surface-container-high focus:border-secondary focus:outline-none"
                  />
                ))}
              </div>

              <p className="text-xs font-body-sm text-on-surface-variant text-center max-w-sm">
                Code sent to registered mobile <span className="font-semibold text-on-surface">{cookData.phone}</span>.
              </p>

              <button
                type="button"
                onClick={onVerifyOTP}
                disabled={loading}
                className="w-full py-3 rounded-xl bg-secondary text-white font-label-md text-xs font-bold flex items-center justify-center gap-2 shadow-md hover:bg-secondary/90 transition-colors"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Verify Partner Phone & Proceed"}
                <CheckCircle2 className="w-4 h-4" />
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="flex flex-col gap-5">
              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">
                  Create Partner Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-on-surface-variant absolute left-3 top-3" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/80 border border-surface-container-high text-xs font-body-md focus:border-secondary focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-label-md font-semibold text-on-surface mb-2">
                  Select Certified Cooking Cuisines
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2.5">
                  {[
                    "South Indian",
                    "North Indian",
                    "Italian",
                    "Chinese",
                    "Gujarati",
                    "Continental",
                  ].map((c) => {
                    const selected = specializations.includes(c);
                    return (
                      <button
                        key={c}
                        type="button"
                        onClick={() => toggleSpecialization(c)}
                        className={`p-2.5 rounded-xl border text-xs font-semibold text-center transition-all ${
                          selected
                            ? "bg-secondary-fixed text-on-secondary-fixed border-secondary shadow-sm font-bold"
                            : "bg-white/60 border-surface-container-high text-on-surface-variant hover:bg-white"
                        }`}
                      >
                        {c}
                      </button>
                    );
                  })}
                </div>
              </div>

              <button
                type="button"
                onClick={onStep3Complete}
                disabled={loading}
                className="w-full py-3 rounded-xl bg-secondary text-white font-label-md text-xs font-bold flex items-center justify-center gap-2 mt-2 shadow-md hover:bg-secondary/90 transition-colors"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Complete Partner Setup & View Roster"}
                <Award className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        <div className="text-center mt-6 text-xs font-body-sm text-on-surface-variant">
          Already a Cook Partner?{" "}
          <Link to="/cook/login" className="text-secondary font-semibold hover:underline">
            Partner Sign-In
          </Link>
        </div>
      </div>
    </div>
  );
};

