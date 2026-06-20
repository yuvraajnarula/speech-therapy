import { useEffect, useRef, useState } from "react";

const floatTo16BitPCM = (float32array: Float32Array) => {
  const int16Array = new Int16Array(float32array.length);

  for (let i = 0; i < float32array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32array[i]));
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }

  return int16Array.buffer;
};

export function useAudioStreamer() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startStreaming = async () => {
    try {
      // Clear previous transcript when starting a new recording
      setTranscript("");

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      streamRef.current = stream;

      // Open WebSocket connection
      wsRef.current = new WebSocket("ws://localhost:8000/ws/local-therapy");
      wsRef.current.binaryType = "arraybuffer";

      wsRef.current.onopen = () => {
        console.log("WebSocket connected");
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.transcribed !== undefined) {
            // 1. Update the UI with the transcript!
            setTranscript(data.transcribed);

            // 2. NOW it is safe to close the socket
            wsRef.current?.close();
            wsRef.current = null;
          }
        } catch (err) {
          console.error("Error parsing websocket message:", err);
        }
      };

      wsRef.current.onerror = (err) => {
        console.error("WebSocket error:", err);
      };

      wsRef.current.onclose = () => {
        console.log("WebSocket disconnected");
      };

      const AudioContextClass =
        window.AudioContext ||
        (window as typeof window & {
          webkitAudioContext?: typeof AudioContext;
        }).webkitAudioContext;

      if (!AudioContextClass) {
        throw new Error("AudioContext is not supported in this browser.");
      }

      const audioContext = new AudioContextClass({
        sampleRate: 16000,
      });

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
      console.log("Microphone started, speak now.");
    } catch (err) {
      console.error("Microphone access denied or audio error:", err);
      alert("Please allow microphone access to use this app.");
    }
  };

  const stopStreaming = () => {
    processRef.current?.disconnect();
    processRef.current = null;

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            action: "stop",
          })
        );
      }
      
    }

    setIsListening(false);
    console.log("Stop signal sent to backend. Waiting for transcript...");
  };

  useEffect(() => {
    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      stopStreaming();
    };
  }, []);

  return {
    isListening,
    transcript,
    startStreaming,
    stopStreaming,
  };
}