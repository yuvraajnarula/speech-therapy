import React from "react";
import { useTherapyStore, DiagnosticResult } from "../store/therapyStore";
import { WaveformComparator } from "./WaveformComparator";
import { PhonemeTelemetryPills } from "./PhonemeTelemetryPills";
import { ClinicianPromptLogger } from "./ClinicianPromptLogger";
import { Badge } from "./ui/Badge";

interface DualPaneASTProps {
  diagnostic: DiagnosticResult | null;
}

export const DualPaneAST: React.FC<DualPaneASTProps> = ({ diagnostic }) => {
  const userRole = useTherapyStore((s) => s.userRole);
  const targetWord = useTherapyStore((s) => s.targetWord);
  const sourceLanguage = useTherapyStore((s) => s.sourceLanguage);
  const targetLanguage = useTherapyStore((s) => s.targetLanguage);
  const hasPatientAudio = useTherapyStore((s) => s.hasPatientAudio);

  const targetPhonemes = diagnostic?.target_phonemes
    ? diagnostic.target_phonemes.split("")
    : [];
  const spokenPhonemes = diagnostic?.spoken_phonemes
    ? diagnostic.spoken_phonemes.split("")
    : [];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1.25fr 1fr",
        gap: "1.25rem",
        marginTop: "1.25rem",
      }}
    >
      {/* ---------------------------------------------------------------------- */}
      {/* LEFT STAGE: Acoustic Comparator & SODA Articulation Matrix */}
      {/* ---------------------------------------------------------------------- */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        {/* Waveform Comparator */}
        <WaveformComparator
          targetWord={targetWord}
          sourceLanguage={sourceLanguage}
          targetPhonemes={targetPhonemes}
          spokenPhonemes={spokenPhonemes}
          hasPatientAudio={hasPatientAudio}
        />

        {/* SODA Phoneme Diagnostic Matrix */}
        {diagnostic ? (
          <PhonemeTelemetryPills diagnostic={diagnostic} />
        ) : (
          <div
            style={{
              padding: "2rem",
              textAlign: "center",
              backgroundColor: "#ffffff",
              borderRadius: "10px",
              border: "1px dashed #cbd5e1",
              color: "#64748b",
            }}
          >
            <p style={{ margin: 0, fontSize: "0.85rem" }}>
              Awaiting speech take. Click <strong>"Start Speaking"</strong> to capture audio and generate real-time SODA alignment.
            </p>
          </div>
        )}
      </div>

      {/* ---------------------------------------------------------------------- */}
      {/* RIGHT STAGE: Clinician HUD & Live AST Translation */}
      {/* ---------------------------------------------------------------------- */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        {/* Clinician Prompt Hierarchy Logger */}
        {userRole === "therapist" && <ClinicianPromptLogger />}

        {/* Live AST Automatic Speech Translation Box */}
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
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "1rem" }}>🌐</span>
              <h4 style={{ margin: 0, fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
                Live AST & Translation Stream
              </h4>
            </div>
            <Badge variant="secondary">
              {sourceLanguage.toUpperCase()} ➔ {targetLanguage.toUpperCase()}
            </Badge>
          </div>

          <p style={{ fontSize: "0.75rem", color: "#64748b", margin: "0 0 0.85rem" }}>
            Real-time cross-lingual translation bridge for multilingual clinical communication.
          </p>

          {diagnostic ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {/* Spoken Utterance Detected */}
              <div
                style={{
                  backgroundColor: "#f8fafc",
                  padding: "0.75rem 1rem",
                  borderRadius: "6px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <span style={{ fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase", color: "#94a3b8" }}>
                  Patient Utterance ({sourceLanguage.toUpperCase()})
                </span>
                <div style={{ fontSize: "1.05rem", fontWeight: 600, color: "#0f172a", marginTop: "0.2rem" }}>
                  "{diagnostic.spoken}"
                </div>
              </div>

              {/* Live Translation Output */}
              <div
                style={{
                  backgroundColor: "#eff6ff",
                  padding: "0.75rem 1rem",
                  borderRadius: "6px",
                  border: "1px solid #bfdbfe",
                }}
              >
                <span style={{ fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase", color: "#2563eb" }}>
                  Live Translation ({targetLanguage.toUpperCase()})
                </span>
                <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "#1e3a8a", marginTop: "0.2rem" }}>
                  "{diagnostic.translated_text || diagnostic.spoken}"
                </div>
              </div>
            </div>
          ) : (
            <div
              style={{
                padding: "1.5rem",
                textAlign: "center",
                backgroundColor: "#f8fafc",
                borderRadius: "6px",
                border: "1px dashed #cbd5e1",
                color: "#94a3b8",
                fontSize: "0.8rem",
              }}
            >
              Spoken words and instant translation will stream here during session practice.
            </div>
          )}
        </div>

        {/* Clinical Telemetry Summary */}
        <div
          style={{
            borderRadius: "10px",
            border: "1px solid #e2e8f0",
            backgroundColor: "#f8fafc",
            padding: "1rem 1.25rem",
            fontSize: "0.75rem",
            color: "#64748b",
            display: "flex",
            flexDirection: "column",
            gap: "0.4rem",
          }}
        >
          <div style={{ fontWeight: 700, color: "#334155", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Acoustic Pipeline Telemetry
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>Silero VAD Chunking:</span>
            <strong style={{ color: "#059669" }}>Active (16kHz PCM mono)</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>ASR Acoustic Model:</span>
            <strong>faster-whisper / IndicWhisper</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>Translation Model:</span>
            <strong>IndicTrans2 AST Adapter</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span>PHI Encryption:</span>
            <strong>AES-256 at-rest</strong>
          </div>
        </div>
      </div>
    </div>
  );
};
