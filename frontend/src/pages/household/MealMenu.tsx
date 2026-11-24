import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Utensils,
  Search,
  Check,
  ChefHat,
  Filter,
  Calendar,
  Clock,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Star,
} from "lucide-react";

export interface DishItem {
  id: string;
  name: string;
  cuisine: string;
  mealType: ("breakfast" | "lunch" | "dinner" | "snacks")[];
  dietary: "veg" | "non_veg" | "jain" | "vegan";
  prepTimeMinutes: number;
  description: string;
}

export interface MatchedCook {
  id: string;
  name: string;
  rating: number;
  reviewsCount: number;
  experienceYears: number;
  cuisines: string[];
  dishes: string[];
  society: string;
  photoUrl: string;
  isAvailableToday: boolean;
}

// 16 Approved Cuisines & Rich Discovered Dishes
export const CUISINES = [
  "All Cuisines",
  "South Indian",
  "North Indian",
  "Italian",
  "Chinese",
  "Continental",
  "Mexican",
  "Mediterranean",
  "Bengali",
  "Maharashtrian",
  "Gujarati",
  "Punjabi",
  "Kerala",
  "Andhra",
  "Karnataka",
  "Thai",
  "Japanese",
];

export const DISH_CATALOG: DishItem[] = [
  // South Indian
  { id: "si-1", name: "Crisp Masala Dosa", cuisine: "South Indian", mealType: ["breakfast", "dinner"], dietary: "veg", prepTimeMinutes: 30, description: "Golden rice crepe stuffed with spiced potato masala and coconut chutney" },
  { id: "si-2", name: "Steamed Fluffy Idlis", cuisine: "South Indian", mealType: ["breakfast", "dinner"], dietary: "veg", prepTimeMinutes: 25, description: "Fermented rice and lentil cakes served with drumstick sambar" },
  { id: "si-3", name: "Medu Vada", cuisine: "South Indian", mealType: ["breakfast", "snacks"], dietary: "veg", prepTimeMinutes: 30, description: "Crispy lentil donuts tempered with peppercorns and curry leaves" },
  { id: "si-4", name: "Ven Pongal", cuisine: "South Indian", mealType: ["breakfast"], dietary: "veg", prepTimeMinutes: 30, description: "Ghee-tempered rice and moong dal porridge with black pepper and cashews" },
  { id: "si-5", name: "Bisi Bele Bath", cuisine: "South Indian", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 45, description: "Traditional spicy Karnataka rice and lentil pot dish with seasonal vegetables" },
  { id: "si-6", name: "Lemon Rice & Papad", cuisine: "South Indian", mealType: ["lunch"], dietary: "veg", prepTimeMinutes: 25, description: "Tangy turmeric-infused rice with roasted peanuts and mustard tempering" },
  { id: "si-7", name: "Tomato Rasam", cuisine: "South Indian", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 20, description: "Spicy and tangy herbal tomato broth with cumin and garlic" },

  // North Indian
  { id: "ni-1", name: "Paneer Butter Masala", cuisine: "North Indian", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 35, description: "Cottage cheese cubes simmered in rich creamy tomato and butter gravy" },
  { id: "ni-2", name: "Fresh Wheat Phulkas", cuisine: "North Indian", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 25, description: "Soft, puffed whole-wheat flatbreads brushed with organic ghee" },
  { id: "ni-3", name: "Dal Tadka", cuisine: "North Indian", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 25, description: "Yellow arhar lentils tempered with garlic, cumin, and dried red chilies" },
  { id: "ni-4", name: "Palak Paneer", cuisine: "North Indian", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 35, description: "Nutritious spinach puree spiced with garam masala and tender paneer" },
  { id: "ni-5", name: "Pindi Chole", cuisine: "North Indian", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 45, description: "Slow-cooked chickpeas spiced with pomegranate seeds and dry roasted spices" },
  { id: "ni-6", name: "Aloo Paratha with Curd", cuisine: "North Indian", mealType: ["breakfast", "lunch"], dietary: "veg", prepTimeMinutes: 30, description: "Flaky griddled flatbread stuffed with spiced mashed potatoes" },
  { id: "ni-7", name: "Rajma Masala", cuisine: "North Indian", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 45, description: "Red kidney beans cooked in aromatic onion-tomato masala" },

  // Italian
  { id: "it-1", name: "Penne Pomodoro & Basil", cuisine: "Italian", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 30, description: "Al dente penne in fresh San Marzano tomato sauce and torn basil" },
  { id: "it-2", name: "Artisanal Herb Focaccia", cuisine: "Italian", mealType: ["snacks", "dinner"], dietary: "vegan", prepTimeMinutes: 40, description: "Olive oil rich leavened bread topped with rosemary and sea salt" },
  { id: "it-3", name: "Vegetable Lasagna", cuisine: "Italian", mealType: ["dinner"], dietary: "veg", prepTimeMinutes: 50, description: "Layered pasta sheets with ricotta, marinara, and garden zucchini" },
  { id: "it-4", name: "Mushroom Risotto", cuisine: "Italian", mealType: ["dinner"], dietary: "veg", prepTimeMinutes: 40, description: "Creamy Arborio rice slow-cooked with wild mushrooms and parmesan" },
  { id: "it-5", name: "Garlic Herb Bread", cuisine: "Italian", mealType: ["snacks", "dinner"], dietary: "veg", prepTimeMinutes: 20, description: "Crisp toasted baguette with garlic-herb compound butter" },

  // Chinese
  { id: "ch-1", name: "Veg Hakka Noodles", cuisine: "Chinese", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 25, description: "Wok-tossed noodles with shredded cabbage, bell peppers, and scallions" },
  { id: "ch-2", name: "Schezwan Fried Rice", cuisine: "Chinese", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 25, description: "Aromatic basmati tossed in spicy house Schezwan chili paste" },
  { id: "ch-3", name: "Vegetable Manchurian", cuisine: "Chinese", mealType: ["lunch", "dinner"], dietary: "veg", prepTimeMinutes: 35, description: "Crispy vegetable dumplings coated in savory soy-garlic sauce" },
  { id: "ch-4", name: "Crispy Spring Rolls", cuisine: "Chinese", mealType: ["snacks"], dietary: "veg", prepTimeMinutes: 30, description: "Golden fried wrappers stuffed with spiced julienned vegetables" },

  // Kerala
  { id: "kl-1", name: "Appam & Veg Stew", cuisine: "Kerala", mealType: ["breakfast", "dinner"], dietary: "veg", prepTimeMinutes: 35, description: "Lacy fermented rice hoppers served with coconut milk vegetable stew" },
  { id: "kl-2", name: "Puttu & Kadala Curry", cuisine: "Kerala", mealType: ["breakfast"], dietary: "veg", prepTimeMinutes: 35, description: "Steamed rice cake cylinders layered with grated coconut and black chickpeas" },

  // Punjabi
  { id: "pj-1", name: "Amritsari Kulcha", cuisine: "Punjabi", mealType: ["breakfast", "lunch"], dietary: "veg", prepTimeMinutes: 35, description: "Tandoor style crisp layered bread stuffed with spiced potatoes and onions" },
  { id: "pj-2", name: "Sarson Ka Saag & Makki Roti", cuisine: "Punjabi", mealType: ["dinner"], dietary: "veg", prepTimeMinutes: 50, description: "Traditional mustard greens mash served with griddled yellow corn flatbread" },

  // Gujarati
  { id: "gj-1", name: "Gujarati Kadhi & Khichdi", cuisine: "Gujarati", mealType: ["dinner"], dietary: "veg", prepTimeMinutes: 30, description: "Sweet and tangy yogurt soup paired with moong dal and rice porridge" },
  { id: "gj-2", name: "Khaman Dhokla", cuisine: "Gujarati", mealType: ["breakfast", "snacks"], dietary: "veg", prepTimeMinutes: 25, description: "Steamed fluffy gram flour cakes tempered with mustard and green chilies" },
];

