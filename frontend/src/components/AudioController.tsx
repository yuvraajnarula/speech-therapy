import { useEffect } from "react";
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
    (w) => w.language === sourceLanguage
  ).slice(0, 5);

  // Clinical Demo Simulation for offline / test environments
  const handleSimulateTrial = () => {
    therapyStore.setIsProcessing(true);
    therapyStore.setAgentStatus("Simulating acoustic alignment & SODA matrix...");

    setTimeout(() => {
      const isClean = Math.random() > 0.35;
      const targetPhonemes = matchedItem ? matchedItem.phonemeArray.join("") : targetWord.toUpperCase();

      if (isClean) {
        therapyStore.setDiagnostic({
          type: "diagnostic",
          target: targetWord,
          spoken: targetWord,
          target_phonemes: targetPhonemes,
          spoken_phonemes: targetPhonemes,
          is_correct: true,
          target_achieved: true,
          accuracy_score: 95,
          errors: [],
          clinical_feedback: "Optimal articulatory placement observed. Acoustic energy and duration meet clinical target thresholds.",
          translated_text: matchedItem?.englishMeaning || targetWord,
        });
      } else {
        const errorPhoneme = matchedItem ? matchedItem.phonemeArray[0] : "P";
        therapyStore.setDiagnostic({
          type: "diagnostic",
          target: targetWord,
          spoken: targetWord.slice(0, -1) + "a",
          target_phonemes: targetPhonemes,
          spoken_phonemes: targetPhonemes.replace(errorPhoneme, "T"),
          is_correct: false,
          target_achieved: false,
          accuracy_score: 68,
          errors: [
            {
              type: "replace",
              target_slice: errorPhoneme,
              spoken_slice: "T",
            },
          ],
          clinical_feedback: `Articulatory Deviation: Substitution error detected on /${errorPhoneme}/ target. Tongue posture or lip closure deviated towards alveolar tap.`,
          translated_text: matchedItem?.englishMeaning || targetWord,
        });
      }

      therapyStore.setIsProcessing(false);
      therapyStore.setAgentStatus("Clinical analysis complete.");
    }, 600);
  };

  return (
    <section
      aria-label="Speech exercise controls"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        backgroundColor: "var(--surface-overlay)",
        padding: "1.5rem",
        borderRadius: "12px",
        boxShadow: "0 2px 6px rgba(28, 25, 23, 0.10)",
        border: "1px solid var(--border-subdued)",
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
          backgroundColor: "var(--bg-canvas)",
          border: "1px solid var(--border-subdued)",
          borderRadius: "8px",
          padding: "1.15rem 1.25rem",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-secondary)", letterSpacing: "0.04em" }}>
              Active Target Stimulus
            </span>
            {matchedItem && (
              <Badge variant="secondary">
                {matchedItem.phonemeTarget} • {matchedItem.phoneticPosition} sound
              </Badge>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "baseline", gap: "0.75rem", flexWrap: "wrap" }}>
            {matchedItem?.nativeScript && (
              <span style={{ fontSize: "2.35rem", fontWeight: 800, color: "var(--text-primary)" }}>
                {matchedItem.nativeScript}
              </span>
            )}
            <span style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--accent-primary)" }}>
              "{targetWord}"
            </span>
            {matchedItem && (
              <span style={{ fontSize: "0.95rem", color: "var(--text-secondary)" }}>
                ({matchedItem.englishMeaning})
              </span>
            )}
          </div>

          {matchedItem && (
            <div style={{ fontSize: "0.8rem", color: "var(--text-tertiary)", marginTop: "0.35rem" }}>
              IPA: <code style={{ color: "var(--accent-primary)", fontWeight: 600, backgroundColor: "var(--surface-overlay)", padding: "2px 6px", borderRadius: "4px" }}>{matchedItem.ipa}</code> — {matchedItem.clinicalCue}
            </div>
          )}
        </div>

        {/* Custom target input & bank explorer quick jump */}
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
              border: "1px solid var(--border-strong)",
              backgroundColor: "var(--bg-canvas)",
              color: "var(--text-primary)",
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
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-tertiary)", textTransform: "uppercase" }}>
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
                border: targetWord.toLowerCase() === item.romanized.toLowerCase() ? "1px solid var(--accent-primary)" : "1px solid var(--border-subdued)",
                backgroundColor: targetWord.toLowerCase() === item.romanized.toLowerCase() ? "var(--surface-overlay)" : "var(--bg-canvas)",
                color: targetWord.toLowerCase() === item.romanized.toLowerCase() ? "var(--text-primary)" : "var(--text-secondary)",
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <span>{item.nativeScript}</span>
              <span style={{ fontWeight: 400, color: "var(--text-tertiary)" }}>({item.romanized})</span>
            </button>
          ))}
        </div>
      )}

      {/* Recording PTT Button & Action Bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          {!isListening && !isProcessing ? (
            <button
              type="button"
              onClick={onStart}
              aria-label={`Start speaking target ${targetWord}`}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.6rem",
                padding: "0.75rem 1.75rem",
                backgroundColor: "var(--surface-overlay)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-strong)",
                borderRadius: "9999px",
                fontSize: "0.95rem",
                fontWeight: 600,
                cursor: "pointer",
                boxShadow: "0 2px 4px rgba(28, 25, 23, 0.10)",
                transition: "all 0.15s ease",
              }}
            >
              <span style={{ fontSize: "1.1rem" }}>🎙️</span>
              <span>Start Speaking "{targetWord}"</span>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginLeft: "0.25rem" }}>[Space]</span>
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
                gap: "0.6rem",
                padding: "0.75rem 1.75rem",
                backgroundColor: "var(--danger-bg)",
                color: "var(--danger-text)",
                border: "1px solid var(--danger-border)",
                borderRadius: "9999px",
                fontSize: "0.95rem",
                fontWeight: 600,
                cursor: "pointer",
                animation: isListening ? "pulse 1.8s infinite" : "none",
              }}
            >
              <span style={{ fontSize: "1.1rem" }}>⏹️</span>
              <span>Stop & Analyze Pronunciation</span>
            </button>
          )}

          {/* Quick Demo Simulator button for seamless testing */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleSimulateTrial}
            disabled={isListening || isProcessing}
            title="Run simulated acoustic analysis with SODA matrix and clinical alignment"
          >
            ✨ Run SODA Trial Simulation
          </Button>
        </div>

        {/* Engine Pipeline Status Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", textTransform: "uppercase", fontWeight: 700 }}>
            Pipeline Status:
          </span>
          <Badge variant={isListening ? "warning" : isProcessing ? "secondary" : "default"}>
            {agentStatus}
          </Badge>
        </div>
      </div>
    </section>
  );
};
