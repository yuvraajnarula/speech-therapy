/**
 * LiveTutorMode — Real-time adaptive speech therapy coaching.
 *
 * Uses /ws/live-tutor WebSocket with the memory layer to:
 *  - Select drill targets based on patient's weak phonemes
 *  - Provide encouragement feedback after each attempt
 *  - Adapt difficulty based on consecutive correct/incorrect streaks
 *  - Display session score and phoneme mastery progress
 */
import { useState, useCallback } from "react";
import { useTherapyStore } from "../store/therapyStore";
import { useLiveTutor } from "../protocol/useLiveTutor";

interface LiveTutorModeProps {
  authToken?: string | null;
}

const DIALECT_LABELS: Record<string, string> = {
  hi: "Hindi",
  kn: "Kannada",
  ta: "Tamil",
  te: "Telugu",
  "en-IN": "English (India)",
};

// -------------------------------------------------------------------------
// Render helpers (hoisted out of the component so they are not re-created
// on every render — creating components during render breaks hook order)
// -------------------------------------------------------------------------

function StatusBadge({ label, color }: { label: string; color: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: "9999px",
        fontSize: "0.75rem",
        fontWeight: 600,
        background: color,
        color: "var(--text-primary)",
        letterSpacing: "0.04em",
      }}
    >
      {label}
    </span>
  );
}

function Metric({ label, value, accent = "var(--surface-overlay)" }: { label: string; value: number; accent?: string }) {
  return (
    <div>
      <p style={{ margin: "0 0 4px", color: "var(--text-tertiary)", fontSize: "0.75rem", fontWeight: 600 }}>{label}</p>
      <span style={{ color: accent, fontSize: "1.5rem", fontWeight: 700 }}>{value}</span>
    </div>
  );
}

