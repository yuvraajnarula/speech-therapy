import React from "react";
import { useTherapyStore, DiagnosticResult } from "../store/therapyStore";

const PHONEME_GUIDE: Record<string, string> = {
  HH: "H (breath from throat)",
  T: "T (alveolar tongue tap)",
  TR: "T (retroflex tongue curl)",
  K: "K (velar back of throat)",
  D: "D (tongue taps palate)",
  DR: "D (retroflex tongue curl)",
  G: "G (voiced velar)",
  P: "P (lip pop plosive)",
  B: "B (voiced lip pop)",
  S: "S (hissing snake)",
  SH: "SH (quiet fricative)",
  Z: "Z (buzzing bee)",
  TH: "TH (tongue between teeth)",
  DH: "DH (voiced dental)",
  AH: "uh (short central vowel)",
  AE: "a (cat)",
  AA: "aa (father)",
  OW: "oh (rounded lips)",
  IY: "ee (see)",
  IH: "ih (sit)",
  L: "L (tongue up against palate)",
  R: "R (growl/liquid sound)",
  M: "M (lips closed nasal)",
  N: "N (tongue tap nasal)",
  W: "W (rounded lips)",
  V: "V (teeth over lower lip)",
  F: "F (teeth over lower lip puff)",
};

interface PhonemeVisualizerProps {
  diagnostic: DiagnosticResult | null;
}

export const PhonemeVisualizer: React.FC<PhonemeVisualizerProps> = ({ diagnostic }) => {
  const highContrastMode = useTherapyStore((s) => s.highContrastMode);

  if (!diagnostic) {
    return (
      <div
        style={{
          padding: "2rem",
          textAlign: "center",
          backgroundColor: highContrastMode ? "#111" : "#f8fafc",
          borderRadius: "8px",
          border: "1px dashed #94a3b8",
          color: "#64748b",
        }}
      >
        <p>No audio analyzed yet. Click "Start Speaking" to begin your articulation exercise.</p>
      </div>
    );
  }

  const isSuccess = diagnostic.is_correct || diagnostic.target_achieved;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        backgroundColor: highContrastMode ? "#000" : "#ffffff",
        border: `2px solid ${isSuccess ? "#10b981" : "#f59e0b"}`,
        borderRadius: "10px",
        padding: "1.5rem",
      }}
    >
      {/* Header Status & Score */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <span
            style={{
              display: "inline-block",
              padding: "0.25rem 0.75rem",
              borderRadius: "9999px",
              fontSize: "0.85rem",
              fontWeight: 700,
              backgroundColor: isSuccess ? "#d1fae5" : "#fef3c7",
              color: isSuccess ? "#065f46" : "#92400e",
            }}
          >
            {isSuccess ? "Target Achieved!" : "Needs Improvement"}
          </span>
        </div>

        {diagnostic.accuracy_score !== undefined && (
          <div style={{ textAlign: "right" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b" }}>Articulation Accuracy: </span>
            <strong style={{ fontSize: "1.2rem", color: isSuccess ? "#10b981" : "#d97706" }}>
              {diagnostic.accuracy_score}%
            </strong>
          </div>
        )}
      </div>

      {/* Target vs Spoken Comparison */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1rem",
          backgroundColor: highContrastMode ? "#1e293b" : "#f1f5f9",
          padding: "1rem",
          borderRadius: "8px",
        }}
      >
        <div>
          <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "#64748b", fontWeight: 700 }}>
            Target Phrase
          </span>
          <div style={{ fontSize: "1.1rem", fontWeight: 600, color: highContrastMode ? "#fff" : "#0f172a" }}>
            "{diagnostic.target}"
          </div>
          {diagnostic.target_phonemes && (
            <div style={{ fontSize: "0.8rem", color: "#3b82f6", marginTop: "0.25rem" }}>
              Phonemes: /{diagnostic.target_phonemes}/
            </div>
          )}
        </div>

        <div>
          <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "#64748b", fontWeight: 700 }}>
            Spoken Detected
          </span>
          <div style={{ fontSize: "1.1rem", fontWeight: 600, color: highContrastMode ? "#fff" : "#0f172a" }}>
            "{diagnostic.spoken}"
          </div>
          {diagnostic.spoken_phonemes && (
            <div style={{ fontSize: "0.8rem", color: "#6366f1", marginTop: "0.25rem" }}>
              Phonemes: /{diagnostic.spoken_phonemes}/
            </div>
          )}
        </div>
      </div>

      {/* Phonetic Articulation Errors */}
      {diagnostic.errors && diagnostic.errors.length > 0 && (
        <div>
          <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.95rem", color: "#dc2626" }}>
            Articulation Deviations Detected:
          </h4>
          <ul style={{ margin: 0, paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {diagnostic.errors.map((err, idx) => (
              <li key={idx} style={{ fontSize: "0.9rem", color: highContrastMode ? "#fff" : "#334155" }}>
                {err.type === "replace" && (
                  <span>
                    <strong>Substituted</strong> /{err.target_slice}/
                    {PHONEME_GUIDE[err.target_slice] && ` (${PHONEME_GUIDE[err.target_slice]})`} with /
                    {err.spoken_slice}/
                    {PHONEME_GUIDE[err.spoken_slice] && ` (${PHONEME_GUIDE[err.spoken_slice]})`}
                  </span>
                )}
                {err.type === "delete" && (
                  <span>
                    <strong>Omitted Sound</strong> /{err.target_slice}/
                    {PHONEME_GUIDE[err.target_slice] && ` (${PHONEME_GUIDE[err.target_slice]})`}
                  </span>
                )}
                {err.type === "insert" && (
                  <span>
                    <strong>Extraneous Sound</strong> /{err.spoken_slice}/
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Clinical Guidance */}
      {diagnostic.clinical_feedback && (
        <div
          style={{
            backgroundColor: highContrastMode ? "#1a2e05" : "#f0fdf4",
            borderLeft: "4px solid #16a34a",
            padding: "0.75rem 1rem",
            borderRadius: "4px",
            fontSize: "0.85rem",
            color: highContrastMode ? "#dcfce7" : "#14532d",
            whiteSpace: "pre-line",
          }}
        >
          {diagnostic.clinical_feedback}
        </div>
      )}
    </div>
  );
};
