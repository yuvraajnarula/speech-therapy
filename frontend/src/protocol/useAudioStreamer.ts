import { useEffect, useRef, useState } from "react";

export interface DiagnosticResult {
  target: string;
  spoken: string;
  target_phonemes: string;
  spoken_phonemes: string;
  is_correct: boolean;
  target_achieved: boolean; 
  errors: {
    type: string;
    target_slice: string;
    spoken_slice: string;
  }[];
}

const floatTo16BitPCM = (float32array: Float32Array) => {
  const int16Array = new Int16Array(float32array.length);
  for (let i = 0; i < float32array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32array[i]));
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return int16Array.buffer;
};

export function useAudioStreamer(targetText: string) {
  const [isListening, setIsListening] = useState(false);
  const [diagnostic, setDiagnostic] = useState<DiagnosticResult | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startStreaming = async () => {
    try {
      setDiagnostic(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      streamRef.current = stream;

      wsRef.current = new WebSocket("ws://localhost:8000/ws/local-therapy");
      wsRef.current.binaryType = "arraybuffer";

      wsRef.current.onopen = () => {
        console.log("WebSocket connected");
        wsRef.current?.send(JSON.stringify({ action: "set_target", target: targetText }));
      };

      wsRef.current.onmessage = (event) => {
        console.log("RAW WS DATA:", event.data);
        try {
          const data: DiagnosticResult = JSON.parse(event.data);
          
          if (data.target !== undefined) { 
            console.log("PARSED DIAGNOSTIC:", data);
            setDiagnostic(data);
            wsRef.current?.close();
            wsRef.current = null;
          }
        } catch (err) {
          console.error("Error parsing websocket message:", err);
        }
      };

      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const float32Data = e.inputBuffer.getChannelData(0);
          const pcm16Data = floatTo16BitPCM(float32Data);
          wsRef.current.send(pcm16Data);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);
      setIsListening(true);
    } catch (err) {
      console.error("Microphone error:", err);
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
    }
    setIsListening(false);
  };

  useEffect(() => {
    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, []);

  return { isListening, diagnostic, startStreaming, stopStreaming };
}