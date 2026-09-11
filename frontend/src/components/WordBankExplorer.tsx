import React, { useState } from "react";
import { INDIC_WORD_BANK, ClinicalWordItem, speakTargetReference } from "../data/indicWordBank";
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
    therapyStore.setSourceLanguage(item.language === "en-IN" ? "en" : item.language);
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
        backgroundColor: "#ffffff",
        borderRadius: "12px",
        border: "1px solid #e2e8f0",
        padding: "1.5rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}
    >
      {/* Search and Filters Header */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
          <div>
            <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "#0f172a" }}>
              Indic Speech Articulation Word Bank
            </h3>
            <p style={{ margin: "0.2rem 0 0", fontSize: "0.8rem", color: "#64748b" }}>
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
              border: "1px solid #cbd5e1",
              fontSize: "0.85rem",
              color: "#0f172a",
            }}
          />

          {/* Language Selector */}
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            style={{
              padding: "0.5rem 0.85rem",
              borderRadius: "6px",
              border: "1px solid #cbd5e1",
              fontSize: "0.85rem",
              backgroundColor: "#ffffff",
              color: "#0f172a",
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
              border: "1px solid #cbd5e1",
              fontSize: "0.85rem",
              backgroundColor: "#ffffff",
              color: "#0f172a",
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
              border: "1px solid #e2e8f0",
              backgroundColor: "#f8fafc",
              transition: "border-color 0.15s",
            }}
          >
            <div>
              {/* Card Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <Badge variant="outline">
                  {item.language.toUpperCase()} • {item.phoneticPosition}
                </Badge>
                <span style={{ fontSize: "0.7rem", color: "#64748b", fontWeight: 600 }}>
                  Age: {item.developmentalAgeYears}y+
                </span>
              </div>

              {/* Word Display */}
              <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", marginBottom: "0.25rem" }}>
                <span style={{ fontSize: "1.5rem", fontWeight: 700, color: "#0f172a" }}>
                  {item.nativeScript}
                </span>
                <span style={{ fontSize: "1rem", fontWeight: 600, color: "#475569" }}>
                  "{item.romanized}"
                </span>
              </div>

              <div style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "0.5rem" }}>
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
                  color: "#2563eb",
                  marginBottom: "0.5rem",
                }}
              >
                <span>{item.ipa}</span>
                <span style={{ color: "#cbd5e1" }}>|</span>
                <span style={{ color: "#64748b", fontFamily: "inherit" }}>
                  Target: <strong>{item.phonemeTarget}</strong>
                </span>
              </div>

              {/* Clinical Cue */}
              <p
                style={{
                  fontSize: "0.75rem",
                  color: "#475569",
                  backgroundColor: "#ffffff",
                  padding: "0.45rem 0.6rem",
                  borderRadius: "4px",
                  border: "1px solid #e2e8f0",
                  lineHeight: 1.4,
                  margin: "0.5rem 0",
                }}
              >
                💡 <strong>Cue:</strong> {item.clinicalCue}
              </p>
            </div>

            {/* Actions Bar */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "0.75rem", paddingTop: "0.5rem", borderTop: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", gap: "0.35rem" }}>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePlayAudio(item, 1.0)}
                  disabled={playingId === item.id}
                  title="Hear model standard pronunciation"
                >
                  🔊 1.0x
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePlayAudio(item, 0.75)}
                  disabled={playingId === item.id}
                  title="Hear slow articulatory drill"
                >
                  🐢 0.75x
                </Button>
              </div>

              <Button
                variant="default"
                size="sm"
                onClick={() => handleSelectWord(item)}
              >
                Practice ➔
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
