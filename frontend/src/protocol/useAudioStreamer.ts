import { useEffect, useRef } from "react";
import { therapyStore, useTherapyStore } from "../store/therapyStore";
import type { DiagnosticResult } from "../store/therapyStore";

const floatTo16BitPCM = (float32array: Float32Array): ArrayBuffer => {
  const int16Array = new Int16Array(float32array.length);
  for (let i = 0; i < float32array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32array[i]));
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return int16Array.buffer;
};

export function useAudioStreamer() {
  const targetWord = useTherapyStore((s) => s.targetWord);
  const sourceLanguage = useTherapyStore((s) => s.sourceLanguage);
  const targetLanguage = useTherapyStore((s) => s.targetLanguage);
  const isListening = useTherapyStore((s) => s.isListening);
  const isProcessing = useTherapyStore((s) => s.isProcessing);
  const diagnostic = useTherapyStore((s) => s.diagnostic);
  const agentStatus = useTherapyStore((s) => s.agentStatus);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const closeWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const startStreaming = async () => {
    closeWebSocket();

    try {
      therapyStore.setDiagnostic(null);
      therapyStore.setAgentStatus("Connecting to Live AST Engine...");
      therapyStore.setIsProcessing(false);

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("MediaDevices API not supported on this browser context.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
      });
      streamRef.current = stream;

      // Connect to WebSocket dynamically based on host and environment
      const isDevPort = window.location.port === "5173";
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = isDevPort
        ? "ws://localhost:8000/ws/live-ast"
        : `${wsProtocol}//${window.location.host}/ws/live-ast`;
      const ws = new WebSocket(wsUrl);
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;

      ws.onopen = () => {
        therapyStore.setAgentStatus("Connected. Listening (16kHz PCM)...");
        ws.send(
          JSON.stringify({
            action: "configure",
            target: targetWord,
            source_language: sourceLanguage,
            target_language: targetLanguage,
          })
        );
      };

      ws.onmessage = (event) => {
        if (typeof event.data === "string" && !event.data.trim().startsWith("{")) {
          therapyStore.setAgentStatus(event.data);
          return;
        }

        try {
          const data: DiagnosticResult = JSON.parse(event.data);
          if (data.type === "diagnostic") {
            therapyStore.setDiagnostic(data);
            therapyStore.setAgentStatus("Analysis complete!");
            therapyStore.setIsProcessing(false);
            closeWebSocket();
          }
        } catch (err) {
          console.error("Error parsing AST response:", err);
        }
      };

      ws.onerror = () => {
        // Fallback gracefully if backend is not started locally
        therapyStore.setAgentStatus("Acoustic engine offline (Use 'Run SODA Trial Simulation' to test offline)");
      };

      ws.onclose = () => {
        if (therapyStore.getState().isProcessing) {
          therapyStore.setIsProcessing(false);
          therapyStore.setAgentStatus("Connection closed.");
        }
      };

      const AudioContextClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioContextClass) throw new Error("Web Audio API not supported");
      const audioContext = new AudioContextClass({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      // 4096 buffer size at 16kHz = ~256ms chunk duration for optimal low latency
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (ws.readyState === WebSocket.OPEN) {
          const float32Data = e.inputBuffer.getChannelData(0);
          const pcm16Data = floatTo16BitPCM(float32Data);
          ws.send(pcm16Data);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);
      therapyStore.setIsListening(true);
    } catch (err) {
      console.warn("Microphone access notice:", (err as Error).message);
      therapyStore.setAgentStatus("Microphone inactive. You can use 'Run SODA Trial Simulation' anytime.");
      therapyStore.setIsListening(false);
    }
  };

  const stopStreaming = () => {
    processRef.current?.disconnect();
    processRef.current = null;
    audioContextRef.current?.close();
    audioContextRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "stop" }));
      therapyStore.setAgentStatus("Analyzing speech with faster-whisper & AST...");
      therapyStore.setIsProcessing(true);
    } else {
      therapyStore.setAgentStatus("Recording stopped.");
    }

    therapyStore.setIsListening(false);
  };

  useEffect(() => {
    return () => {
      processRef.current?.disconnect();
      audioContextRef.current?.close();
      streamRef.current?.getTracks().forEach((track) => track.stop());
      closeWebSocket();
    };
  }, []);

  return {
    isListening,
    isProcessing,
    diagnostic,
    agentStatus,
    startStreaming,
    stopStreaming,
  };
}
