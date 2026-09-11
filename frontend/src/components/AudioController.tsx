import React, { useEffect } from "react";
import { useTherapyStore, therapyStore } from "../store/therapyStore";
import { Button } from "./ui/Button";
import { Badge } from "./ui/Badge";
import { INDIC_WORD_BANK } from "../data/indicWordBank";

interface AudioControllerProps {
  onStart: () => void;
  onStop: () => void;
}

export const AudioController: React.FC<AudioControllerProps> = ({ onStart, onStop }) => {
  const targetWord = useTherapyStore((s) => s.targetWord);
  const sourceLanguage = useTherapyStore((s) => s.sourceLanguage);
  const isListening = useTherapyStore((s) => s.isListening);
  const isProcessing = useTherapyStore((s) => s.isProcessing);
  const agentStatus = useTherapyStore((s) => s.agentStatus);

  // Match target word in word bank if available
  const matchedItem = INDIC_WORD_BANK.find(
    (w) => w.romanized.toLowerCase() === targetWord.toLowerCase()
  );

  // Accessible keyboard shortcuts: Space to toggle speaking, Escape to cancel
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && e.target === document.body && !isProcessing) {
        e.preventDefault();
        if (isListening) onStop();
        else onStart();
      } else if (e.code === "Escape" && isListening) {
        onStop();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isListening, isProcessing, onStart, onStop]);

  // Suggestions for current language
  const languageSuggestions = INDIC_WORD_BANK.filter(
    (w) => w.language === sourceLanguage || (sourceLanguage === "en" && w.language === "en-IN")
  ).slice(0, 5);

  return (
    <section
      aria-label="Speech exercise controls"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        backgroundColor: "#ffffff",
        padding: "1.5rem",
        borderRadius: "12px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
        border: "1px solid #e2e8f0",
      }}
    >
      {/* Target Stimulus Card Display */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          backgroundColor: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "8px",
          padding: "1rem 1.25rem",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>
              Active Target Stimulus
            </span>
            {matchedItem && (
              <Badge variant="secondary">
                {matchedItem.phonemeTarget} • {matchedItem.phoneticPosition}
              </Badge>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "baseline", gap: "0.75rem" }}>
            {matchedItem?.nativeScript && (
              <span style={{ fontSize: "2.25rem", fontWeight: 800, color: "#0f172a" }}>
                {matchedItem.nativeScript}
              </span>
            )}
            <span style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>
              "{targetWord}"
            </span>
            {matchedItem && (
              <span style={{ fontSize: "0.9rem", color: "#64748b" }}>
                ({matchedItem.englishMeaning})
              </span>
            )}
          </div>

          {matchedItem && (
            <div style={{ fontSize: "0.8rem", color: "#475569", marginTop: "0.25rem" }}>
              IPA: <code style={{ color: "#2563eb", fontWeight: 600 }}>{matchedItem.ipa}</code> — {matchedItem.clinicalCue}
            </div>
          )}
        </div>

        {/* Custom target input */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input
            type="text"
            value={targetWord}
            onChange={(e) => therapyStore.setTargetWord(e.target.value.toLowerCase())}
            disabled={isListening || isProcessing}
            placeholder="Type target word..."
            style={{
              padding: "0.5rem 0.85rem",
              borderRadius: "6px",
              border: "1px solid #cbd5e1",
              fontSize: "0.9rem",
              width: "160px",
            }}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => therapyStore.setActiveTab("wordbank")}
          >
            Browse Bank ➔
          </Button>
        </div>
      </div>

      {/* Suggested Words Bar */}
      {languageSuggestions.length > 0 && (
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#94a3b8", textTransform: "uppercase" }}>
            Quick Drill Targets:
          </span>
          {languageSuggestions.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                therapyStore.setTargetWord(item.romanized);
              }}
              disabled={isListening || isProcessing}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                padding: "0.25rem 0.65rem",
                borderRadius: "6px",
                border: targetWord.toLowerCase() === item.romanized.toLowerCase() ? "1px solid #2563eb" : "1px solid #e2e8f0",
                backgroundColor: targetWord.toLowerCase() === item.romanized.toLowerCase() ? "#eff6ff" : "#f8fafc",
                color: targetWord.toLowerCase() === item.romanized.toLowerCase() ? "#1d4ed8" : "#334155",
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              <span>{item.nativeScript}</span>
              <span style={{ fontWeight: 400, color: "#64748b" }}>({item.romanized})</span>
            </button>
          ))}
        </div>
      )}

      {/* Recording PTT Button & Audio Meter */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {!isListening && !isProcessing ? (
            <button
              type="button"
              onClick={onStart}
              aria-label={`Start speaking target ${targetWord}`}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.75rem 1.85rem",
                backgroundColor: "#0f172a",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                fontSize: "0.95rem",
                fontWeight: 600,
                cursor: "pointer",
                boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
              }}
            >
              <span style={{ fontSize: "1.1rem" }}>🎙️</span>
              <span>Start Speaking "{targetWord}"</span>
              <span style={{ fontSize: "0.75rem", opacity: 0.6, marginLeft: "0.25rem" }}>[Space]</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={onStop}
              disabled={!isListening || isProcessing}
              aria-label="Stop recording and run SODA alignment"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.75rem 1.85rem",
                backgroundColor: isProcessing ? "#475569" : "#dc2626",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                fontSize: "0.95rem",
                fontWeight: 600,
                cursor: isProcessing ? "wait" : "pointer",
              }}
            >
              <span>{isProcessing ? "⏳" : "⏹️"}</span>
              <span>{isProcessing ? "Aligning Phonemes..." : "Stop & Analyze Take"}</span>
            </button>
          )}

          {/* Voice Pulse Indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            {isListening && (
              <span
                style={{
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  backgroundColor: "#ef4444",
                  display: "inline-block",
                  animation: "pulse 1.5s infinite",
                }}
              />
            )}
            <span
              aria-live="polite"
              style={{
                fontSize: "0.85rem",
                color: isListening ? "#dc2626" : isProcessing ? "#2563eb" : "#64748b",
                fontWeight: 500,
              }}
            >
              {agentStatus}
            </span>
          </div>
        </div>

        {/* Keyboard shortcut hint */}
        <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
          Press <kbd style={{ padding: "0.15rem 0.4rem", backgroundColor: "#f1f5f9", borderRadius: "4px", border: "1px solid #cbd5e1" }}>Space</kbd> to talk / stop
        </div>
      </div>
    </section>
  );
};
