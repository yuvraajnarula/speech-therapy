import { useEffect, useRef, useState } from "react";

export interface DiagnosticResult {
  type: string;
  target: string;
  spoken: string;
  target_phonemes: string;
  spoken_phonemes: string;
  is_correct: boolean;
  target_achieved: boolean;
  errors: { type: string; target_slice: string; spoken_slice: string; }[];
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
  const [isProcessing, setIsProcessing] = useState(false); 
  const [diagnostic, setDiagnostic] = useState<DiagnosticResult | null>(null);
  const [agentStatus, setAgentStatus] = useState<string>("");

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
      setDiagnostic(null);
      setAgentStatus("Connecting to Agent...");
      setIsProcessing(false);
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      streamRef.current = stream;

      const ws = new WebSocket("ws://localhost:8000/ws/agent-therapy");
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connected to Agent");
        ws.send(JSON.stringify({ action: "set_target", target: targetText }));
      };

      ws.onmessage = (event) => {
        if (typeof event.data === 'string' && !event.data.trim().startsWith('{')) {
          setAgentStatus(event.data);
          return; 
        }

        try {
          const data: DiagnosticResult = JSON.parse(event.data);
          if (data.type === 'diagnostic') { 
            setDiagnostic(data);
            setAgentStatus("Analysis complete!");
            setIsProcessing(false);
            closeWebSocket(); // Safely close now that we have the result
          }
        } catch (err) {
          console.error("Error parsing websocket JSON:", err);
        }
      };

      ws.onerror = (err) => console.error("WebSocket error:", err);
      
      ws.onclose = () => {
        console.log("WebSocket closed");
        if (isProcessing) {
          setIsProcessing(false);
          setAgentStatus("Connection lost.");
        }
      };

      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
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
      setAgentStatus("Processing audio...");
      setIsProcessing(true); // 🚨 LOCK THE UI
    }
    
    setIsListening(false);
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
    stopStreaming 
  };
}