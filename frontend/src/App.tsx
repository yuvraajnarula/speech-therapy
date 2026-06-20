import { useAudioStreamer } from "./protocol/useAudioStreamer";

export default function App(){
  const {
    isListening,
    startStreaming,
    stopStreaming
  } = useAudioStreamer();

  return (
    <>
      <div>
        <h1>
          Audio Capture MVP
        </h1>
        <p>
          Status: 
          {
            isListening ? ' Listening' : ' Idle'
          }
        </p>
        {!isListening ? (
          <button onClick={startStreaming}>
            Start Listening
          </button>
        ) : (
          <button onClick={stopStreaming}>
            Stop
          </button>
        )}
        <p>
        <strong>Instructions:</strong> Click "Start Speaking", allow mic permissions, and talk. 
        Open your browser console : Press F12 for  Console tab to see the raw audio chunks being captured!
        </p>
      </div>
    </>
  )
}