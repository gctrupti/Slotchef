import React, { useState } from "react";
import { toast } from "sonner";
import { householdsApi } from "@/api/households";
import { extractErrorMessage } from "@/api/client";
import {
  Sparkles,
  ShieldCheck,
  Flame,
  AlertTriangle,
  Users,
  Check,
  Save,
  Loader2,
} from "lucide-react";

export const DietaryVault: React.FC = () => {
  const [dietaryType, setDietaryType] = useState<string>("veg");
  const [spiceLevel, setSpiceLevel] = useState<number>(2); // 1=Mild, 2=Medium, 3=Fiery
  const [oilLevel, setOilLevel] = useState<number>(1);   // 1=Minimal, 2=Standard, 3=Rich
  const [saltLevel, setSaltLevel] = useState<number>(2);  // 1=Low, 2=Standard, 3=Robust
  const [garlicOnion, setGarlicOnion] = useState<boolean>(true);
  const [headcount, setHeadcount] = useState<number>(4);
  const [allergens, setAllergens] = useState<string[]>(["Peanuts"]);
  const [loading, setLoading] = useState<boolean>(false);

  const allergenList = [
    "Peanuts",
    "Tree Nuts",
    "Dairy / Lactose",
    "Gluten / Wheat",
    "Mustard Seeds",
    "Sesame Seeds",
    "Soy",
    "Shellfish",
  ];

  const toggleAllergen = (item: string) => {
    if (allergens.includes(item)) {
      setAllergens(allergens.filter((a) => a !== item));
    } else {
      setAllergens([...allergens, item]);
    }
  };

  const handleSaveVault = async () => {
    try {
      setLoading(true);
      await householdsApi.updateDietaryVault({
        dietary_type: dietaryType,
        spice_level: spiceLevel,
        oil_level: oilLevel,
        salt_level: saltLevel,
        garlic_onion: garlicOnion,
        headcount,
        allergens,
      });

      toast.success("Kitchen Directives & Dietary Vault securely updated!");
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Permanent Household Directives
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• Applied to All Assigned Cooks</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Kitchen Directives & Dietary Vault
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Configure your family's exact seasoning preferences, oil calibration, and medical allergen restrictions. Assigned cooks receive this protocol automatically.
          </p>
        </div>

        <button
          onClick={handleSaveVault}
          disabled={loading}
          className="btn-gradient-primary px-5 py-2.5 rounded-xl font-label-md text-xs font-bold flex items-center gap-2 shadow-glow-primary"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          <span>Save Kitchen Directives</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 Cols): Classification & Seasoning Matrix */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Section 1: Primary Dietary Classification */}
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <h2 className="font-headline-sm text-base font-bold text-on-surface">
                1. Primary Dietary Classification
              </h2>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-1">
              {[
                { id: "veg", label: "Vegetarian", icon: "🌱" },
                { id: "egg", label: "Eggetarian", icon: "🥚" },
                { id: "non_veg", label: "Non-Veg", icon: "🍗" },
                { id: "jain", label: "Jain", icon: "🌿" },
                { id: "vegan", label: "Vegan", icon: "🥑" },
              ].map((d) => {
                const isSelected = dietaryType === d.id;
                return (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => setDietaryType(d.id)}
                    className={`p-3.5 rounded-xl border text-center flex flex-col items-center gap-1.5 transition-all ${
                      isSelected
                        ? "border-primary bg-primary-fixed/40 text-primary font-bold shadow-xs ring-1 ring-primary"
                        : "border-surface-container-high bg-white/70 text-on-surface-variant hover:bg-white"
                    }`}
                  >
                    <span className="text-xl">{d.icon}</span>
                    <span className="text-xs font-label-md">{d.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Section 2: Spice, Oil & Seasoning Matrix */}
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-5">
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-primary" />
              <h2 className="font-headline-sm text-base font-bold text-on-surface">
                2. Spice, Oil & Seasoning Matrix
              </h2>
            </div>

            {/* Spice Slider */}
            <div>
              <div className="flex justify-between text-xs font-label-md font-semibold text-on-surface mb-2">
                <span>Chili & Heat Calibration:</span>
                <span className="text-primary font-bold">
                  {spiceLevel === 1 ? "Mild (Child-Friendly)" : spiceLevel === 2 ? "Medium Spiced (Balanced)" : "Fiery (Authentic Regional)"}
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={3}
                value={spiceLevel}
                onChange={(e) => setSpiceLevel(Number(e.target.value))}
                className="w-full accent-primary cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-on-surface-variant mt-1">
                <span>1 - Mild</span>
                <span>2 - Medium</span>
                <span>3 - Fiery</span>
              </div>
            </div>

            {/* Cooking Oil Slider */}
            <div>
              <div className="flex justify-between text-xs font-label-md font-semibold text-on-surface mb-2">
                <span>Cooking Oil & Ghee Volume:</span>
                <span className="text-primary font-bold">
                  {oilLevel === 1 ? "Minimal / Low-Calorie" : oilLevel === 2 ? "Standard Indian Tempering" : "Generous / Restaurant Texture"}
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={3}
                value={oilLevel}
                onChange={(e) => setOilLevel(Number(e.target.value))}
                className="w-full accent-primary cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-on-surface-variant mt-1">
                <span>Low Oil</span>
                <span>Standard</span>
                <span>Generous</span>
              </div>
            </div>

            {/* Garlic & Onion Toggle */}
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-surface-container-low border border-surface-container mt-1">
              <div>
                <span className="font-label-md text-xs font-bold text-on-surface block">
                  Garlic & Onion Tempering Allowed
                </span>
                <span className="font-body-sm text-[11px] text-on-surface-variant">
                  Toggle off for Satvik or Jain preparation standards
                </span>
              </div>
              <button
                type="button"
                onClick={() => setGarlicOnion(!garlicOnion)}
                className={`w-11 h-6 rounded-full transition-colors relative ${
                  garlicOnion ? "bg-primary" : "bg-surface-container-high"
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full bg-white absolute top-1 transition-transform ${
                    garlicOnion ? "left-6" : "left-1"
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Allergen Vault & Headcount */}
        <div className="flex flex-col gap-6">
          {/* Allergen Vault */}
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <h3 className="font-headline-sm text-base font-bold text-on-surface">
                Allergen & Restriction Vault
              </h3>
            </div>
            <p className="font-body-sm text-xs text-on-surface-variant">
              Cooks are strictly audited to avoid cross-contamination for checked allergens:
            </p>

            <div className="flex flex-col gap-2 pt-1">
              {allergenList.map((allergen) => {
                const isRestricted = allergens.includes(allergen);
                return (
                  <button
                    key={allergen}
                    type="button"
                    onClick={() => toggleAllergen(allergen)}
                    className={`p-2.5 rounded-xl border text-left flex items-center justify-between text-xs transition-all ${
                      isRestricted
                        ? "bg-amber-50 border-amber-300 text-amber-900 font-bold"
                        : "bg-white/70 border-surface-container-high text-on-surface hover:bg-white"
                    }`}
                  >
                    <span>{allergen}</span>
                    {isRestricted ? (
                      <span className="px-1.5 py-0.5 rounded bg-amber-200 text-amber-800 text-[10px] uppercase font-bold">
                        RESTRICTED
                      </span>
                    ) : (
                      <span className="text-[10px] text-on-surface-variant font-medium">Safe</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Default Headcount Card */}
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-primary" />
              <h3 className="font-headline-sm text-base font-bold text-on-surface">
                Standard Household Headcount
              </h3>
            </div>
            <p className="text-xs text-on-surface-variant font-body-sm">
              Default portions prepared unless customized on slot booking:
            </p>

            <div className="flex items-center justify-between p-3 rounded-xl bg-surface-container-low border border-surface-container mt-1">
              <button
                type="button"
                onClick={() => setHeadcount(Math.max(1, headcount - 1))}
                className="w-9 h-9 rounded-lg bg-surface-container font-bold text-on-surface hover:bg-surface-container-high"
              >
                -
              </button>
              <span className="font-label-lg font-extrabold text-lg text-primary">{headcount} Family Members</span>
              <button
                type="button"
                onClick={() => setHeadcount(headcount + 1)}
                className="w-9 h-9 rounded-lg bg-surface-container font-bold text-on-surface hover:bg-surface-container-high"
              >
                +
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

