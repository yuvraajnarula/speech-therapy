import { Badge } from "./ui/Badge";
import type { DiagnosticResult } from "../store/therapyStore";

interface PhonemeTelemetryPillsProps {
  diagnostic: DiagnosticResult | null;
}

const PHONEME_ANATOMY_MAP: Record<string, { placement: string; cue: string }> = {
  P: { placement: "Bilabial Plosive", cue: "Press both lips together firmly, release sudden puff of air without vocal vibration." },
  B: { placement: "Voiced Bilabial", cue: "Close lips, engage vocal cords humming, then release." },
  T: { placement: "Alveolar Plosive", cue: "Tongue tip taps alveolar gum ridge behind top teeth." },
  T_DENTAL: { placement: "Dental Plosive", cue: "Place tongue tip lightly against upper front teeth." },
  TR_RETRO: { placement: "Retroflex Plosive", cue: "Curl tongue tip backwards towards hard palate dome." },
  K: { placement: "Velar Plosive", cue: "Back of tongue raises against soft palate (velum) in back of throat." },
  G: { placement: "Voiced Velar Plosive", cue: "Back of tongue against soft palate with vocal humming." },
  S: { placement: "Alveolar Fricative", cue: "Teeth lightly closed, tongue tip near ridge, blow steady cool hissing air." },
  SH: { placement: "Palato-Alveolar Fricative", cue: "Lips slightly rounded, gentle quiet sound." },
  Z: { placement: "Voiced Fricative", cue: "Tongue near ridge with buzzing vocal cord vibration." },
  L: { placement: "Lateral Liquid", cue: "Tongue tip up firmly against palate ridge, air escapes sides of tongue." },
  R: { placement: "Alveolar Liquid/Tap", cue: "Tongue curls or taps roof cleanly without touching teeth." },
  M: { placement: "Bilabial Nasal", cue: "Lips sealed, voice humming resonating in nasal cavity." },
  N: { placement: "Alveolar Nasal", cue: "Tongue tip pressed to ridge, nasal resonance." },
  ZH_RETRO: { placement: "Retroflex Approximant (Zha)", cue: "Curl tongue far back into palate dome without contact; smooth gliding airflow." },
};

export const PhonemeTelemetryPills: React.FC<PhonemeTelemetryPillsProps> = ({ diagnostic }) => {
  if (!diagnostic) return null;

  const errors = diagnostic.errors || [];
  const isCorrect = diagnostic.is_correct || diagnostic.target_achieved;
  const score = diagnostic.accuracy_score !== undefined ? diagnostic.accuracy_score : isCorrect ? 100 : 65;

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
      {/* SODA Diagnostic Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid var(--border-subdued)",
          paddingBottom: "0.75rem",
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)" }}>
            Phonemic Alignment & SODA Matrix
          </h3>
          <p style={{ margin: "0.2rem 0 0", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            Taxonomy: Substitution, Omission, Distortion, Addition
          </p>
        </div>

        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "1.4rem", fontWeight: 700, fontFamily: "ui-monospace, monospace", color: isCorrect ? "var(--success-text)" : "var(--warn-text)" }}>
            {score}%
          </div>
          <span style={{ fontSize: "0.7rem", color: "var(--text-tertiary)", textTransform: "uppercase", fontWeight: 600 }}>
            Articulation Score
          </span>
        </div>
      </div>

      {/* SODA Status Pills */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.65rem", marginTop: "1rem" }}>
        {isCorrect && errors.length === 0 ? (
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.5rem 0.85rem",
              borderRadius: "8px",
              backgroundColor: "var(--success-bg)",
              border: "1px solid var(--success-border)",
              color: "var(--success-text)",
              fontSize: "0.85rem",
              fontWeight: 600,
            }}
          >
            <span>✓</span>
            <span>Target Achieved: All target phonemes accurately articulated</span>
          </div>
        ) : (
          errors.map((err, idx) => {
            const isSub = err.type === "replace";
            const isDel = err.type === "delete";
            const isIns = err.type === "insert";
            const anatomy = PHONEME_ANATOMY_MAP[err.target_slice] || {
              placement: "Articulatory Target",
              cue: "Focus on tongue placement and steady airflow.",
            };

            return (
              <div
                key={idx}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  padding: "0.55rem 0.85rem",
                  borderRadius: "8px",
                  border: isSub
                    ? "1px solid var(--danger-text)"
                    : isDel
                    ? "1px solid var(--warn-text)"
                    : "1px solid var(--accent-primary)",
                  backgroundColor: isSub
                    ? "var(--danger-text)"
                    : isDel
                    ? "var(--warn-text)"
                    : "var(--accent-primary)",
                  color: isSub
                    ? "var(--danger-text)"
                    : isDel
                    ? "var(--warn-text)"
                    : "var(--accent-primary)",
                  fontSize: "0.8rem",
                  maxWidth: "280px",
                }}
                title={anatomy.cue}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontSize: "0.65rem", fontWeight: 800, textTransform: "uppercase" }}>
                    {isSub ? "Substitution (S)" : isDel ? "Omission (O)" : "Addition (A)"}
                  </span>
                  <Badge variant={isSub ? "destructive" : isDel ? "warning" : "secondary"}>
                    {err.target_slice || "Sound"}
                  </Badge>
                </div>

                <div style={{ fontFamily: "ui-monospace, monospace", fontWeight: 700, margin: "0.3rem 0", fontSize: "0.92rem" }}>
                  {isSub && (
                    <span>
                      /{err.target_slice}/ ➔ <span style={{ textDecoration: "underline", color: "var(--danger-text)" }}>/{err.spoken_slice}/</span>
                    </span>
                  )}
                  {isDel && <span>Omitted sound: /{err.target_slice}/</span>}
                  {isIns && <span>Extra sound: /{err.spoken_slice}/</span>}
                </div>

                <span style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                  {anatomy.placement}
                </span>
              </div>
            );
          })
        )}
      </div>

      {/* Clinical Guidance Accordion / Box */}
      {diagnostic.clinical_feedback && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: "6px",
            backgroundColor: "var(--bg-canvas)",
            borderLeft: "3px solid var(--accent-primary)",
            fontSize: "0.82rem",
            color: "var(--pill-text)",
            lineHeight: 1.5,
            whiteSpace: "pre-line",
            border: "1px solid var(--border-subdued)",
            borderLeftWidth: "3px",
          }}
        >
          {diagnostic.clinical_feedback}
        </div>
      )}
    </div>
  );
};
