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
  const audioContextRef = useRef<AudioContext | null>(null);
  const processRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startStreaming = async () => {
    try {
      // request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      const AudioContextClass =
        window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass({
        sampleRate: 16000, // gold standard for Automatic Speech Recognition (ASR) and speech processing models like Whisper and Sarvam AI
      });
      audioContextRef.current = audioContext;
      // Buffer size 4096 at 16kHz means we get a chunk every
      // ~256 milliseconds.

      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processRef.current = processor;
      processor.onaudioprocess = (e) => {
        // Extract the raw float32 data from the left channel (since it's mono)
        const float32Data = e.inputBuffer.getChannelData(0);

        // Convert to 16-bit PCM
        const pcm16Data = floatTo16BitPCM(float32Data);

        // FOR NOW: Just log the byte size to the console to prove it's working!
        console.log(`Captured audio chunk: ${pcm16Data.byteLength} bytes`);
      };

      source.connect(processor);
      processor.connect(audioContext.destination);
      setIsListening(true);
      console.log("microphone started, speak now");
    } catch (err) {
      console.error("Microphone access denied or audio error:", err);
      alert("Please allow microphone access to use this app.");
    }
  };

  const stopStreaming = () => {
    //cleanup
    processRef.current?.disconnect();
    audioContextRef.current?.close();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    setIsListening(false);
    console.log("microphone stopped and clean up was successful.");
  };
  useEffect(() => {
    return () => {
      stopStreaming();
    };
  }, []);
  return { isListening, startStreaming, stopStreaming };
}