export default function LiveTutorMode({ authToken = null }: LiveTutorModeProps) {
  const sourceLanguage = useTherapyStore((s) => s.sourceLanguage);
  const tutorSession = useTherapyStore((s) => s.tutorSession);
  const patientMemory = useTherapyStore((s) => s.patientMemory);

  const [patientId] = useState(() => {
    // In production, inject real patient UUID from auth context.
    // For demo, use a stable session identifier.
    return sessionStorage.getItem("indicast_patient_id") ?? "demo-patient-" + Math.random().toString(36).slice(2, 8);
  });

  const { status, error, isRecording, start, startRecording, stopAndSubmit, stop } =
    useLiveTutor(authToken);

  const handleStart = useCallback(() => {
    start(patientId, sourceLanguage);
  }, [start, patientId, sourceLanguage]);

  // -------------------------------------------------------------------------
  // Status badge helpers
  // -------------------------------------------------------------------------

  const statusColor =
    status === "active"
      ? "var(--success-text)"
      : status === "complete"
      ? "var(--accent-primary)"
      : status === "error"
      ? "var(--danger-text)"
      : "var(--text-tertiary)";

  const statusLabel =
    status === "connecting"
      ? "Connecting…"
      : status === "active"
      ? "Live Session"
      : status === "complete"
      ? "Session Complete"
      : status === "error"
      ? "Error"
      : "Ready";

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div
      style={{
        background: "var(--bg-canvas)",
        minHeight: "100%",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        maxWidth: "900px",
        margin: "0 auto",
      }}
    >
      {/* ---- Header ---- */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ margin: 0, color: "var(--text-primary)", fontSize: "1.25rem", fontWeight: 600 }}>
            🎓 Live Tutor Mode
          </h2>
          <p style={{ margin: "4px 0 0", color: "var(--text-tertiary)", fontSize: "0.875rem" }}>
            Adaptive coaching powered by clinical memory — {DIALECT_LABELS[sourceLanguage] ?? sourceLanguage}
          </p>
        </div>
        <StatusBadge label={statusLabel} color={statusColor} />
      </div>

      {/* ---- Memory Context Bar ---- */}
      {patientMemory && patientMemory.weak_phonemes_ranked.length > 0 && (
        <div
          style={{
            background: "var(--surface-overlay)",
            border: "1px solid var(--border-subdued)",
            borderRadius: "12px",
            padding: "16px 20px",
          }}
        >
          <p style={{ margin: "0 0 10px", color: "var(--text-secondary)", fontSize: "0.8rem", fontWeight: 600, letterSpacing: "0.08em" }}>
            MEMORY LAYER — WEAK PHONEMES
          </p>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {patientMemory.weak_phonemes_ranked.slice(0, 6).map((ph) => {
              const errorCount = patientMemory.phoneme_errors[ph] ?? 0;
              const mastery = patientMemory.mastery_scores[ph] ?? 0;
              const masteryPct = Math.round(mastery * 100);
              return (
                <div
                  key={ph}
                  style={{
                    background: "var(--bg-canvas)",
                    border: `1px solid ${errorCount > 5 ? "var(--danger-border)" : errorCount > 2 ? "var(--warn-border)" : "var(--border-subdued)"}`,
                    borderRadius: "8px",
                    padding: "8px 14px",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    minWidth: "72px",
                  }}
                >
                  <span style={{ color: "var(--pill-text)", fontSize: "1rem", fontWeight: 700, fontFamily: "monospace" }}>{ph}</span>
                  <span style={{ color: "var(--text-tertiary)", fontSize: "0.7rem" }}>✗ {errorCount}</span>
                  <span style={{ color: masteryPct > 70 ? "var(--success-text)" : masteryPct > 40 ? "var(--warn-text)" : "var(--danger-text)", fontSize: "0.7rem" }}>
                    {masteryPct}% mastery
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ---- Error State ---- */}
      {error && (
        <div
          style={{
            background: "var(--surface-overlay)",
            border: "1px solid var(--danger-border)",
            borderRadius: "12px",
            padding: "16px 20px",
            color: "var(--danger-text)",
            fontSize: "0.875rem",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* ---- Idle: Start Session ---- */}
      {(status === "idle" || status === "error") && (
        <div
          style={{
            background: "var(--surface-overlay)",
            border: "1px solid var(--border-subdued)",
            borderRadius: "12px",
            padding: "32px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "20px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: "3rem" }}>🎯</div>
          <div>
            <h3 style={{ margin: "0 0 8px", color: "var(--text-primary)", fontWeight: 600 }}>
              Start Your Adaptive Session
            </h3>
            <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.875rem", maxWidth: "420px" }}>
              The tutor will select drill words targeting your weakest phonemes based on your session history.
              {patientMemory?.total_attempts
                ? ` Based on ${patientMemory.total_attempts} past attempts.`
                : " Building your phoneme profile as you go."}
            </p>
          </div>
          <button
            onClick={handleStart}
            style={{
              background: "linear-gradient(135deg, var(--bg-elevated), var(--surface-overlay))",
              color: "var(--text-primary)",
              border: "1px solid var(--border-subdued)",
              borderRadius: "9999px",
              padding: "12px 32px",
              fontSize: "1rem",
              fontWeight: 600,
              cursor: "pointer",
              letterSpacing: "0.02em",
            }}
          >
            Begin Session →
          </button>
        </div>
      )}

      {/* ---- Active: Drill Target ---- */}
      {status === "active" && tutorSession.currentCue && (
        <div
          style={{
            background: "var(--surface-overlay)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "28px",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          {/* Target word display */}
          <div style={{ textAlign: "center" }}>
            <p style={{ margin: "0 0 8px", color: "var(--text-tertiary)", fontSize: "0.75rem", fontWeight: 600, letterSpacing: "0.1em" }}>
              SAY THIS WORD
            </p>
            <div style={{ fontSize: "3rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "6px" }}>
              {tutorSession.currentCue.target_word}
            </div>
            {tutorSession.currentCue.native_script && (
              <div style={{ fontSize: "1.75rem", color: "var(--text-tertiary)", marginBottom: "4px" }}>
                {tutorSession.currentCue.native_script}
              </div>
            )}
            {tutorSession.currentCue.ipa && (
              <div style={{ fontSize: "0.9rem", color: "var(--text-tertiary)", fontFamily: "monospace" }}>
                {tutorSession.currentCue.ipa}
              </div>
            )}
          </div>

          {/* Phoneme focus */}
          {tutorSession.currentCue.phoneme_target && (
            <div
              style={{
                background: "var(--bg-canvas)",
                borderRadius: "8px",
                padding: "10px 16px",
                display: "flex",
                alignItems: "center",
                gap: "10px",
              }}
            >
              <span style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>Focus phoneme:</span>
              <span
                style={{
                  background: "var(--surface-overlay)",
                  color: "var(--pill-text)",
                  borderRadius: "6px",
                  padding: "2px 10px",
                  fontFamily: "monospace",
                  fontSize: "0.9rem",
                  fontWeight: 600,
                }}
              >
                {tutorSession.currentCue.phoneme_target}
              </span>
            </div>
          )}

          {/* Encouragement message */}
          {tutorSession.encouragement && (
            <div
              style={{
                borderLeft: "3px solid var(--accent-primary)",
                paddingLeft: "14px",
                color: "var(--text-secondary)",
                fontSize: "0.9rem",
                fontStyle: "italic",
              }}
            >
              {tutorSession.encouragement}
            </div>
          )}

          {/* Recording controls */}
          <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
            {!isRecording ? (
              <button
                onClick={startRecording}
                style={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--accent-primary)",
                  color: "var(--accent-primary)",
                  borderRadius: "9999px",
                  padding: "12px 28px",
                  fontSize: "0.9rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                🎙️ Speak Now
              </button>
            ) : (
              <button
                onClick={stopAndSubmit}
                style={{
                  background: "var(--danger-bg)",
                  border: "1px solid var(--danger-border)",
                  color: "var(--danger-text)",
                  borderRadius: "9999px",
                  padding: "12px 28px",
                  fontSize: "0.9rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                ⏹ Submit
              </button>
            )}
            <button
              onClick={stop}
              style={{
                background: "transparent",
                border: "1px solid var(--border-subdued)",
                color: "var(--text-tertiary)",
                borderRadius: "9999px",
                padding: "12px 20px",
                fontSize: "0.875rem",
                cursor: "pointer",
              }}
            >
              End Session
            </button>
          </div>
        </div>
      )}

      {status === "active" && tutorSession.memorySnapshot && (
        <div
          style={{
            background: "var(--surface-overlay)",
            border: "1px solid var(--border-subdued)",
            borderRadius: "12px",
            padding: "16px 20px",
            display: "flex",
            gap: "24px",
            flexWrap: "wrap",
          }}
        >
          <Metric label="Attempts" value={tutorSession.memorySnapshot.total_attempts} />
          <Metric label="Streak ✓" value={tutorSession.memorySnapshot.consecutive_correct} accent="var(--success-text)" />
          <Metric label="Streak ✗" value={tutorSession.memorySnapshot.consecutive_incorrect} accent="var(--danger-text)" />
          <div>
            <p style={{ margin: "0 0 6px", color: "var(--text-tertiary)", fontSize: "0.75rem", fontWeight: 600 }}>TOP TARGETS</p>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
              {tutorSession.memorySnapshot.weak_phonemes.slice(0, 4).map((ph) => (
                <span
                  key={ph}
                  style={{
                    background: "var(--surface-overlay)",
                    color: "var(--pill-text)",
                    borderRadius: "6px",
                    padding: "2px 8px",
                    fontFamily: "monospace",
                    fontSize: "0.8rem",
                  }}
                >
                  {ph}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ---- Session Score ---- */}
      {tutorSession.sessionScore.total > 0 && (
        <div
          style={{
            background: "var(--surface-overlay)",
            border: "1px solid var(--border-subdued)",
            borderRadius: "12px",
            padding: "16px 20px",
            display: "flex",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <span style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>Session Score:</span>
          <span style={{ color: "var(--text-primary)", fontWeight: 700, fontSize: "1.25rem" }}>
            {tutorSession.sessionScore.correct} / {tutorSession.sessionScore.total}
          </span>
          <span style={{ color: "var(--text-tertiary)", fontSize: "0.875rem" }}>
            ({Math.round((tutorSession.sessionScore.correct / tutorSession.sessionScore.total) * 100)}%)
          </span>
        </div>
      )}

      {/* ---- Complete ---- */}
      {status === "complete" && (
        <div
          style={{
            background: "var(--surface-overlay)",
            border: "1px solid var(--success-border)",
            borderRadius: "12px",
            padding: "28px",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
            alignItems: "center",
          }}
        >
          <div style={{ fontSize: "2.5rem" }}>🏆</div>
          <h3 style={{ margin: 0, color: "var(--text-primary)" }}>{tutorSession.encouragement}</h3>
          <button
            onClick={handleStart}
            style={{
              background: "linear-gradient(135deg, var(--bg-elevated), var(--surface-overlay))",
              color: "var(--text-primary)",
              border: "1px solid var(--border-subdued)",
              borderRadius: "9999px",
              padding: "10px 24px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Start New Session
          </button>
        </div>
      )}
    </div>
  );
}
