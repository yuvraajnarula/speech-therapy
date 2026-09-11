import { useEffect, useRef } from "react";
import { therapyStore, useTherapyStore, DiagnosticResult } from "../store/therapyStore";

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

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
      });
      streamRef.current = stream;

      // Connect to WebSocket
      const wsUrl = "ws://localhost:8000/ws/live-ast";
      const ws = new WebSocket(wsUrl);
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;

      ws.onopen = () => {
        therapyStore.setAgentStatus("Connected. Listening...");
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

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        therapyStore.setAgentStatus("Connection error");
      };

      ws.onclose = () => {
        if (therapyStore.getState().isProcessing) {
          therapyStore.setIsProcessing(false);
          therapyStore.setAgentStatus("Connection closed.");
        }
      };

      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
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
      console.error("Microphone error:", err);
      therapyStore.setAgentStatus("Microphone access denied");
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