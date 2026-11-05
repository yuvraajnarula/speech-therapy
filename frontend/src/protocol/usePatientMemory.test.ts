import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePatientMemory } from "./usePatientMemory";
import { therapyStore } from "../store/therapyStore";

describe("usePatientMemory", () => {
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
    vi.mocked(global.fetch).mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns null when no patientId", () => {
    const { result } = renderHook(() => usePatientMemory(null, "hi", "token"));
    expect(result.current).toBe(null);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("returns null when no authToken", () => {
    const { result } = renderHook(() => usePatientMemory("p1", "hi", null));
    expect(result.current).toBe(null);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("fetches memory and stores it", async () => {
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
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => memory,
    } as Response);

    const { result } = renderHook(() => usePatientMemory("p1", "hi", "token"));

    // Wait for the async fetch to complete
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/memory/p1?dialect=hi",
      expect.objectContaining({
        headers: { Authorization: "Bearer token" },
      })
    );
    expect(therapyStore.getState().patientMemory).toBe(memory);
  });

  it("does not store memory on non-ok response", async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
      status: 404,
    } as Response);

    const { result } = renderHook(() => usePatientMemory("p1", "hi", "token"));

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    expect(therapyStore.getState().patientMemory).toBe(null);
  });

  it("silently handles fetch errors", async () => {
    vi.mocked(global.fetch).mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => usePatientMemory("p1", "hi", "token"));

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    expect(therapyStore.getState().patientMemory).toBe(null);
  });

  it("returns existing memory from store", () => {
    const memory = {
      patient_id: "p1",
      dialect: "hi",
      phoneme_errors: {},
      mastery_scores: {},
      weak_phonemes_ranked: [],
      recent_utterances: [],
      total_sessions: 1,
      total_attempts: 5,
      consecutive_correct: 3,
      consecutive_incorrect: 0,
      last_updated: "2026-01-01T00:00:00Z",
    };
    therapyStore.setPatientMemory(memory);

    const { result } = renderHook(() => usePatientMemory("p1", "hi", "token"));
    expect(result.current).toBe(memory);
  });
});
