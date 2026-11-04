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
        backgroundColor: "var(--surface-overlay)",
        borderRadius: "12px",
        border: "1px solid var(--border-subdued)",
        padding: "1.5rem",
        boxShadow: "0 2px 8px rgba(28, 25, 23, 0.10)",
      }}
    >
      {/* Header & Clinical Metrics */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)" }}>
            Clinical SOAP Trial Telemetry & Progress
          </h3>
          <p style={{ margin: "0.2rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
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
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem" }}>
        <div style={{ padding: "0.85rem", backgroundColor: "var(--bg-canvas)", borderRadius: "8px", border: "1px solid var(--surface-overlay)" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", textTransform: "uppercase", fontWeight: 700 }}>
            Total Trials
          </span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", fontFamily: "ui-monospace, monospace" }}>
            {totalTrials}
          </div>
        </div>

        <div style={{ padding: "0.85rem", backgroundColor: "var(--success-bg)", borderRadius: "8px", border: "1px solid var(--success-bg)" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--success-text)", textTransform: "uppercase", fontWeight: 700 }}>
            Independent / Correct
          </span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--success-text)", fontFamily: "ui-monospace, monospace" }}>
            {correctCount}
          </div>
        </div>

        <div style={{ padding: "0.85rem", backgroundColor: "var(--warn-bg)", borderRadius: "8px", border: "1px solid var(--warn-bg)" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--warn-text)", textTransform: "uppercase", fontWeight: 700 }}>
            Approximated (Prompted)
          </span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--warn-text)", fontFamily: "ui-monospace, monospace" }}>
            {approxCount}
          </div>
        </div>

        <div style={{ padding: "0.85rem", backgroundColor: "var(--danger-bg)", borderRadius: "8px", border: "1px solid var(--danger-bg)" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--danger-text)", textTransform: "uppercase", fontWeight: 700 }}>
            Deviations / Incorrect
          </span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--danger-text)", fontFamily: "ui-monospace, monospace" }}>
            {incorrectCount}
          </div>
        </div>

        <div style={{ padding: "0.85rem", backgroundColor: "var(--accent-primary)", borderRadius: "8px", border: "1px solid var(--accent-primary)" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--accent-primary)", textTransform: "uppercase", fontWeight: 700 }}>
            Weighted Mastery Score
          </span>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--accent-primary)", fontFamily: "ui-monospace, monospace" }}>
            {overallAccuracy}%
          </div>
        </div>
      </div>

      {/* Trial Logs Table */}
      {totalTrials > 0 ? (
        <div style={{ overflowX: "auto", border: "1px solid var(--border-subdued)", borderRadius: "8px" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
            <thead>
              <tr style={{ backgroundColor: "var(--bg-canvas)", borderBottom: "1px solid var(--surface-overlay)" }}>
                <th style={{ padding: "0.65rem 1rem", color: "var(--text-secondary)", fontWeight: 600 }}>Timestamp</th>
                <th style={{ padding: "0.65rem 1rem", color: "var(--text-secondary)", fontWeight: 600 }}>Target Stimulus</th>
                <th style={{ padding: "0.65rem 1rem", color: "var(--text-secondary)", fontWeight: 600 }}>Prompt Level</th>
                <th style={{ padding: "0.65rem 1rem", color: "var(--text-secondary)", fontWeight: 600 }}>Rating</th>
                <th style={{ padding: "0.65rem 1rem", color: "var(--text-secondary)", fontWeight: 600 }}>Mastery Value</th>
              </tr>
            </thead>
            <tbody>
              {trialLogs.slice().reverse().map((trial) => (
                <tr key={trial.id} style={{ borderBottom: "1px solid var(--surface-overlay)", backgroundColor: "var(--bg-canvas)" }}>
                  <td style={{ padding: "0.65rem 1rem", color: "var(--text-secondary)", fontFamily: "ui-monospace, monospace" }}>
                    {trial.timestamp}
                  </td>
                  <td style={{ padding: "0.65rem 1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    "{trial.targetWord}"
                  </td>
                  <td style={{ padding: "0.65rem 1rem" }}>
                    <Badge variant="outline">{trial.cueLevel}</Badge>
                  </td>
                  <td style={{ padding: "0.65rem 1rem" }}>
                    <Badge variant={trial.rating === "correct" ? "success" : trial.rating === "approx" ? "warning" : "destructive"}>
                      {trial.rating.toUpperCase()}
                    </Badge>
                  </td>
                  <td style={{ padding: "0.65rem 1rem", fontFamily: "ui-monospace, monospace", fontWeight: 700, color: "var(--text-primary)" }}>
                    {(trial.score * 100).toFixed(0)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div
          style={{
            padding: "2.5rem",
            textAlign: "center",
            backgroundColor: "var(--bg-canvas)",
            borderRadius: "8px",
            border: "1px dashed var(--border-subdued)",
            color: "var(--text-tertiary)",
          }}
        >
          <div style={{ fontSize: "1.75rem", marginBottom: "0.5rem" }}>📊</div>
          <h4 style={{ margin: "0 0 0.25rem", color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            No Clinical Trials Logged in this Session
          </h4>
          <p style={{ margin: 0, fontSize: "0.8rem" }}>
            Rate patient takes using the Clinician Prompt Hierarchy Logger to compile automated SOAP progress metrics.
          </p>
        </div>
      )}

      {/* Clinical Notes Section */}
      {userRole === "therapist" && (
        <div
          style={{
            backgroundColor: "var(--bg-canvas)",
            borderRadius: "8px",
            border: "1px solid var(--border-subdued)",
            padding: "1rem 1.25rem",
            fontSize: "0.8rem",
          }}
        >
          <div style={{ fontWeight: 700, color: "var(--text-tertiary)", marginBottom: "0.4rem" }}>
            SOAP Clinical Summary Note Draft:
          </div>
          <div style={{ color: "var(--text-secondary)", lineHeight: 1.5 }}>
            <strong>S (Subjective):</strong> Patient engaged in articulatory practice across dialect track <code>{sourceLanguage.toUpperCase()}-IN</code>.<br />
            <strong>O (Objective):</strong> Total stimulus drill count: {totalTrials} trials. Overall unassisted accuracy: {overallAccuracy}%.<br />
            <strong>A (Assessment):</strong> {overallAccuracy >= 80 ? "Demonstrates sound mastery at the single-word level." : "Requires continued visual and verbal cues for alveolar/bilabial sound contrast."}<br />
            <strong>P (Plan):</strong> Continue daily 15-minute drills using native script cues with 0.75x slow auditory playback.
          </div>
        </div>
      )}
    </div>
  );
};
