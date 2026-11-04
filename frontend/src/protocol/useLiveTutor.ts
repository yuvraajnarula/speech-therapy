/**
 * useLiveTutor — WebSocket hook for the Live Tutor adaptive coaching loop.
 *
 * Connects to /ws/live-tutor and manages the full session lifecycle:
 *  - start(patientId, dialect)       → initialise session, receive first TutorCue
 *  - submitAudio(pcmChunks)          → stream PCM + trigger submit
 *  - stop()                          → end session gracefully
 *
 * Server messages (type):
 *  connected   → initial handshake
 *  tutor_cue   → next drill target
 *  feedback    → diagnostic + encouragement + next_cue + memory_snapshot
 *  session_complete → final score
 *  error       → server-side error
 */
import { useCallback, useEffect, useRef, useState } from "react";
import type { TutorCue } from "../store/therapyStore";
import { therapyStore } from "../store/therapyStore";

type TutorStatus = "idle" | "connecting" | "active" | "complete" | "error";

const WS_BASE =
  window.location.protocol === "https:"
    ? `wss://${window.location.host}`
    : window.location.hostname === "localhost"
    ? "ws://localhost:8000"
    : `ws://${window.location.host}`;

export function useLiveTutor(authToken: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<TutorStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // -------------------------------------------------------------------------
  // Connection lifecycle
  // -------------------------------------------------------------------------

  const connect = useCallback(() => {
    const url = authToken
      ? `${WS_BASE}/ws/live-tutor?token=${encodeURIComponent(authToken)}`
      : `${WS_BASE}/ws/live-tutor`;

    const ws = new WebSocket(url);
    wsRef.current = ws;
    setStatus("connecting");

    ws.onopen = () => setStatus("connecting"); // wait for 'connected' message

    ws.onmessage = (evt) => {
      let msg: Record<string, unknown>;
      try {
        msg = JSON.parse(evt.data as string) as Record<string, unknown>;
      } catch {
        return;
      }

      const type = msg.type as string;

      if (type === "connected") {
        setStatus("active");
      } else if (type === "tutor_cue") {
        therapyStore.setTutorSession({
          status: "active",
          currentCue: msg as unknown as TutorCue,
          encouragement: "",
        });
      } else if (type === "feedback") {
        const nextCue = msg.next_cue as TutorCue | undefined;
        therapyStore.setTutorSession({
          status: "active",
          currentCue: nextCue ?? null,
          encouragement: (msg.encouragement as string) ?? "",
          sessionScore: msg.session_score as { correct: number; total: number },
          memorySnapshot: msg.memory_snapshot as {
            weak_phonemes: string[];
            consecutive_correct: number;
            consecutive_incorrect: number;
            total_attempts: number;
          },
        });
      } else if (type === "session_complete") {
        therapyStore.setTutorSession({
          status: "complete",
          sessionScore: msg.session_score as { correct: number; total: number },
          encouragement: (msg.message as string) ?? "Session complete!",
        });
        setStatus("complete");
      } else if (type === "error") {
        setError((msg.message as string) ?? "Unknown tutor error");
        setStatus("error");
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection error");
      setStatus("error");
    };

    ws.onclose = () => {
      if (status !== "complete") setStatus("idle");
    };
  }, [authToken, status]);

  // -------------------------------------------------------------------------
  // Session control
  // -------------------------------------------------------------------------

  const start = useCallback(
    (patientId: string, dialect: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connect();
        // Wait for open before sending start
        const tryStart = () => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(
              JSON.stringify({ action: "start", patient_id: patientId, dialect })
            );
          } else {
            setTimeout(tryStart, 100);
          }
        };
        setTimeout(tryStart, 200);
      } else {
        wsRef.current.send(
          JSON.stringify({ action: "start", patient_id: patientId, dialect })
        );
      }
      therapyStore.setTutorSession({ status: "active" });
    },
    [connect]
  );

  const startRecording = useCallback(async () => {
    if (isRecording) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mr;
      setIsRecording(true);

      mr.ondataavailable = (evt) => {
        if (evt.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          evt.data.arrayBuffer().then((buf) => {
            wsRef.current?.send(buf);
          });
        }
      };
      mr.start(250); // 250ms chunks
    } catch {
      setError("Microphone access denied");
    }
  }, [isRecording]);

  const stopAndSubmit = useCallback(() => {
    if (!isRecording) return;
    mediaRecorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setIsRecording(false);
    // Signal server to process
    wsRef.current?.send(JSON.stringify({ action: "submit" }));
  }, [isRecording]);

  const stop = useCallback(() => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      setIsRecording(false);
    }
    wsRef.current?.send(JSON.stringify({ action: "stop" }));
    setStatus("idle");
    therapyStore.resetTutorSession();
  }, [isRecording]);

  // -------------------------------------------------------------------------
  // Cleanup
  // -------------------------------------------------------------------------

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  return {
    status,
    error,
    isRecording,
    connect,
    start,
    startRecording,
    stopAndSubmit,
    stop,
  };
}
