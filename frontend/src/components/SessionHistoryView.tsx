import React from "react";
import { useTherapyStore, therapyStore } from "../store/therapyStore";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";

export const SessionHistoryView: React.FC = () => {
  const trialLogs = useTherapyStore((s) => s.trialLogs);
  const userRole = useTherapyStore((s) => s.userRole);
  const sourceLanguage = useTherapyStore((s) => s.sourceLanguage);

  const totalTrials = trialLogs.length;
  const correctCount = trialLogs.filter((t) => t.rating === "correct").length;
  const approxCount = trialLogs.filter((t) => t.rating === "approx").length;
  const incorrectCount = trialLogs.filter((t) => t.rating === "incorrect").length;
  const overallAccuracy = totalTrials > 0 ? Math.round(((correctCount + approxCount * 0.5) / totalTrials) * 100) : 0;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        backgroundColor: "#ffffff",
        borderRadius: "12px",
        border: "1px solid #e2e8f0",
        padding: "1.5rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
      }}
    >
      {/* Header & Clinical Metrics */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "#0f172a" }}>
            Clinical SOAP Trial Telemetry & Progress
          </h3>
          <p style={{ margin: "0.2rem 0 0", fontSize: "0.8rem", color: "#64748b" }}>
            Trial-by-trial articulatory data for clinical documentation and insurance billing
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => therapyStore.clearTrialLogs()}
            disabled={totalTrials === 0}
          >
            Clear Session
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => window.print()}
            disabled={totalTrials === 0}
          >
            🖨️ Export / Print SOAP
          </Button>
        </div>
      </div>

      {/* Trial Performance Cards Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.75rem" }}>
        <div style={{ padding: "0.85rem", backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <span style={{ fontSize: "0.7rem", color: "#64748b", textTransform: "uppercase", fontWeight: 700 }}>
            Total Trials
          </span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#0f172a", fontFamily: "ui-monospace, monospace" }}>
            {totalTrials}
          </div>
        </div>

        <div style={{ padding: "0.85rem", backgroundColor: "#ecfdf5", borderRadius: "8px", border: "1px solid #a7f3d0" }}>
          <span style={{ fontSize: "0.7rem", color: "#065f46", textTransform: "uppercase", fontWeight: 700 }}>
            Independent / Correct
          </span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#065f46", fontFamily: "ui-monospace, monospace" }}>
            {correctCount}
          </div>
        </div>

        <div style={{ padding: "0.85rem", backgroundColor: "#fffbeb", borderRadius: "8px", border: "1px solid #fde68a" }}>
          <span style={{ fontSize: "0.7rem", color: "#92400e", textTransform: "uppercase", fontWeight: 700 }}>
            Approximated (Prompted)
          </span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#92400e", fontFamily: "ui-monospace, monospace" }}>
            {approxCount}
          </div>
        </div>

        <div style={{ padding: "0.85rem", backgroundColor: "#eff6ff", borderRadius: "8px", border: "1px solid #bfdbfe" }}>
          <span style={{ fontSize: "0.7rem", color: "#1d4ed8", textTransform: "uppercase", fontWeight: 700 }}>
            Weighted Mastery Score
          </span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#1d4ed8", fontFamily: "ui-monospace, monospace" }}>
            {overallAccuracy}%
          </div>
        </div>
      </div>

      {/* Trial Logs Table */}
      {totalTrials > 0 ? (
        <div style={{ overflowX: "auto", border: "1px solid #e2e8f0", borderRadius: "8px" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
            <thead>
              <tr style={{ backgroundColor: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                <th style={{ padding: "0.65rem 1rem", color: "#64748b", fontWeight: 600 }}>Timestamp</th>
                <th style={{ padding: "0.65rem 1rem", color: "#64748b", fontWeight: 600 }}>Target Stimulus</th>
                <th style={{ padding: "0.65rem 1rem", color: "#64748b", fontWeight: 600 }}>Prompt Level</th>
                <th style={{ padding: "0.65rem 1rem", color: "#64748b", fontWeight: 600 }}>Rating</th>
                <th style={{ padding: "0.65rem 1rem", color: "#64748b", fontWeight: 600 }}>Mastery Value</th>
              </tr>
            </thead>
            <tbody>
              {trialLogs.slice().reverse().map((trial) => (
                <tr key={trial.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                  <td style={{ padding: "0.65rem 1rem", color: "#64748b", fontFamily: "ui-monospace, monospace" }}>
                    {trial.timestamp}
                  </td>
                  <td style={{ padding: "0.65rem 1rem", fontWeight: 600, color: "#0f172a" }}>
                    "{trial.targetWord}"
                  </td>
                  <td style={{ padding: "0.65rem 1rem" }}>
                    <Badge variant="outline">
                      {trial.cueLevel.toUpperCase()}
                    </Badge>
                  </td>
                  <td style={{ padding: "0.65rem 1rem" }}>
                    <Badge variant={trial.rating === "correct" ? "success" : trial.rating === "approx" ? "warning" : "destructive"}>
                      {trial.rating.toUpperCase()}
                    </Badge>
                  </td>
                  <td style={{ padding: "0.65rem 1rem", fontFamily: "ui-monospace, monospace", fontWeight: 700 }}>
                    {trial.score.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div
          style={{
            padding: "3rem",
            textAlign: "center",
            backgroundColor: "#f8fafc",
            borderRadius: "8px",
            border: "1px dashed #cbd5e1",
            color: "#64748b",
          }}
        >
          <p style={{ margin: 0, fontSize: "0.9rem" }}>
            No trials recorded in current session block. Complete speech attempts or log clinician prompts to populate SOAP telemetry.
          </p>
        </div>
      )}

      {/* Clinician SOAP Narrative Draft */}
      {userRole === "therapist" && totalTrials > 0 && (
        <div
          style={{
            backgroundColor: "#f8fafc",
            borderLeft: "4px solid #0f172a",
            padding: "1rem 1.25rem",
            borderRadius: "6px",
            fontSize: "0.8rem",
            color: "#334155",
            lineHeight: 1.6,
          }}
        >
          <strong>Draft SOAP Note:</strong>
          <br />
          <strong>S:</strong> Patient attended session targeting Indian dialect articulation ({sourceLanguage.toUpperCase()}). Cooperated with visual and acoustic prompts.
          <br />
          <strong>O:</strong> Patient completed {totalTrials} trials. Achieved {correctCount}/{totalTrials} ({overallAccuracy}%) accuracy across target phoneme stimuli.
          <br />
          <strong>A:</strong> Demonstrated improved articulatory placement on bilabial plosives. Minor substitution errors noted on retroflex stops requiring visual modeling.
          <br />
          <strong>P:</strong> Continue multi-sensory drill in carrier phrases. Transition to independent production next session.
        </div>
      )}
    </div>
  );
};
