import { useState } from "react";
import { Badge } from "./ui/Badge";
import { therapyStore, useTherapyStore } from "../store/therapyStore";
import type { TrialLogItem } from "../store/therapyStore";

export type CueLevel = "independent" | "verbal" | "visual" | "tactile";

export const ClinicianPromptLogger: React.FC = () => {
  const [selectedCue, setSelectedCue] = useState<CueLevel>("independent");
  const targetWord = useTherapyStore((s) => s.targetWord);
  const trialLogs = useTherapyStore((s) => s.trialLogs);

  const handleLog = (rating: "correct" | "approx" | "incorrect") => {
    const score = rating === "correct" ? 1.0 : rating === "approx" ? 0.5 : 0.0;
    const newLog: TrialLogItem = {
      id: Math.random().toString(36).substring(2, 9),
      targetWord,
      cueLevel: selectedCue,
      rating,
      score,
      timestamp: new Date().toLocaleTimeString(),
    };
    therapyStore.addTrialLog(newLog);
  };

  const totalTrials = trialLogs.length;
  const correctTrials = trialLogs.filter((t) => t.rating === "correct").length;
  const blockAccuracy = totalTrials > 0 ? Math.round((correctTrials / totalTrials) * 100) : 0;

  return (
    <div
      style={{
        borderRadius: "12px",
        border: "1px solid var(--border-subdued)",
        backgroundColor: "var(--surface-overlay)",
        padding: "1.25rem",
        boxShadow: "0 2px 6px rgba(28, 25, 23, 0.10)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid var(--border-subdued)",
          paddingBottom: "0.65rem",
          marginBottom: "0.85rem",
        }}
      >
        <div>
          <h4 style={{ margin: 0, fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>
            Clinician Prompt Hierarchy Logger
          </h4>
          <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
            SOAP Clinical Telemetry & Prompt Recording
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Badge variant={blockAccuracy >= 80 ? "success" : "warning"}>
            Trial Block: {correctTrials}/{totalTrials} ({blockAccuracy}%)
          </Badge>
        </div>
      </div>

      {/* Prompt Hierarchy Selector */}
      <div style={{ marginBottom: "0.85rem" }}>
        <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "0.4rem" }}>
          Prompt Level Provided:
        </span>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.4rem" }}>
          {(["independent", "verbal", "visual", "tactile"] as CueLevel[]).map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => setSelectedCue(level)}
              style={{
                padding: "0.45rem 0.6rem",
                borderRadius: "6px",
                fontSize: "0.75rem",
                fontWeight: selectedCue === level ? 700 : 500,
                textTransform: "capitalize",
                border: selectedCue === level ? "1px solid var(--accent-primary)" : "1px solid var(--border-subdued)",
                backgroundColor: selectedCue === level ? "var(--surface-overlay)" : "var(--bg-canvas)",
                color: selectedCue === level ? "var(--text-primary)" : "var(--text-secondary)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* Trial Rating Buttons */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.5rem" }}>
        <button
          type="button"
          onClick={() => handleLog("correct")}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.3rem",
            padding: "0.6rem 0.5rem",
            borderRadius: "6px",
            border: "1px solid var(--success-border)",
            backgroundColor: "var(--success-bg)",
            color: "var(--success-text)",
            fontSize: "0.8rem",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          <span>✓</span> Correct (1.0)
        </button>

        <button
          type="button"
          onClick={() => handleLog("approx")}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.3rem",
            padding: "0.6rem 0.5rem",
            borderRadius: "6px",
            border: "1px solid var(--warn-border)",
            backgroundColor: "var(--warn-bg)",
            color: "var(--warn-text)",
            fontSize: "0.8rem",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          <span>~</span> Approx (0.5)
        </button>

        <button
          type="button"
          onClick={() => handleLog("incorrect")}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.3rem",
            padding: "0.6rem 0.5rem",
            borderRadius: "6px",
            border: "1px solid var(--danger-border)",
            backgroundColor: "var(--danger-bg)",
            color: "var(--danger-text)",
            fontSize: "0.8rem",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          <span>✕</span> Incorrect (0.0)
        </button>
      </div>

      {/* Recent Trial Logs */}
      {trialLogs.length > 0 && (
        <div style={{ marginTop: "0.85rem", borderTop: "1px solid var(--border-subdued)", paddingTop: "0.65rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-tertiary)" }}>
              Recent Block Logs
            </span>
            <button
              type="button"
              onClick={() => therapyStore.clearTrialLogs()}
              style={{ background: "none", border: "none", fontSize: "0.7rem", color: "var(--surface-overlay)", cursor: "pointer", textDecoration: "underline" }}
            >
              Clear
            </button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem", maxHeight: "120px", overflowY: "auto" }}>
            {trialLogs.slice(-4).reverse().map((log) => (
              <div
                key={log.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  fontSize: "0.75rem",
                  padding: "0.3rem 0.6rem",
                  backgroundColor: "var(--bg-canvas)",
                  borderRadius: "6px",
                  border: "1px solid var(--border-subdued)",
                }}
              >
                <span>
                  <strong style={{ color: "var(--text-primary)" }}>"{log.targetWord}"</strong> ({log.cueLevel})
                </span>
                <span style={{ fontWeight: 700, color: log.rating === "correct" ? "var(--success-text)" : log.rating === "approx" ? "var(--warn-text)" : "var(--danger-text)" }}>
                  {log.rating.toUpperCase()} • {log.timestamp}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
