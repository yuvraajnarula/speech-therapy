import { useState } from "react";
import { INDIC_WORD_BANK, speakTargetReference } from "../data/indicWordBank";
import type { ClinicalWordItem } from "../data/indicWordBank";
import { therapyStore } from "../store/therapyStore";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";

interface WordBankExplorerProps {
  onSelectWord?: (word: ClinicalWordItem) => void;
}

export const WordBankExplorer: React.FC<WordBankExplorerProps> = ({ onSelectWord }) => {
  const [selectedLanguage, setSelectedLanguage] = useState<string>("all");
  const [selectedPosition, setSelectedPosition] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [playingId, setPlayingId] = useState<string | null>(null);

  const filteredWords = INDIC_WORD_BANK.filter((item) => {
    if (selectedLanguage !== "all" && item.language !== selectedLanguage) return false;
    if (selectedPosition !== "all" && item.phoneticPosition !== selectedPosition) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        item.romanized.toLowerCase().includes(q) ||
        item.nativeScript.includes(q) ||
        item.englishMeaning.toLowerCase().includes(q) ||
        item.phonemeTarget.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handlePlayAudio = async (item: ClinicalWordItem, rate: number = 1.0) => {
    setPlayingId(item.id);
    await speakTargetReference(item.nativeScript || item.romanized, item.language, rate);
    setPlayingId(null);
  };

  const handleSelectWord = (item: ClinicalWordItem) => {
    therapyStore.setTargetWord(item.romanized);
    therapyStore.setSourceLanguage(item.language);
    if (onSelectWord) {
      onSelectWord(item);
    }
  };

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
      {/* Search and Filters Header */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
          <div>
            <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Indic Speech Articulation Word Bank
            </h3>
            <p style={{ margin: "0.2rem 0 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              AIISH Clinical Guidelines & IndicVoices articulatory targets with native reference audio
            </p>
          </div>
          <Badge variant="secondary">
            {filteredWords.length} targets available
          </Badge>
        </div>

        {/* Filter Controls Bar */}
        <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr", gap: "0.75rem" }}>
          {/* Text Search */}
          <input
            type="text"
            placeholder="Search words (e.g. pani, to, apple, water)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              padding: "0.5rem 0.85rem",
              borderRadius: "6px",
              border: "1px solid var(--border-strong)",
              fontSize: "0.85rem",
              backgroundColor: "var(--bg-canvas)",
              color: "var(--text-primary)",
            }}
          />

          {/* Language Selector */}
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            style={{
              padding: "0.5rem 0.85rem",
              borderRadius: "6px",
              border: "1px solid var(--border-strong)",
              fontSize: "0.85rem",
              backgroundColor: "var(--bg-canvas)",
              color: "var(--text-primary)",
            }}
          >
            <option value="all">All Languages</option>
            <option value="hi">Hindi (हिंदी)</option>
            <option value="kn">Kannada (ಕನ್ನಡ)</option>
            <option value="ta">Tamil (தமிழ்)</option>
            <option value="te">Telugu (తెలుగు)</option>
            <option value="en-IN">Indian English (en-IN)</option>
          </select>

          {/* Phonetic Position */}
          <select
            value={selectedPosition}
            onChange={(e) => setSelectedPosition(e.target.value)}
            style={{
              padding: "0.5rem 0.85rem",
              borderRadius: "6px",
              border: "1px solid var(--border-strong)",
              fontSize: "0.85rem",
              backgroundColor: "var(--bg-canvas)",
              color: "var(--text-primary)",
            }}
          >
            <option value="all">All Positions</option>
            <option value="initial">Initial Sound</option>
            <option value="medial">Medial Sound</option>
            <option value="final">Final Sound</option>
          </select>
        </div>
      </div>

      {/* Word Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "1rem",
          maxHeight: "540px",
          overflowY: "auto",
          paddingRight: "0.25rem",
        }}
      >
        {filteredWords.map((item) => (
          <div
            key={item.id}
            style={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              padding: "1rem",
              borderRadius: "8px",
              border: "1px solid var(--border-subdued)",
              backgroundColor: "var(--bg-canvas)",
              transition: "border-color 0.15s",
            }}
          >
            <div>
              {/* Card Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <Badge variant="outline">
                  {item.language.toUpperCase()} • {item.phoneticPosition}
                </Badge>
                <span style={{ fontSize: "0.7rem", color: "var(--text-tertiary)", fontWeight: 600 }}>
                  Age: {item.developmentalAgeYears}y+
                </span>
              </div>

              {/* Word Display */}
              <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", marginBottom: "0.25rem" }}>
                <span style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  {item.nativeScript}
                </span>
                <span style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                  "{item.romanized}"
                </span>
              </div>

              <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                Meaning: <em>{item.englishMeaning}</em>
              </div>

              {/* IPA and Anatomical Target */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  fontFamily: "ui-monospace, monospace",
                  fontSize: "0.8rem",
                  color: "var(--accent-primary)",
                  marginBottom: "0.5rem",
                }}
              >
                <span>{item.ipa}</span>
                <span style={{ color: "var(--text-secondary)" }}>|</span>
                <span style={{ color: "var(--text-secondary)", fontFamily: "inherit" }}>
                  Target: <strong>{item.phonemeTarget}</strong>
                </span>
              </div>

              <p style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", margin: "0 0 0.85rem", lineHeight: 1.4 }}>
                {item.clinicalCue}
              </p>
            </div>

            {/* Action Buttons */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem", borderTop: "1px solid var(--border-standard)", paddingTop: "0.75rem" }}>
              <div style={{ display: "flex", gap: "0.35rem" }}>
                <button
                  type="button"
                  onClick={() => handlePlayAudio(item, 1.0)}
                  disabled={playingId === item.id}
                  style={{
                    padding: "0.3rem 0.55rem",
                    borderRadius: "4px",
                    border: "1px solid var(--border-subdued)",
                    backgroundColor: "var(--surface-overlay)",
                    color: "var(--pill-text)",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                  }}
                  title="Play standard model reference audio"
                >
                  🔊 1.0x
                </button>
                <button
                  type="button"
                  onClick={() => handlePlayAudio(item, 0.75)}
                  disabled={playingId === item.id}
                  style={{
                    padding: "0.3rem 0.55rem",
                    borderRadius: "4px",
                    border: "1px solid var(--border-subdued)",
                    backgroundColor: "var(--surface-overlay)",
                    color: "var(--pill-text)",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                  }}
                  title="Play slow articulatory model audio"
                >
                  🐢 0.75x
                </button>
              </div>

              <Button
                variant="default"
                size="sm"
                onClick={() => handleSelectWord(item)}
              >
                Select Target ➔
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
