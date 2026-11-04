import { useEffect } from "react";
import { useAudioStreamer } from "./protocol/useAudioStreamer";
import { useTherapyStore, therapyStore } from "./store/therapyStore";
import { RoleNavbar } from "./components/RoleNavbar";
import { AudioController } from "./components/AudioController";
import { DualPaneAST } from "./components/DualPaneAST";
import { WordBankExplorer } from "./components/WordBankExplorer";
import { SessionHistoryView } from "./components/SessionHistoryView";
import { ClinicalCommandBar } from "./components/ClinicalCommandBar";
import LiveTutorMode from "./components/LiveTutorMode";

export default function App() {
  const { startStreaming, stopStreaming } = useAudioStreamer();
  const diagnostic = useTherapyStore((s) => s.diagnostic);
  const userRole = useTherapyStore((s) => s.userRole);
  const sourceLanguage = useTherapyStore((s) => s.sourceLanguage);
  const highContrastMode = useTherapyStore((s) => s.highContrastMode);
  const activeTab = useTherapyStore((s) => s.activeTab);

  // Deep-link support: /?tab=tutor|trial|wordbank|history
  useEffect(() => {
    const tab = new URLSearchParams(window.location.search).get("tab");
    if (tab === "trial" || tab === "wordbank" || tab === "history" || tab === "tutor") {
      therapyStore.setActiveTab(tab);
    }
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: highContrastMode ? "var(--input-surface)" : "var(--bg-canvas)",
        color: "var(--text-primary)",
        fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "0 1.5rem 3rem" }}>
        {/* Navigation & Clinical Controls */}
        <RoleNavbar />

        {/* Clinician Telemetry Banner (Visible in Therapist HUD) */}
        {userRole === "therapist" && (
          <aside
            aria-label="Clinical telemetry bar"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "0.75rem",
              padding: "0.65rem 1.25rem",
              backgroundColor: highContrastMode ? "var(--bg-canvas)" : "var(--surface-overlay)",
              border: "1px solid var(--border-subdued)",
              borderRadius: "8px",
              marginBottom: "1.25rem",
              fontSize: "0.8rem",
            }}
          >
            <div>
              <strong style={{ color: "var(--bg-elevated)" }}>Active Session:</strong> Patient Record <code style={{ backgroundColor: "var(--bg-canvas)", padding: "2px 6px", borderRadius: "4px", color: "var(--accent-primary)" }}>#pt_8492</code> | Dialect Track: <code style={{ backgroundColor: "var(--bg-canvas)", padding: "2px 6px", borderRadius: "4px", color: "var(--accent-primary)" }}>{sourceLanguage.toUpperCase()}-IN</code>
            </div>
            <div style={{ display: "flex", gap: "1.25rem", color: "var(--text-secondary)" }}>
              <span>🔒 <strong>Storage:</strong> AES-256 S3 Encrypted</span>
              <span>⚡ <strong>VAD:</strong> Silero 16kHz Real-time</span>
              <span>🧠 <strong>Model:</strong> faster-whisper + IndicTrans2</span>
            </div>
          </aside>
        )}

        {/* Dynamic Tab Body */}
        <main>
          {activeTab === "trial" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <AudioController onStart={startStreaming} onStop={stopStreaming} />
              <DualPaneAST diagnostic={diagnostic} />
            </div>
          )}

          {activeTab === "wordbank" && (
            <WordBankExplorer
              onSelectWord={() => {
                therapyStore.setActiveTab("trial");
              }}
            />
          )}

          {activeTab === "history" && (
            <SessionHistoryView />
          )}

          {activeTab === "tutor" && <LiveTutorMode />}
        </main>

        {/* Interactive Bottom Command & Chat Capsule Bar (design.md §3.3) */}
        <ClinicalCommandBar />
      </div>
    </div>
  );
}
