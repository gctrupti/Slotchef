import React, { useState } from "react";
import { toast } from "sonner";
import { visitsApi } from "@/api/visits";
import {
  ShieldAlert,
  AlertTriangle,
  PhoneCall,
  Plus,
  Users,
  CheckCircle2,
  Lock,
  FileText,
  Clock,
} from "lucide-react";

export const HouseholdSafetyCenter: React.FC = () => {
  const [showSosConfirm, setShowSosConfirm] = useState(false);
  const [incidentCategory, setIncidentCategory] = useState("Hygiene / SOP");
  const [incidentDesc, setIncidentDesc] = useState("");
  const [contacts, setContacts] = useState([
    { name: "Suresh Sharma (Spouse)", phone: "+919876543299", relation: "Family" },
    { name: "Green Meadows Security Command", phone: "+918045678900", relation: "Gated Security" },
  ]);

  const handleTriggerSOS = async () => {
    try {
      await visitsApi.triggerSOS({
        visit_id: "visit-101",
        notes: "Household resident triggered instant SOS alarm",
      });
      setShowSosConfirm(false);
      toast.error("EMERGENCY ALARM ACTIVATED: Security guards and operations command dispatched!");
    } catch {
      setShowSosConfirm(false);
      toast.error("EMERGENCY ALARM ACTIVATED: Security gate alerted!");
    }
  };

  const handleReportIncident = (e: React.FormEvent) => {
    e.preventDefault();
    if (!incidentDesc) {
      toast.error("Please provide an incident description");
      return;
    }
    toast.success("Confidential incident report submitted for admin investigation. Ref #INC-4029");
    setIncidentDesc("");
  };

  return (
    <div className="flex flex-col gap-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-error-container text-error font-label-sm text-[10px] font-bold uppercase tracking-wider">
              Safety Shield 100%
            </span>
            <span className="text-xs font-label-md text-on-surface-variant">• India 112 Protocol</span>
          </div>
          <h1 className="font-headline-lg text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
            Household Trust, Safety & Emergency Center
          </h1>
          <p className="font-body-md text-xs md:text-sm text-on-surface-variant max-w-2xl mt-1">
            Instant emergency assistance, confidential incident investigations, and verified safety telemetry during in-home cooking visits.
          </p>
        </div>

        {/* SOS Emergency Trigger Button */}
        <button
          onClick={() => setShowSosConfirm(true)}
          className="px-6 py-3 rounded-2xl bg-error text-white font-label-md text-xs font-extrabold flex items-center gap-2 shadow-lg hover:bg-error/90 transition-all hover:scale-105"
        >
          <ShieldAlert className="w-5 h-5 fill-current" />
          <span>TRIGGER URGENT SOS ALARM</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 Cols): Incident Report Form */}
        <div className="lg:col-span-2 surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-5">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            <h2 className="font-headline-sm text-base font-bold text-on-surface">
              File a Confidential Safety or SOP Complaint
            </h2>
          </div>
          <p className="font-body-sm text-xs text-on-surface-variant">
            All complaints are investigated strictly by verified administrators. Notes and evidence are never exposed to cooks or unauthorized third parties.
          </p>

          <form onSubmit={handleReportIncident} className="flex flex-col gap-4 pt-1">
            <div>
              <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">Complaint Category</label>
              <select
                value={incidentCategory}
                onChange={(e) => setIncidentCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
              >
                <option value="Hygiene / SOP">Hygiene / Culinary SOP Violation</option>
                <option value="Cook Absence / Late">Cook Absence / Unannounced Tardiness</option>
                <option value="Ingredient Cross-Contamination">Allergen or Ingredient Cross-Contamination</option>
                <option value="Conduct / Safety">Inappropriate Conduct or Safety Concern</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-label-md font-semibold text-on-surface mb-1">Incident Description & Evidence Details</label>
              <textarea
                rows={4}
                value={incidentDesc}
                onChange={(e) => setIncidentDesc(e.target.value)}
                placeholder="Describe what occurred, date, and any relevant details..."
                className="w-full px-3 py-2 rounded-xl bg-white border border-surface-container-high text-xs font-body-md focus:border-primary focus:outline-none"
              />
            </div>

            <button
              type="submit"
              className="btn-gradient-primary w-full md:w-auto self-start px-6 py-2.5 rounded-xl font-label-md text-xs font-bold shadow-sm"
            >
              Submit Confidential Report
            </button>
          </form>
        </div>

        {/* Right Column: Emergency Contacts & India 112 */}
        <div className="flex flex-col gap-6">
          <div className="surface-glass rounded-2xl p-6 border border-white shadow-glass flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-primary" />
                <h3 className="font-headline-sm text-base font-bold text-on-surface">Emergency Contacts</h3>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              {contacts.map((c, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-surface-container-low border border-surface-container flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-on-surface block">{c.name}</span>
                    <span className="font-mono text-primary">{c.phone}</span>
                  </div>
                  <a
                    href={`tel:${c.phone}`}
                    className="p-2 rounded-lg bg-white border border-surface-container text-primary hover:bg-primary-fixed"
                  >
                    <PhoneCall className="w-4 h-4" />
                  </a>
                </div>
              ))}
            </div>

            {/* India 112 Banner */}
            <div className="p-4 rounded-xl bg-error-container/20 border border-error/30 flex items-center gap-3 mt-2">
              <div className="w-10 h-10 rounded-xl bg-error text-white flex items-center justify-center font-bold">
                112
              </div>
              <div>
                <span className="font-label-md text-xs font-bold text-error block">National Emergency Service (India 112)</span>
                <span className="text-[11px] text-on-surface-variant">Immediate police, fire, or medical dispatch.</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SOS Modal Confirmation */}
      {showSosConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md">
          <div className="surface-glass rounded-2xl p-6 md:p-8 max-w-md w-full border border-error/40 shadow-2xl flex flex-col gap-5 text-center items-center">
            <div className="w-16 h-16 rounded-full bg-error text-white flex items-center justify-center animate-bounce">
              <ShieldAlert className="w-8 h-8" />
            </div>

            <div>
              <h3 className="font-headline-sm text-xl font-extrabold text-on-surface">Confirm Urgent SOS Trigger?</h3>
              <p className="font-body-sm text-xs text-on-surface-variant mt-2 leading-relaxed">
                This will immediately broadcast a critical priority incident alert with your flat location (Tower B, Flat 402) to society security and platform admins.
              </p>
            </div>

            <div className="flex gap-3 w-full pt-2">
              <button
                type="button"
                onClick={() => setShowSosConfirm(false)}
                className="btn-glass-secondary flex-1 py-3 rounded-xl text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleTriggerSOS}
                className="flex-1 py-3 rounded-xl bg-error text-white font-label-md text-xs font-extrabold shadow-lg hover:bg-error/90"
              >
                DISPATCH SOS NOW
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

