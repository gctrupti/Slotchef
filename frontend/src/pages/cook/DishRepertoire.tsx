import React, { useState } from "react";
import { toast } from "sonner";
import {
  ChefHat,
  CheckCircle2,
  ShieldCheck,
  Search,
  Check,
  Plus,
  Flame,
  Star,
  Award,
} from "lucide-react";
import { CUISINES, DISH_CATALOG } from "@/pages/household/MealMenu";

export const DishRepertoire: React.FC = () => {
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([
    "South Indian",
    "North Indian",
    "Kerala",
  ]);
  const [certifiedDishes, setCertifiedDishes] = useState<string[]>([
    "Crisp Masala Dosa",
    "Steamed Fluffy Idlis",
    "Paneer Butter Masala",
    "Fresh Wheat Phulkas",
    "Dal Tadka",
    "Appam & Veg Stew",
  ]);
  const [searchQuery, setSearchQuery] = useState("");

  const toggleCuisine = (cuisine: string) => {
    if (cuisine === "All Cuisines") return;
    if (selectedCuisines.includes(cuisine)) {
      setSelectedCuisines(selectedCuisines.filter((c) => c !== cuisine));
    } else {
      setSelectedCuisines([...selectedCuisines, cuisine]);
    }
  };

  const toggleDish = (dishName: string) => {
    if (certifiedDishes.includes(dishName)) {
      setCertifiedDishes(certifiedDishes.filter((d) => d !== dishName));
    } else {
      setCertifiedDishes([...certifiedDishes, dishName]);
    }
  };

  const handleSaveRepertoire = () => {
    toast.success("Culinary Repertoire updated! Your skills are visible to household cook matching.");
  };

  const availableDishes = DISH_CATALOG.filter((d) => {
    const inCuisine = selectedCuisines.includes(d.cuisine);
    const matchesSearch = d.name.toLowerCase().includes(searchQuery.toLowerCase());
    return inCuisine && matchesSearch;
  });

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Skills & Certified Repertoire
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• Verified Profile</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Dish Repertoire & Kitchen Directives
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Specify the exact cuisines and recipes you are certified to prepare. Households matching these dishes in Green Meadows will discover your profile.
          </p>
        </div>

        {/* Re-Cert Card */}
        <div className="surface-glass p-4 rounded-2xl border border-white shadow-sm flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center text-white shrink-0">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-label-sm uppercase font-bold text-secondary">Culinary Audit Standing</span>
            <h4 className="font-label-md text-xs font-bold text-on-surface">MasterChef Inspector Certified</h4>
            <span className="text-[10px] text-tertiary font-semibold">Valid till Dec 2026</span>
          </div>
        </div>
      </div>

      {/* Cuisines Selection */}
      <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="font-headline-sm text-base font-bold text-on-surface">
            1. Which Cuisines Can You Confidently Prepare?
          </h2>
          <span className="text-xs font-mono font-bold text-secondary">
            {selectedCuisines.length} Cuisines Selected
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2.5">
          {CUISINES.filter((c) => c !== "All Cuisines").map((c) => {
            const isSelected = selectedCuisines.includes(c);
            return (
              <button
                key={c}
                type="button"
                onClick={() => toggleCuisine(c)}
                className={`p-3 rounded-xl border text-xs font-semibold text-center transition-all ${
                  isSelected
                    ? "bg-secondary text-white border-secondary shadow-xs font-bold"
                    : "bg-white/70 border-surface-container-high text-on-surface-variant hover:bg-white"
                }`}
              >
                {c}
              </button>
            );
          })}
        </div>
      </div>

      {/* Specific Dishes Selection */}
      <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="font-headline-sm text-base font-bold text-on-surface">
              2. Individual Certified Dishes ({certifiedDishes.length} Selected)
            </h2>
            <p className="font-body-sm text-xs text-on-surface-variant mt-0.5">
              Select all individual recipes you have mastered:
            </p>
          </div>

          <div className="relative w-full md:w-64">
            <Search className="w-4 h-4 text-on-surface-variant absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter dishes..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-white border border-surface-container-high text-xs font-body-md focus:border-secondary focus:outline-none"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {availableDishes.map((dish) => {
            const isCertified = certifiedDishes.includes(dish.name);
            return (
              <div
                key={dish.id}
                onClick={() => toggleDish(dish.name)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all flex items-center justify-between gap-3 ${
                  isCertified
                    ? "bg-white border-secondary ring-1 ring-secondary/30 shadow-xs"
                    : "bg-white/60 border-surface-container-high hover:bg-white"
                }`}
              >
                <div>
                  <h4 className="font-label-md text-xs font-bold text-on-surface">{dish.name}</h4>
                  <span className="text-[10px] text-on-surface-variant">{dish.cuisine}</span>
                </div>

                <div
                  className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 ${
                    isCertified
                      ? "bg-secondary text-white border-secondary"
                      : "border-surface-container-high bg-white"
                  }`}
                >
                  {isCertified && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex justify-end pt-4 border-t border-surface-container-high">
          <button
            onClick={handleSaveRepertoire}
            className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-secondary text-white font-label-md text-xs font-bold flex items-center justify-center gap-2 shadow-md hover:bg-secondary/90 transition-colors"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Save Certified Repertoire</span>
          </button>
        </div>
      </div>
    </div>
  );
};

