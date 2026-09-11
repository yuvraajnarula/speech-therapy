import React from "react";
import { useTherapyStore, therapyStore } from "../store/therapyStore";
import { Badge } from "./ui/Badge";
import { Tabs, TabItem } from "./ui/Tabs";

export const RoleNavbar: React.FC = () => {
  const userRole = useTherapyStore((s) => s.userRole);
  const sourceLanguage = useTherapyStore((s) => s.sourceLanguage);
  const highContrastMode = useTherapyStore((s) => s.highContrastMode);
  const activeTab = useTherapyStore((s) => s.activeTab);
  const trialLogs = useTherapyStore((s) => s.trialLogs);

  const navTabs: TabItem[] = [
    { id: "trial", label: "Active Speech Trial", icon: "🎙️" },
    { id: "wordbank", label: "Word Bank Explorer", icon: "📖", badge: "20+" },
    { id: "history", label: "SOAP Trial Logs", icon: "📋", badge: trialLogs.length ? String(trialLogs.length) : undefined },
  ];

  return (
    <header
      role="banner"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.75rem",
        padding: "1rem 1.5rem",
        backgroundColor: highContrastMode ? "#000000" : "#ffffff",
        color: highContrastMode ? "#ffffff" : "#0f172a",
        borderBottom: "1px solid #e2e8f0",
        borderRadius: "0 0 10px 10px",
        marginBottom: "1.25rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
      }}
    >
      {/* Top Bar: Brand, HIPAA Badge, Dialect & Mode Selector */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        {/* Brand & Compliance */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              backgroundColor: "#0f172a",
              color: "#ffffff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1rem",
              fontWeight: 800,
            }}
          >
            SLP
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, letterSpacing: "-0.02em" }}>
              IndicAST <span style={{ color: "#2563eb" }}>Clinical Studio</span>
            </h1>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "0.7rem", color: "#64748b" }}>
                AIISH Clinical Articulation Framework
              </span>
              <Badge variant="success">HIPAA / GDPR Ready</Badge>
            </div>
          </div>
        </div>

        {/* Right Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          {/* Dialect Selector */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <label htmlFor="dialect-select" style={{ fontSize: "0.8rem", fontWeight: 500, color: "#64748b" }}>
              Target Dialect:
            </label>
            <select
              id="dialect-select"
              value={sourceLanguage}
              onChange={(e) => therapyStore.setSourceLanguage(e.target.value as any)}
              style={{
                padding: "0.35rem 0.65rem",
                borderRadius: "6px",
                backgroundColor: "#f8fafc",
                color: "#0f172a",
                border: "1px solid #cbd5e1",
                fontSize: "0.8rem",
                fontWeight: 500,
              }}
            >
              <option value="hi">Hindi (हिंदी)</option>
              <option value="kn">Kannada (ಕನ್ನಡ)</option>
              <option value="ta">Tamil (தமிழ்)</option>
              <option value="te">Telugu (తెలుగు)</option>
              <option value="en-IN">Indian English (en-IN)</option>
            </select>
          </div>

          {/* Role Switcher */}
          <div
            role="group"
            aria-label="User role selector"
            style={{
              display: "inline-flex",
              backgroundColor: "#f1f5f9",
              borderRadius: "6px",
              padding: "2px",
              border: "1px solid #e2e8f0",
            }}
          >
            <button
              type="button"
              onClick={() => therapyStore.setUserRole("patient")}
              style={{
                padding: "0.3rem 0.75rem",
                borderRadius: "4px",
                border: "none",
                cursor: "pointer",
                fontSize: "0.8rem",
                fontWeight: userRole === "patient" ? 600 : 500,
                backgroundColor: userRole === "patient" ? "#ffffff" : "transparent",
                color: userRole === "patient" ? "#0f172a" : "#64748b",
                boxShadow: userRole === "patient" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
              }}
            >
              Patient Mode
            </button>
            <button
              type="button"
              onClick={() => therapyStore.setUserRole("therapist")}
              style={{
                padding: "0.3rem 0.75rem",
                borderRadius: "4px",
                border: "none",
                cursor: "pointer",
                fontSize: "0.8rem",
                fontWeight: userRole === "therapist" ? 600 : 500,
                backgroundColor: userRole === "therapist" ? "#ffffff" : "transparent",
                color: userRole === "therapist" ? "#0f172a" : "#64748b",
                boxShadow: userRole === "therapist" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
              }}
            >
              Therapist HUD
            </button>
          </div>

          {/* High Contrast */}
          <button
            type="button"
            onClick={() => therapyStore.toggleHighContrast()}
            aria-pressed={highContrastMode}
            style={{
              padding: "0.35rem 0.65rem",
              borderRadius: "6px",
              border: "1px solid #cbd5e1",
              backgroundColor: highContrastMode ? "#0f172a" : "#ffffff",
              color: highContrastMode ? "#ffffff" : "#475569",
              fontSize: "0.8rem",
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            {highContrastMode ? "Normal A11y" : "High Contrast"}
          </button>
        </div>
      </div>

      {/* Navigation Tabs Bar */}
      <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "0.5rem" }}>
        <Tabs
          items={navTabs}
          activeId={activeTab}
          onChange={(id) => therapyStore.setActiveTab(id as any)}
        />
      </div>
    </header>
  );
};
