import io
import json
import wave
import string
import pronouncing
import difflib
from fastapi import FastAPI, WebSocket
from faster_whisper import WhisperModel
import uvicorn

app = FastAPI()

print("Loading Whisper model...")
model = WhisperModel("small", device="cpu", compute_type="int8")
print("Model loaded successfully!")

class DiagnosticEngine:
    def clean_phonemes(self, text):
        text = text.translate(str.maketrans('', '', string.punctuation)).lower()
        words = text.split()
        
        phoneme_string = ""
        for word in words:
            phones = pronouncing.phones_for_word(word)
            if phones:
                cleaned = ''.join([p[:-1] if p[-1].isdigit() else p for p in phones[0].split()])
                phoneme_string += cleaned
            else:
                phoneme_string += word.upper() 
        return phoneme_string

    def analyze(self, target_text, spoken_text):
        target_phonemes = self.clean_phonemes(target_text)
        spoken_phonemes = self.clean_phonemes(spoken_text)
            
        matcher = difflib.SequenceMatcher(None, target_phonemes, spoken_phonemes)
        
        errors = []
        is_correct = True
        target_achieved = False
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                is_correct = False
                errors.append({
                    "type": tag, 
                    "target_slice": target_phonemes[i1:i2],
                    "spoken_slice": spoken_phonemes[j1:j2]
                })
        if target_phonemes and spoken_phonemes.startswith(target_phonemes):
            target_achieved = True
            if len(target_phonemes) == len(spoken_phonemes):
                is_correct = True
                errors = []
            else:
                errors = [e for e in errors if e['type'] == 'insert']   
        return {
            "target": target_text,
            "spoken": spoken_text,
            "target_phonemes": target_phonemes,
            "spoken_phonemes": spoken_phonemes,
            "is_correct": is_correct,
            "target_achieved": target_achieved,
            "errors": errors
        }

engine = DiagnosticEngine()

@app.websocket("/ws/local-therapy")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("React client connected.")
    
    audio_buffer = bytearray()
    target_text = "hello" 
    
    try:
        while True:
            message = await websocket.receive()
            
            if message.get("type") == "websocket.disconnect":
                break
                
            if "text" in message and message["text"]:
                data = json.loads(message["text"])
                
                if data.get("action") == "set_target":
                    target_text = data.get("target", "hello").lower()
                    print(f"new target set: {target_text}")
                    continue 
                    
                elif data.get("action") == "stop":
                    print(f"Stop signal. Processing {len(audio_buffer)} bytes...")
                    
                    if len(audio_buffer) > 0:
                        wav_buffer = io.BytesIO()
                        with wave.open(wav_buffer, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(16000)
                            wav_file.writeframes(audio_buffer)
                        wav_buffer.seek(0)
                        
                        segments, info = model.transcribe(wav_buffer, beam_size=5)
                        spoken_text = " ".join([segment.text.strip() for segment in segments])
                        print(f"Whisper heard: '{spoken_text}'")
                        
                        diagnostic = engine.analyze(target_text, spoken_text)
                        print(f"Diagnostic sent to UI.")
                        
                        await websocket.send_json(diagnostic)
                        
                    audio_buffer.clear()
                    
            elif "bytes" in message and message["bytes"]:
                audio_buffer.extend(message["bytes"])
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)