import { useSyncExternalStore } from "react";

export interface DiagnosticError {
  type: string;
  target_slice: string;
  spoken_slice: string;
}

export interface DiagnosticResult {
  type: string;
  target: string;
  spoken: string;
  source_language?: string;
  target_language?: string;
  translated_text?: string;
  target_phonemes: string;
  spoken_phonemes: string;
  is_correct: boolean;
  target_achieved: boolean;
  accuracy_score?: number;
  errors: DiagnosticError[];
  clinical_feedback?: string;
}

export interface TrialLogItem {
  id: string;
  targetWord: string;
  cueLevel: "independent" | "verbal" | "visual" | "tactile";
  rating: "correct" | "approx" | "incorrect";
  score: number;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// Memory Layer types
// ---------------------------------------------------------------------------
export interface PatientMemory {
  patient_id: string;
  dialect: string;
  phoneme_errors: Record<string, number>;
  mastery_scores: Record<string, number>;
  weak_phonemes_ranked: string[];
  recent_utterances: Array<Record<string, unknown>>;
  total_sessions: number;
  total_attempts: number;
  consecutive_correct: number;
  consecutive_incorrect: number;
  last_updated: string;
}

// ---------------------------------------------------------------------------
// Live Tutor types
// ---------------------------------------------------------------------------
export interface TutorCue {
  target_word: string;
  phoneme_target: string;
  cue_text: string;
  native_script: string;
  ipa: string;
  category: string;
}

export interface TutorSession {
  status: "idle" | "active" | "complete";
  currentCue: TutorCue | null;
  sessionScore: { correct: number; total: number };
  encouragement: string;
  memorySnapshot: {
    weak_phonemes: string[];
    consecutive_correct: number;
    consecutive_incorrect: number;
    total_attempts: number;
  } | null;
}

export interface TherapyState {
  userRole: "therapist" | "patient";
  targetWord: string;
  sourceLanguage: "hi" | "kn" | "ta" | "te" | "en-IN";
  targetLanguage: "en" | "hi";
  isListening: boolean;
  isProcessing: boolean;
  agentStatus: string;
  diagnostic: DiagnosticResult | null;
  highContrastMode: boolean;
  activeTab: "trial" | "wordbank" | "history" | "tutor";
  hasPatientAudio: boolean;
  trialLogs: TrialLogItem[];
  patientMemory: PatientMemory | null;
  tutorSession: TutorSession;
}

const initialState: TherapyState = {
  userRole: "therapist",
  targetWord: "pani",
  sourceLanguage: "hi",
  targetLanguage: "en",
  isListening: false,
  isProcessing: false,
  agentStatus: "Ready",
  diagnostic: null,
  highContrastMode: false,
  activeTab: "trial",
  hasPatientAudio: false,
  trialLogs: [],
  patientMemory: null,
  tutorSession: {
    status: "idle",
    currentCue: null,
    sessionScore: { correct: 0, total: 0 },
    encouragement: "",
    memorySnapshot: null,
  },
};

let state: TherapyState = { ...initialState };
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((l) => l());
}

export const therapyStore = {
  getState: () => state,
  setState: (updater: Partial<TherapyState> | ((prev: TherapyState) => Partial<TherapyState>)) => {
    const patch = typeof updater === "function" ? updater(state) : updater;
    state = { ...state, ...patch };
    notify();
  },
  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  // Helper actions
  setUserRole: (role: "therapist" | "patient") => {
    therapyStore.setState({ userRole: role });
  },
  setTargetWord: (word: string) => {
    therapyStore.setState({ targetWord: word });
  },
  setSourceLanguage: (lang: "hi" | "kn" | "ta" | "te" | "en-IN") => {
    therapyStore.setState({ sourceLanguage: lang });
  },
  setTargetLanguage: (lang: "en" | "hi") => {
    therapyStore.setState({ targetLanguage: lang });
  },
  setIsListening: (isListening: boolean) => {
    therapyStore.setState({ isListening });
  },
  setIsProcessing: (isProcessing: boolean) => {
    therapyStore.setState({ isProcessing });
  },
  setAgentStatus: (agentStatus: string) => {
    therapyStore.setState({ agentStatus });
  },
  setDiagnostic: (diagnostic: DiagnosticResult | null) => {
    therapyStore.setState({ diagnostic, hasPatientAudio: !!diagnostic });
  },
  setHasPatientAudio: (hasAudio: boolean) => {
    therapyStore.setState({ hasPatientAudio: hasAudio });
  },
  setActiveTab: (tab: "trial" | "wordbank" | "history" | "tutor") => {
    therapyStore.setState({ activeTab: tab });
  },
  addTrialLog: (log: TrialLogItem) => {
    therapyStore.setState((prev) => ({ trialLogs: [...prev.trialLogs, log] }));
  },
  clearTrialLogs: () => {
    therapyStore.setState({ trialLogs: [] });
  },
  toggleHighContrast: () => {
    therapyStore.setState((prev) => ({ highContrastMode: !prev.highContrastMode }));
  },
  resetSession: () => {
    therapyStore.setState({
      diagnostic: null,
      isListening: false,
      isProcessing: false,
      hasPatientAudio: false,
      agentStatus: "Ready",
    });
  },

  // Memory layer
  setPatientMemory: (memory: PatientMemory | null) => {
    therapyStore.setState({ patientMemory: memory });
  },

  // Live Tutor
  setTutorSession: (patch: Partial<TutorSession>) => {
    therapyStore.setState((prev) => ({
      tutorSession: { ...prev.tutorSession, ...patch },
    }));
  },
  resetTutorSession: () => {
    therapyStore.setState({
      tutorSession: {
        status: "idle",
        currentCue: null,
        sessionScore: { correct: 0, total: 0 },
        encouragement: "",
        memorySnapshot: null,
      },
    });
  },
};

/** React Hook for consuming therapyStore with useSyncExternalStore */
export function useTherapyStore<T>(selector: (state: TherapyState) => T): T {
  return useSyncExternalStore(
    therapyStore.subscribe,
    () => selector(therapyStore.getState()),
    () => selector(initialState)
  );
}
