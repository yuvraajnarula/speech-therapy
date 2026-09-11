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
  activeTab: "trial" | "wordbank" | "history";
  hasPatientAudio: boolean;
  trialLogs: TrialLogItem[];
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
  setActiveTab: (tab: "trial" | "wordbank" | "history") => {
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
};

/** React Hook for consuming therapyStore with useSyncExternalStore */
export function useTherapyStore<T>(selector: (state: TherapyState) => T): T {
  return useSyncExternalStore(
    therapyStore.subscribe,
    () => selector(therapyStore.getState()),
    () => selector(initialState)
  );
}
