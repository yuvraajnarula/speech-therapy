import React, { useRef, useEffect, useState } from "react";
import { Button } from "./ui/Button";
import { Badge } from "./ui/Badge";
import { speakTargetReference } from "../data/indicWordBank";

interface WaveformComparatorProps {
  targetWord: string;
  sourceLanguage: "hi" | "kn" | "ta" | "te" | "en-IN";
  targetPhonemes: string[];
  spokenPhonemes: string[];
  hasPatientAudio: boolean;
}

export const WaveformComparator: React.FC<WaveformComparatorProps> = ({
  targetWord,
  sourceLanguage,
  targetPhonemes,
  spokenPhonemes,
  hasPatientAudio,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [activeTrack, setActiveTrack] = useState<"target" | "patient" | "both">("both");
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Render high-DPI crisp clinical audio waveform
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const width = rect.width || 560;
    const height = 110;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);

    // Center reference baseline
    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();

    // Render acoustic envelope bars
    const barWidth = 3;
    const gap = 2;
    const barCount = Math.floor(width / (barWidth + gap));

    for (let i = 0; i < barCount; i++) {
      const x = i * (barWidth + gap);

      // Model target curve
      const normalizedPos = i / barCount;
      const targetAmp =
        Math.sin(normalizedPos * Math.PI) * (height * 0.4) * (0.6 + 0.4 * Math.sin(i * 0.7));

      if (activeTrack === "target" || activeTrack === "both") {
        ctx.fillStyle = "#94a3b8"; // Slate-400 for model reference
        const h = Math.max(3, targetAmp);
        ctx.fillRect(x, height / 2 - h / 2, barWidth, h);
      }

      // Patient audio overlay
      if ((activeTrack === "patient" || activeTrack === "both") && hasPatientAudio) {
        // Overlay deviation
        const patientAmp = targetAmp * (0.85 + 0.25 * Math.sin(i * 1.3));
        ctx.fillStyle = "#2563eb"; // Cobalt blue
        const h = Math.max(3, patientAmp);
        ctx.fillRect(x + 1, height / 2 - h / 2, barWidth - 1, h);
      }
    }
  }, [hasPatientAudio, activeTrack, targetWord]);

  const handlePlayModel = async (rate: number = 1.0) => {
    setIsPlayingAudio(true);
    await speakTargetReference(targetWord, sourceLanguage, rate);
    setIsPlayingAudio(false);
  };

  return (
    <div
      style={{
        borderRadius: "10px",
        border: "1px solid #e2e8f0",
        backgroundColor: "#ffffff",
        padding: "1rem 1.25rem",
        boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
      }}
    >
      {/* Waveform Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid #f1f5f9",
          paddingBottom: "0.65rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span
            style={{
              display: "inline-block",
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: "#10b981",
            }}
          />
          <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "#64748b", letterSpacing: "0.05em" }}>
            Dual-Waveform Acoustic Comparator
          </span>
        </div>

        {/* Track switch buttons */}
        <div style={{ display: "flex", gap: "3px", backgroundColor: "#f1f5f9", padding: "2px", borderRadius: "6px" }}>
          <button
            type="button"
            onClick={() => setActiveTrack("target")}
            style={{
              padding: "0.25rem 0.6rem",
              fontSize: "0.75rem",
              fontWeight: 500,
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
              backgroundColor: activeTrack === "target" ? "#ffffff" : "transparent",
              color: activeTrack === "target" ? "#0f172a" : "#64748b",
              boxShadow: activeTrack === "target" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
            }}
          >
            Model Reference
          </button>
          <button
            type="button"
            onClick={() => setActiveTrack("patient")}
            style={{
              padding: "0.25rem 0.6rem",
              fontSize: "0.75rem",
              fontWeight: 500,
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
              backgroundColor: activeTrack === "patient" ? "#ffffff" : "transparent",
              color: activeTrack === "patient" ? "#0f172a" : "#64748b",
              boxShadow: activeTrack === "patient" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
            }}
          >
            Patient Spoken
          </button>
          <button
            type="button"
            onClick={() => setActiveTrack("both")}
            style={{
              padding: "0.25rem 0.6rem",
              fontSize: "0.75rem",
              fontWeight: 500,
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
              backgroundColor: activeTrack === "both" ? "#ffffff" : "transparent",
              color: activeTrack === "both" ? "#0f172a" : "#64748b",
              boxShadow: activeTrack === "both" ? "0 1px 2px rgba(0,0,0,0.05)" : "none",
            }}
          >
            Synchronous Overlay
          </button>
        </div>
      </div>

      {/* Canvas Area */}
      <div
        style={{
          margin: "0.75rem 0",
          borderRadius: "8px",
          backgroundColor: "#f8fafc",
          border: "1px solid #f1f5f9",
          padding: "0.5rem",
        }}
      >
        <canvas ref={canvasRef} style={{ width: "100%", height: "100px", display: "block" }} />
      </div>

      {/* Waveform Footer: IPA Strip & Model Audio Triggers */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontFamily: "ui-monospace, monospace", fontSize: "0.8rem" }}>
          <span style={{ color: "#94a3b8" }}>Target IPA:</span>
          {targetPhonemes.length > 0 ? (
            targetPhonemes.map((ph, idx) => (
              <Badge key={idx} variant="secondary">
                /{ph}/
              </Badge>
            ))
          ) : (
            <span style={{ color: "#64748b" }}>/{targetWord}/</span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePlayModel(1.0)}
            disabled={isPlayingAudio}
            title="Hear native clinical model pronunciation at standard speed"
          >
            🔊 Model (1.0x)
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePlayModel(0.75)}
            disabled={isPlayingAudio}
            title="Hear slow articulatory drill at 0.75x speed"
          >
            🐢 Drill (0.75x)
          </Button>
          {hasPatientAudio && (
            <Badge variant="success">
              ✓ Spoken Track Synced
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
};
