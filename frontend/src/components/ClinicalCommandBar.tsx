import { useState } from "react";
import { therapyStore, useTherapyStore } from "../store/therapyStore";
import { INDIC_WORD_BANK } from "../data/indicWordBank";

export const ClinicalCommandBar: React.FC = () => {
  const [inputText, setInputText] = useState("");
  const [selectedModel, setSelectedModel] = useState("IndicWhisper v2 + AST");
  const [showModelMenu, setShowModelMenu] = useState(false);
  const [isVADPreview, setIsVADPreview] = useState(true);
  const isListening = useTherapyStore((s) => s.isListening);

  const availableModels = [
    "IndicWhisper v2 + AST",
    "faster-whisper (int8 CPU)",
    "Sarvam-1 Indic ASR",
    "IndicTrans2 Cross-Lingual Bridge",
  ];

  const handleCommandSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputText.trim();
    if (!query) return;

    // Intelligent target detection or clinical notes logging
    const lower = query.toLowerCase();
    const matchedWord = INDIC_WORD_BANK.find(
      (w) =>
        w.romanized.toLowerCase() === lower ||
        w.nativeScript === query ||
        w.englishMeaning.toLowerCase() === lower
    );

    if (matchedWord) {
      therapyStore.setTargetWord(matchedWord.romanized);
      therapyStore.setSourceLanguage(matchedWord.language);
      therapyStore.setAgentStatus(`Stimulus target updated to "${matchedWord.romanized}" (${matchedWord.nativeScript})`);
    } else {
      // Log as clinical note
      therapyStore.setAgentStatus(`Clinical observation noted: "${query.slice(0, 32)}..."`);
    }

    setInputText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleCommandSubmit();
    }
  };

  return (
    <div
      style={{
        marginTop: "1.5rem",
        borderRadius: "16px",
        backgroundColor: "var(--surface-overlay)",
        border: "1px solid var(--border-strong)",
        padding: "0.85rem 1rem",
        boxShadow: "0 4px 12px rgba(28, 25, 23, 0.12)",
        position: "relative",
      }}
    >
      {/* Multi-line input area */}
      <textarea
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a clinical instruction, word query (e.g. 'pani', 'kutta', 'apple'), or SOAP observation..."
        rows={2}
        style={{
          width: "100%",
          backgroundColor: "transparent",
          border: "none",
          outline: "none",
          color: "var(--text-primary)",
          fontSize: "0.9375rem",
          lineHeight: "1.5",
          resize: "none",
          fontFamily: "inherit",
          boxSizing: "border-box",
        }}
      />

      {/* Integrated Bottom Toolbar (design.md §3.3) */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "0.5rem",
          marginTop: "0.5rem",
          borderTop: "1px solid var(--border-subdued)",
          paddingTop: "0.6rem",
        }}
      >
        {/* Left Toolbar Items: Model Picker & Option Pills */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          {/* Model Picker Badge */}
          <div style={{ position: "relative" }}>
            <button
              type="button"
              onClick={() => setShowModelMenu(!showModelMenu)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.25rem 0.65rem",
                borderRadius: "9999px",
                backgroundColor: "var(--surface-overlay)",
                color: "var(--pill-text)",
                border: "1px solid var(--border-strong)",
                fontSize: "0.75rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              <span>🧠</span>
              <span>{selectedModel}</span>
              <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>▼</span>
            </button>

            {/* Model Selector Menu */}
            {showModelMenu && (
              <div
                style={{
                  position: "absolute",
                  bottom: "100%",
                  left: 0,
                  marginBottom: "0.5rem",
                  backgroundColor: "var(--bg-canvas)",
                  border: "1px solid var(--border-strong)",
                  borderRadius: "8px",
                  padding: "0.35rem",
                  boxShadow: "0 4px 12px rgba(28, 25, 23, 0.15)",
                  zIndex: 20,
                  minWidth: "210px",
                }}
              >
                {availableModels.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => {
                      setSelectedModel(m);
                      setShowModelMenu(false);
                      therapyStore.setAgentStatus(`Acoustic pipeline switched to: ${m}`);
                    }}
                    style={{
                      display: "block",
                      width: "100%",
                      textAlign: "left",
                      padding: "0.35rem 0.65rem",
                      fontSize: "0.75rem",
                      backgroundColor: selectedModel === m ? "var(--surface-overlay)" : "transparent",
                      color: selectedModel === m ? "var(--text-primary)" : "var(--text-secondary)",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    {m}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Option Pill: VAD Live Preview */}
          <button
            type="button"
            onClick={() => setIsVADPreview(!isVADPreview)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.35rem",
              padding: "0.25rem 0.65rem",
              borderRadius: "9999px",
              backgroundColor: isVADPreview ? "var(--success-bg)" : "var(--surface-overlay)",
              color: isVADPreview ? "var(--success-text)" : "var(--text-secondary)",
              border: isVADPreview ? "1px solid var(--success-border)" : "1px solid var(--border-strong)",
              fontSize: "0.75rem",
              cursor: "pointer",
            }}
          >
            <span>🛡️</span>
            <span>{isVADPreview ? "VAD Active (16kHz)" : "VAD Paused"}</span>
          </button>

          {/* Encryption Badge */}
          <span
            style={{
              fontSize: "0.7rem",
              color: "var(--text-tertiary)",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.25rem",
            }}
          >
            <span>🔒</span>
            <span>AES-256 S3 Enforced</span>
          </span>
        </div>

        {/* Right Toolbar Items: Voice Mic & Submit Arrow Button */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <button
            type="button"
            onClick={() => {
              therapyStore.setAgentStatus(isListening ? "Listening stopped" : "Microphone active");
            }}
            aria-label="Voice input"
            style={{
              background: "none",
              border: "none",
              color: isListening ? "var(--danger-text)" : "var(--text-secondary)",
              cursor: "pointer",
              padding: "0.35rem",
              fontSize: "1.1rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: "9999px",
            }}
            title="Voice prompt recording"
          >
            🎙️
          </button>

          <button
            type="button"
            onClick={() => handleCommandSubmit()}
            disabled={!inputText.trim()}
            aria-label="Submit command"
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: inputText.trim() ? "var(--bg-elevated)" : "var(--surface-overlay)",
              color: "var(--text-primary)",
              border: "1px solid var(--border-strong)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: inputText.trim() ? "pointer" : "default",
              transition: "all 0.15s ease",
            }}
          >
            ➔
          </button>
        </div>
      </div>
    </div>
  );
};