export const DEMO_COOKS: MatchedCook[] = [
  {
    id: "cook-101",
    name: "Chef Meenakshi Iyer",
    rating: 4.9,
    reviewsCount: 142,
    experienceYears: 8,
    cuisines: ["South Indian", "North Indian", "Kerala"],
    dishes: ["Crisp Masala Dosa", "Steamed Fluffy Idlis", "Paneer Butter Masala", "Fresh Wheat Phulkas", "Tomato Rasam", "Appam & Veg Stew"],
    society: "Green Meadows Residency",
    photoUrl: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80",
    isAvailableToday: true,
  },
  {
    id: "cook-102",
    name: "Chef Anand Deshmukh",
    rating: 4.8,
    reviewsCount: 98,
    experienceYears: 6,
    cuisines: ["North Indian", "Punjabi", "Italian", "Chinese"],
    dishes: ["Paneer Butter Masala", "Fresh Wheat Phulkas", "Dal Tadka", "Penne Pomodoro & Basil", "Veg Hakka Noodles", "Pindi Chole"],
    society: "Green Meadows Residency",
    photoUrl: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
    isAvailableToday: true,
  },
  {
    id: "cook-103",
    name: "Chef Kavya Sharma",
    rating: 4.95,
    reviewsCount: 167,
    experienceYears: 10,
    cuisines: ["Italian", "Continental", "North Indian", "Chinese"],
    dishes: ["Penne Pomodoro & Basil", "Vegetable Lasagna", "Mushroom Risotto", "Garlic Herb Bread", "Schezwan Fried Rice", "Paneer Butter Masala"],
    society: "Green Meadows Residency",
    photoUrl: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
    isAvailableToday: true,
  },
];

