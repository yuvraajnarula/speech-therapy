import { useState } from "react";
import { useAudioStreamer } from "./protocol/useAudioStreamer";

const phonemeGuide: Record<string, string> = {
  HH: "H (breath from throat)",
  T: "T (tongue taps teeth)",
  K: "K (back of throat)",
  D: "D (tongue taps roof)",
  G: "G (back of throat)",
  P: "P (lip pop)",
  B: "B (lip pop)",
  S: "S (hiss snake)",
  Z: "Z (buzz bee)",
  AH: "a (uh)",
  AE: "a (cat)",
  AA: "a (father)",
  OW: "o (go)",
  IY: "ee (see)",
  IH: "i (sit)",
  L: "L (tongue up)",
  R: "R (growl)",
  M: "M (lips closed)",
  N: "N (nose)",
  W: "W (lips round)",
};

export default function App() {
  const [targetText, setTargetText] = useState("hello");

  const {
    isListening,
    isProcessing,
    diagnostic,
    startStreaming,
    stopStreaming,
  } = useAudioStreamer(targetText);

  let title = "Needs Improvement";

  if (diagnostic?.is_correct) {
    title = "Correct";
  } else if (diagnostic?.target_achieved) {
    title = `Correct Target Word (${diagnostic.target})`;
  }

  return (
    <div>
      <h1>Diagnostic Engine</h1>

      <div>
        <label>Target Word: </label>
        <input
          type="text"
          value={targetText}
          onChange={(e) => setTargetText(e.target.value.toLowerCase())}
          disabled={isListening}
        />
      </div>

      <p>Status: {isListening ? "Listening..." : "Idle"}</p>

      {diagnostic && (
        <div>
          <h3>{title}</h3>

          <p>
            <strong>You said:</strong> "{diagnostic.spoken}"
          </p>

          {!diagnostic.is_correct && diagnostic.errors.length > 0 && (
            <div>
              <h4>Feedback</h4>

              <ul>
                {diagnostic.errors.map((err, idx) => (
                  <li key={idx}>
                    {err.type === "replace" && (
                      <>
                        Replaced {err.target_slice}
                        {phonemeGuide[err.target_slice] &&
                          ` (${phonemeGuide[err.target_slice]})`}
                        {" with "}
                        {err.spoken_slice}
                        {phonemeGuide[err.spoken_slice] &&
                          ` (${phonemeGuide[err.spoken_slice]})`}
                      </>
                    )}

                    {err.type === "delete" && (
                      <>
                        Missed sound {err.target_slice}
                        {phonemeGuide[err.target_slice] &&
                          ` (${phonemeGuide[err.target_slice]})`}
                      </>
                    )}

                    {err.type === "insert" && (
                      <>
                        {err.spoken_slice.length > 10
                          ? "Extra words detected."
                          : `Extra sound detected: ${err.spoken_slice}`}
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!isListening && !isProcessing ? (
        <button 
          onClick={startStreaming} 
        >
          Start Speaking "{targetText}"
        </button>
      ) : (
        <button 
          onClick={stopStreaming} 
          disabled={!isListening || isProcessing} 
        >
          {isProcessing ? 'Agent Thinking...' : 'Stop & Analyze'}
        </button>
      )}
    </div>
  );
}
