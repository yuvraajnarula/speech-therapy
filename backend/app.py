from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from faster_whisper import WhisperModel
import json
import io
import wave
import uvicorn

app = FastAPI()

print("Loading whispr model...")
model = WhisperModel("small", device="cpu", compute_type="int8")

print("Model loaded successfully")

@app.websocket('/ws/local-therapy')
async def websocket_endpoint(websocket : WebSocket):
    await websocket.accept()
    print("React Client connected")
    audio_buffer = bytearray()
    try:
        while True:
            msg = await websocket.receive()
            #disconnection
            if msg.get("type") == "websocket.disconnect":
                break 
            #chunk handling
            if "bytes" in msg and   msg["bytes"]:
                audio_buffer.extend(msg["bytes"])
            # command handler
            elif "text" in msg and msg["text"]:
                data = json.loads(msg["text"])
                
                if data.get("action") == "stop":
                    print(f"Stop signal recieved. Processing {len(audio_buffer)} bytes of audio...")
                    
                    if len(audio_buffer) > 0:
                        wav_buffer = io.BytesIO()
                        with wave.open(wav_buffer , "wb") as wav_file:
                            wav_file.setnchannels(1) # mono 
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(16000)
                            wav_file.writeframes(audio_buffer)
                        
                        wav_buffer.seek(0)
                        segments, info = model.transcribe(wav_buffer, beam_size=5)
                        transcribed_text = " ".join([segment.text for segment in segments])
                        
                        print(f"Transcription: {transcribed_text}")
                        
                        # Send the result back to React
                        await websocket.send_json({"transcribed": transcribed_text})
                        
                    audio_buffer.clear()
    except WebSocketDisconnect:
        print("client disconnect")
    except Exception as e:
        print(f"Error : {e}")
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)