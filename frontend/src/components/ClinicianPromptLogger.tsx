import React, { useState } from "react";
import { Button } from "./ui/Button";
import { Badge } from "./ui/Badge";
import { therapyStore, useTherapyStore, TrialLogItem } from "../store/therapyStore";

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
        borderRadius: "10px",
        border: "1px solid #e2e8f0",
        backgroundColor: "#ffffff",
        padding: "1.25rem",
        boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid #f1f5f9",
          paddingBottom: "0.65rem",
          marginBottom: "0.85rem",
        }}
      >
        <div>
          <h4 style={{ margin: 0, fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
            Clinician Prompt Hierarchy Logger
          </h4>
          <span style={{ fontSize: "0.7rem", color: "#64748b" }}>
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
      <div style={{ marginBottom: "0.75rem" }}>
        <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748b", display: "block", marginBottom: "0.4rem" }}>
          Prompt Level Provided:
        </span>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.4rem" }}>
          {(["independent", "verbal", "visual", "tactile"] as CueLevel[]).map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => setSelectedCue(level)}
              style={{
                padding: "0.4rem 0.6rem",
                borderRadius: "6px",
                fontSize: "0.75rem",
                fontWeight: selectedCue === level ? 700 : 500,
                textTransform: "capitalize",
                border: selectedCue === level ? "1px solid #2563eb" : "1px solid #e2e8f0",
                backgroundColor: selectedCue === level ? "#eff6ff" : "#ffffff",
                color: selectedCue === level ? "#1d4ed8" : "#475569",
                cursor: "pointer",
                transition: "all 0.1s ease",
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
            padding: "0.55rem 0.5rem",
            borderRadius: "6px",
            border: "1px solid #a7f3d0",
            backgroundColor: "#ecfdf5",
            color: "#065f46",
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
            padding: "0.55rem 0.5rem",
            borderRadius: "6px",
            border: "1px solid #fde68a",
            backgroundColor: "#fffbeb",
            color: "#92400e",
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
            padding: "0.55rem 0.5rem",
            borderRadius: "6px",
            border: "1px solid #fecaca",
            backgroundColor: "#fef2f2",
            color: "#991b1b",
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
        <div style={{ marginTop: "0.85rem", borderTop: "1px solid #f1f5f9", paddingTop: "0.6rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", color: "#94a3b8" }}>
              Recent Block Logs
            </span>
            <button
              type="button"
              onClick={() => therapyStore.clearTrialLogs()}
              style={{ background: "none", border: "none", fontSize: "0.7rem", color: "#64748b", cursor: "pointer", textDecoration: "underline" }}
            >
              Clear
            </button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem", maxHeight: "120px", overflowY: "auto" }}>
            {trialLogs.slice(-4).reverse().map((log) => (
              <div
                key={log.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  fontSize: "0.75rem",
                  padding: "0.25rem 0.5rem",
                  backgroundColor: "#f8fafc",
                  borderRadius: "4px",
                  border: "1px solid #f1f5f9",
                }}
              >
                <span>
                  <strong>"{log.targetWord}"</strong> ({log.cueLevel})
                </span>
                <span style={{ fontWeight: 700, color: log.rating === "correct" ? "#059669" : log.rating === "approx" ? "#d97706" : "#dc2626" }}>
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
