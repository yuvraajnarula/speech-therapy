import { describe, it, expect, beforeEach, vi } from "vitest";
import { therapyStore, type TherapyState } from "./therapyStore";

describe("therapyStore", () => {
  beforeEach(() => {
    therapyStore.setState({
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
    });
  });

  it("initial state has expected defaults", () => {
    const state = therapyStore.getState();
    expect(state.userRole).toBe("therapist");
    expect(state.targetWord).toBe("pani");
    expect(state.sourceLanguage).toBe("hi");
    expect(state.activeTab).toBe("trial");
    expect(state.tutorSession.status).toBe("idle");
    expect(state.tutorSession.sessionScore).toEqual({ correct: 0, total: 0 });
  });

  it("setUserRole updates role", () => {
    therapyStore.setUserRole("patient");
    expect(therapyStore.getState().userRole).toBe("patient");
  });

  it("setTargetWord updates target word", () => {
    therapyStore.setTargetWord("namaste");
    expect(therapyStore.getState().targetWord).toBe("namaste");
  });

  it("setSourceLanguage updates source language", () => {
    therapyStore.setSourceLanguage("ta");
    expect(therapyStore.getState().sourceLanguage).toBe("ta");
  });

  it("setTargetLanguage updates target language", () => {
    therapyStore.setTargetLanguage("hi");
    expect(therapyStore.getState().targetLanguage).toBe("hi");
  });

  it("setIsListening toggles listening state", () => {
    therapyStore.setIsListening(true);
    expect(therapyStore.getState().isListening).toBe(true);
    therapyStore.setIsListening(false);
    expect(therapyStore.getState().isListening).toBe(false);
  });

  it("setIsProcessing toggles processing state", () => {
    therapyStore.setIsProcessing(true);
    expect(therapyStore.getState().isProcessing).toBe(true);
  });

  it("setAgentStatus updates agent status", () => {
    therapyStore.setAgentStatus("Listening...");
    expect(therapyStore.getState().agentStatus).toBe("Listening...");
  });

  it("setDiagnostic sets diagnostic and hasPatientAudio", () => {
    const diagnostic = {
      type: "diagnostic",
      target: "namaste",
      spoken: "namaste",
      target_phonemes: "nʌmʌsteɪ",
      spoken_phonemes: "nʌmʌsteɪ",
      is_correct: true,
      target_achieved: true,
      errors: [],
    } as any;
    therapyStore.setDiagnostic(diagnostic);
    const state = therapyStore.getState();
    expect(state.diagnostic).toBe(diagnostic);
    expect(state.hasPatientAudio).toBe(true);
  });

  it("setDiagnostic with null clears hasPatientAudio", () => {
    therapyStore.setDiagnostic({ type: "diagnostic", target: "x", spoken: "x", target_phonemes: "", spoken_phonemes: "", is_correct: false, target_achieved: false, errors: [] } as any);
    therapyStore.setDiagnostic(null);
    expect(therapyStore.getState().diagnostic).toBe(null);
    expect(therapyStore.getState().hasPatientAudio).toBe(false);
  });

  it("setActiveTab updates active tab", () => {
    therapyStore.setActiveTab("tutor");
    expect(therapyStore.getState().activeTab).toBe("tutor");
  });

  it("addTrialLog appends to trialLogs", () => {
    therapyStore.addTrialLog({
      id: "1",
      targetWord: "pani",
      cueLevel: "independent",
      rating: "correct",
      score: 100,
      timestamp: "2026-01-01T00:00:00Z",
    });
    expect(therapyStore.getState().trialLogs).toHaveLength(1);
    therapyStore.addTrialLog({
      id: "2",
      targetWord: "namaste",
      cueLevel: "verbal",
      rating: "approx",
      score: 75,
      timestamp: "2026-01-01T00:01:00Z",
    });
    expect(therapyStore.getState().trialLogs).toHaveLength(2);
  });

  it("clearTrialLogs empties trialLogs", () => {
    therapyStore.addTrialLog({
      id: "1",
      targetWord: "pani",
      cueLevel: "independent",
      rating: "correct",
      score: 100,
      timestamp: "2026-01-01T00:00:00Z",
    });
    therapyStore.clearTrialLogs();
    expect(therapyStore.getState().trialLogs).toHaveLength(0);
  });

  it("toggleHighContrast flips highContrastMode", () => {
    expect(therapyStore.getState().highContrastMode).toBe(false);
    therapyStore.toggleHighContrast();
    expect(therapyStore.getState().highContrastMode).toBe(true);
    therapyStore.toggleHighContrast();
    expect(therapyStore.getState().highContrastMode).toBe(false);
  });

  it("resetSession resets listening/processing/diagnostic/audio/status", () => {
    therapyStore.setIsListening(true);
    therapyStore.setIsProcessing(true);
    therapyStore.setDiagnostic({ type: "diagnostic", target: "x", spoken: "x", target_phonemes: "", spoken_phonemes: "", is_correct: false, target_achieved: false, errors: [] } as any);
    therapyStore.setAgentStatus("Processing...");
    therapyStore.resetSession();
    const s = therapyStore.getState();
    expect(s.isListening).toBe(false);
    expect(s.isProcessing).toBe(false);
    expect(s.diagnostic).toBe(null);
    expect(s.hasPatientAudio).toBe(false);
    expect(s.agentStatus).toBe("Ready");
  });

  it("setPatientMemory stores memory", () => {
    const memory = {
      patient_id: "p1",
      dialect: "hi",
      phoneme_errors: {},
      mastery_scores: {},
      weak_phonemes_ranked: [],
      recent_utterances: [],
      total_sessions: 0,
      total_attempts: 0,
      consecutive_correct: 0,
      consecutive_incorrect: 0,
      last_updated: "2026-01-01T00:00:00Z",
    };
    therapyStore.setPatientMemory(memory);
    expect(therapyStore.getState().patientMemory).toBe(memory);
  });

  it("setTutorSession merges partial tutor session", () => {
    therapyStore.setTutorSession({ status: "active", encouragement: "Great job!" });
    const s = therapyStore.getState().tutorSession;
    expect(s.status).toBe("active");
    expect(s.encouragement).toBe("Great job!");
    expect(s.sessionScore).toEqual({ correct: 0, total: 0 });
  });

  it("resetTutorSession resets tutor session to idle", () => {
    therapyStore.setTutorSession({ status: "complete", sessionScore: { correct: 5, total: 10 } });
    therapyStore.resetTutorSession();
    const s = therapyStore.getState().tutorSession;
    expect(s.status).toBe("idle");
    expect(s.currentCue).toBe(null);
    expect(s.sessionScore).toEqual({ correct: 0, total: 0 });
    expect(s.encouragement).toBe("");
    expect(s.memorySnapshot).toBe(null);
  });

  it("notify calls subscribers", () => {
    const listener = vi.fn();
    therapyStore.subscribe(listener);
    therapyStore.setTargetWord("test");
    expect(listener).toHaveBeenCalled();
  });

  it("subscribe returns unsubscribe function", () => {
    const listener = vi.fn();
    const unsubscribe = therapyStore.subscribe(listener);
    unsubscribe();
    therapyStore.setTargetWord("test");
    expect(listener).not.toHaveBeenCalled();
  });
});
