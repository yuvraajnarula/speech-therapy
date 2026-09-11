import React from "react";
import { useAudioStreamer } from "./protocol/useAudioStreamer";
import { useTherapyStore, therapyStore } from "./store/therapyStore";
import { RoleNavbar } from "./components/RoleNavbar";
import { AudioController } from "./components/AudioController";
import { DualPaneAST } from "./components/DualPaneAST";
import { WordBankExplorer } from "./components/WordBankExplorer";
import { SessionHistoryView } from "./components/SessionHistoryView";

export default function App() {
  const { startStreaming, stopStreaming } = useAudioStreamer();
  const diagnostic = useTherapyStore((s) => s.diagnostic);
  const userRole = useTherapyStore((s) => s.userRole);
  const sourceLanguage = useTherapyStore((s) => s.sourceLanguage);
  const highContrastMode = useTherapyStore((s) => s.highContrastMode);
  const activeTab = useTherapyStore((s) => s.activeTab);

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: highContrastMode ? "#09090b" : "#f8fafc",
        color: highContrastMode ? "#f4f4f5" : "#0f172a",
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
              backgroundColor: highContrastMode ? "#18181b" : "#f1f5f9",
              border: "1px solid #cbd5e1",
              borderRadius: "8px",
              marginBottom: "1.25rem",
              fontSize: "0.8rem",
            }}
          >
            <div>
              <strong>Active Session:</strong> Patient Record <code>#pt_8492</code> | Dialect Track: <code>{sourceLanguage.toUpperCase()}-IN</code>
            </div>
            <div style={{ display: "flex", gap: "1.25rem", color: "#475569" }}>
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
        </main>
      </div>
    </div>
  );
}