export const MealMenu: React.FC = () => {
  const [selectedCuisine, setSelectedCuisine] = useState("All Cuisines");
  const [selectedMealType, setSelectedMealType] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDishes, setSelectedDishes] = useState<string[]>([
    "Crisp Masala Dosa",
    "Paneer Butter Masala",
  ]);
  const navigate = useNavigate();

  // Filter Dishes
  const filteredDishes = DISH_CATALOG.filter((d) => {
    const matchesCuisine = selectedCuisine === "All Cuisines" || d.cuisine === selectedCuisine;
    const matchesMeal = selectedMealType === "all" || d.mealType.includes(selectedMealType as any);
    const matchesSearch =
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.cuisine.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCuisine && matchesMeal && matchesSearch;
  });

  const toggleDishSelection = (dishName: string) => {
    if (selectedDishes.includes(dishName)) {
      setSelectedDishes(selectedDishes.filter((d) => d !== dishName));
    } else {
      setSelectedDishes([...selectedDishes, dishName]);
    }
  };

  // Find Cooks matching ALL selected dishes
  const matchingCooks = DEMO_COOKS.filter((cook) => {
    if (selectedDishes.length === 0) return true;
    return selectedDishes.every((selectedDish) => cook.dishes.includes(selectedDish));
  });

  const handleBookWithDishes = () => {
    navigate("/household/booking", { state: { preselectedDishes: selectedDishes } });
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-label-sm text-[10px] font-bold uppercase tracking-wider">
              16 Regional & Global Cuisines
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• Verified Recipe Catalog</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Curated Meal Menu & Chef Discovery
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Pick the exact dishes your family desires. Our constraint engine matches cooks whose verified competencies cover all chosen dishes.
          </p>
        </div>

        {/* Selected Dishes Floating Action Banner */}
        {selectedDishes.length > 0 && (
          <div className="p-3.5 rounded-2xl bg-white border border-primary/30 shadow-glass-elevated flex items-center gap-4">
            <div>
              <span className="text-[10px] font-label-sm uppercase tracking-wider text-primary font-bold">
                Selected for Next Meal
              </span>
              <p className="font-label-md text-xs font-bold text-on-surface">
                {selectedDishes.length} Dish{selectedDishes.length > 1 ? "es" : ""} Selected
              </p>
            </div>
            <button
              onClick={handleBookWithDishes}
              className="btn-gradient-primary px-4 py-2 rounded-xl font-label-md text-xs font-bold flex items-center gap-1.5 shadow-sm"
            >
              <span>Book Cooking Slot</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Search and Filters */}
      <div className="surface-glass rounded-2xl p-4 border border-white shadow-glass flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-on-surface-variant absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search dishes (e.g. Masala Dosa, Paneer)..."
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/90 border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
          />
        </div>

        {/* Meal Type Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {[
            { id: "all", label: "All Meals" },
            { id: "breakfast", label: "Breakfast" },
            { id: "lunch", label: "Lunch" },
            { id: "dinner", label: "Dinner" },
            { id: "snacks", label: "Snacks" },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setSelectedMealType(m.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-label-md font-semibold whitespace-nowrap transition-all ${
                selectedMealType === m.id
                  ? "bg-primary text-white shadow-xs font-bold"
                  : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Horizontal Cuisine Scrolling Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {CUISINES.map((cuisine) => (
          <button
            key={cuisine}
            onClick={() => setSelectedCuisine(cuisine)}
            className={`px-4 py-2 rounded-xl font-label-md text-xs font-semibold whitespace-nowrap transition-all ${
              selectedCuisine === cuisine
                ? "bg-primary-container text-white shadow-sm font-bold"
                : "surface-glass text-on-surface-variant hover:bg-white hover:text-on-surface"
            }`}
          >
            {cuisine}
          </button>
        ))}
      </div>

      {/* 2-Column Layout: Left Dish Grid / Right Matching Cook Fleet */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Dishes Column (2 Cols) */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-xs text-on-surface-variant uppercase font-bold tracking-wider">
              Available Dishes ({filteredDishes.length})
            </span>
            <span className="text-[11px] font-body-sm text-on-surface-variant">
              Click to select dishes for your cook matching
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredDishes.map((dish) => {
              const isSelected = selectedDishes.includes(dish.name);
              return (
                <div
                  key={dish.id}
                  onClick={() => toggleDishSelection(dish.name)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all flex flex-col justify-between ${
                    isSelected
                      ? "bg-white border-primary-container shadow-glass-elevated ring-1 ring-primary-container"
                      : "surface-glass border-white/80 hover:bg-white hover:shadow-glass"
                  }`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-3.5 h-3.5 rounded border border-emerald-600 flex items-center justify-center p-0.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                        </span>
                        <h3 className="font-headline-sm text-sm font-bold text-on-surface">
                          {dish.name}
                        </h3>
                      </div>

                      <div
                        className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                          isSelected
                            ? "bg-primary text-white border-primary"
                            : "border-surface-container-high bg-white/50"
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                    </div>

                    <p className="font-body-sm text-xs text-on-surface-variant line-clamp-2 mb-3">
                      {dish.description}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-surface-container-high/60 text-[11px]">
                    <span className="px-2 py-0.5 rounded-md bg-surface-container text-on-surface-variant font-semibold">
                      {dish.cuisine}
                    </span>
                    <span className="text-on-surface-variant font-mono font-medium">
                      ⏱ {dish.prepTimeMinutes} min
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Recommended Cooks Matching Selection */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-xs text-on-surface-variant uppercase font-bold tracking-wider">
              Matching Verified Cooks ({matchingCooks.length})
            </span>
          </div>

          <div className="flex flex-col gap-4">
            {matchingCooks.length > 0 ? (
              matchingCooks.map((cook) => (
                <div
                  key={cook.id}
                  className="surface-glass rounded-2xl p-5 border border-white shadow-glass flex flex-col justify-between gap-4"
                >
                  <div className="flex items-start gap-3.5">
                    <img
                      src={cook.photoUrl}
                      alt={cook.name}
                      className="w-13 h-13 rounded-xl object-cover border border-white shadow-sm"
                    />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <h4 className="font-label-lg font-bold text-on-surface text-sm">
                          {cook.name}
                        </h4>
                        <ShieldCheck className="w-3.5 h-3.5 text-primary" />
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-xs text-on-surface-variant">
                        <span className="flex items-center text-amber-500 font-bold">
                          <Star className="w-3.5 h-3.5 fill-current mr-0.5" />
                          {cook.rating}
                        </span>
                        <span>•</span>
                        <span>{cook.experienceYears} yrs exp</span>
                      </div>
                      <p className="text-[11px] text-tertiary font-medium mt-1">
                        ✓ In-Resident Node • 0 walking delay
                      </p>
                    </div>
                  </div>

                  {/* Certified Dishes Tag Matrix */}
                  <div>
                    <span className="block text-[10px] font-label-sm text-on-surface-variant uppercase tracking-wider font-bold mb-1.5">
                      Covers Your Selected Recipes:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedDishes.map((dish) => (
                        <span
                          key={dish}
                          className="px-2 py-0.5 rounded-md bg-primary-fixed/50 text-primary font-label-sm text-[10px] font-bold flex items-center gap-1"
                        >
                          <Check className="w-3 h-3 text-primary" />
                          <span>{dish}</span>
                        </span>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() =>
                      navigate("/household/booking", {
                        state: {
                          preferredCookId: cook.id,
                          preselectedDishes: selectedDishes,
                        },
                      })
                    }
                    className="btn-gradient-primary w-full py-2.5 rounded-xl font-label-md text-xs font-bold text-center flex items-center justify-center gap-2"
                  >
                    <span>Book with Chef {cook.name.split(" ")[1] || cook.name}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <div className="surface-glass rounded-2xl p-6 border border-white text-center flex flex-col items-center gap-3">
                <ChefHat className="w-10 h-10 text-on-surface-variant/40" />
                <h4 className="font-headline-sm text-sm font-bold text-on-surface">
                  No Single Cook Prepares All Selected Dishes
                </h4>
                <p className="font-body-sm text-xs text-on-surface-variant max-w-xs">
                  Try unselecting dishes across vastly disparate culinary traditions (e.g. Italian Lasagna + Kerala Puttu) or book sequential slots.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

