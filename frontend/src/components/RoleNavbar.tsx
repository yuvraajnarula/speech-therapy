import { useTherapyStore, therapyStore, type TherapyState } from "../store/therapyStore";
import { Badge } from "./ui/Badge";
import { Tabs } from "./ui/Tabs";
import type { TabItem } from "./ui/Tabs";

export const RoleNavbar: React.FC = () => {
  const userRole = useTherapyStore((s) => s.userRole);
  const sourceLanguage = useTherapyStore((s) => s.sourceLanguage);
  const highContrastMode = useTherapyStore((s) => s.highContrastMode);
  const activeTab = useTherapyStore((s) => s.activeTab);
  const trialLogs = useTherapyStore((s) => s.trialLogs);

  const navTabs: TabItem[] = [
    { id: "trial", label: "Active Speech Trial", icon: "🎙️" },
    { id: "wordbank", label: "Word Bank Explorer", icon: "📖", badge: "20+" },
    { id: "tutor", label: "Live Tutor", icon: "🎓" },
    { id: "history", label: "SOAP Trial Logs", icon: "📋", badge: trialLogs.length ? String(trialLogs.length) : undefined },
  ];

  return (
    <header
      role="banner"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.85rem",
        padding: "1rem 1.5rem",
        backgroundColor: highContrastMode ? "var(--input-surface)" : "var(--surface-overlay)",
        color: "var(--text-primary)",
        borderBottom: "1px solid var(--border-subdued)",
        borderRadius: "0 0 12px 12px",
        marginBottom: "1.25rem",
        boxShadow: "0 2px 8px rgba(28, 25, 23, 0.08)",
      }}
    >
      {/* Top Bar: Brand, HIPAA Badge, Dialect & Mode Selector */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        {/* Brand & Compliance */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              backgroundColor: "var(--surface-overlay)",
              color: "var(--text-primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.95rem",
              fontWeight: 800,
              border: "1px solid var(--border-strong)",
              letterSpacing: "0.05em",
            }}
          >
            SLP
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, letterSpacing: "-0.01em", color: "var(--text-primary)" }}>
              IndicAST <span style={{ color: "var(--text-secondary)", fontWeight: 400 }}>Clinical Studio</span>
            </h1>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.15rem" }}>
              <span style={{ fontSize: "0.72rem", color: "var(--text-tertiary)" }}>
                AIISH Framework • IndicVoices
              </span>
              <Badge variant="success">HIPAA / GDPR Ready</Badge>
            </div>
          </div>
        </div>

        {/* Right Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem", flexWrap: "wrap" }}>
          {/* Dialect Selector */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
            <label htmlFor="dialect-select" style={{ fontSize: "0.8rem", fontWeight: 500, color: "var(--text-secondary)" }}>
              Dialect:
            </label>
            <select
              id="dialect-select"
              value={sourceLanguage}
              onChange={(e) => therapyStore.setSourceLanguage(e.target.value as TherapyState["sourceLanguage"])}
              style={{
                padding: "0.35rem 0.65rem",
                borderRadius: "6px",
                backgroundColor: "var(--bg-canvas)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-strong)",
                fontSize: "0.8rem",
                fontWeight: 500,
                cursor: "pointer",
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
              backgroundColor: "var(--bg-canvas)",
              borderRadius: "6px",
              padding: "2px",
              border: "1px solid var(--border-subdued)",
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
                backgroundColor: userRole === "patient" ? "var(--surface-overlay)" : "transparent",
                color: userRole === "patient" ? "var(--text-primary)" : "var(--text-tertiary)",
                boxShadow: userRole === "patient" ? "var(--shadow-lift)" : "none",
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
                backgroundColor: userRole === "therapist" ? "var(--surface-overlay)" : "transparent",
                color: userRole === "therapist" ? "var(--text-primary)" : "var(--text-tertiary)",
                boxShadow: userRole === "therapist" ? "var(--shadow-lift)" : "none",
              }}
            >
              Therapist HUD
            </button>
          </div>

          {/* High Contrast Toggle */}
          <button
            type="button"
            onClick={() => therapyStore.toggleHighContrast()}
            aria-pressed={highContrastMode}
            style={{
              padding: "0.35rem 0.65rem",
              borderRadius: "6px",
              border: "1px solid var(--border-strong)",
              backgroundColor: highContrastMode ? "var(--input-surface)" : "var(--bg-canvas)",
              color: highContrastMode ? "var(--text-primary)" : "var(--text-secondary)",
              fontSize: "0.8rem",
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            {highContrastMode ? "Normal Slate" : "High Contrast A11y"}
          </button>
        </div>
      </div>

      {/* Navigation Tabs Bar */}
      <div style={{ borderTop: "1px solid var(--border-subdued)", paddingTop: "0.65rem" }}>
        <Tabs
          items={navTabs}
          activeId={activeTab}
          onChange={(id) => therapyStore.setActiveTab(id as TherapyState["activeTab"])}
        />
      </div>
    </header>
  );
};
