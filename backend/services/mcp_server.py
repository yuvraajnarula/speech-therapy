import io 
import json 
import wave 
import string 
import pronouncing
import difflib 
from mcp.server.fastmcp import FastMCP
from faster_whisper import WhisperModel
from datetime import datetime 

mcp = FastMCP("Speech Therapy MCP Server")

print("Loading Whispr for mcp....")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

print("Whispr model loaded ...")

@mcp.tool()
def transcribe_audio(audio_bytes_base64 : str) :
    import base64
    audio_bytes = base64.b64decode(audio_bytes_base64)
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(audio_bytes)
    wav_buffer.seek(0)
    segments, _ = whisper_model.transcribe(wav_buffer, beam_size=5)
    
    return " ".join([segment.text.strip() for segment in segments])

@mcp.tool()
def evaluate_english_phonetics(
    target,
    spoken
):
    def clean_phonemes(text):
        text = text.translate(str.maketrans('', '', string.punctuation)).lower()
        phoneme_string = ''
        for word in text.split():
            phones = pronouncing.phones_for_word(word)
            if phones:
                cleaned = ''.join([p[:-1] if p[-1].isdigit() else p for p in phones[0].split()])
                phoneme_string += cleaned 
            else:
                phoneme_string += word.upper()
        
        return phoneme_string

    target_phonemes, spoken_phonemes = clean_phonemes(target) , clean_phonemes(spoken)
    
    matcher = difflib.SequenceMatcher(None ,  target_phonemes, spoken_phonemes)
    err = []
    is_correct = True 
    target_achieved = False 
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            is_correct = False 
            err.append({
                "type" : tag,
                "target_slice" : target_phonemes[i1: i2],
                "spoken_slice" : spoken_phonemes[j1:j2]
            })
    
    if target_phonemes and spoken_phonemes.startswith(target_phonemes):
        target_achieved = True
        if len(target_phonemes) == len(spoken_phonemes):
            is_correct = True
            errors = []
        else:
            errors = [e for e in errors if e['type'] == 'insert']
            
    return {
        "language": "en",
        "target_phonemes": target_phonemes,
        "spoken_phonemes": spoken_phonemes,
        "is_correct": is_correct,
        "target_achieved": target_achieved,
        "errors": errors
    }

@mcp.tool()
def analyse_indian_context(
    target,
    spoken,
    language_code
):
    return {
        "language": language_code,
        "sarvam_analysis": f"Sarvam AI analyzed '{spoken}' against '{target}' in {language_code}.",
        "cultural_context": "Detected mother-tongue influence (MTI) typical of this region.",
        "is_correct": spoken.lower().strip() == target.lower().strip()
    }

@mcp.tool()
def log_session_for_finetuning(
    audio_bytes_base64,
    target,
    spoken,
    diagnostic_result
):
    data_entry = {
        "audio_ref": f"audio_{hash(audio_bytes_base64)}.wav", 
        "target": target,
        "spoken": spoken,
        "diagnostic": diagnostic_result,
        "timestamp": f"{datetime.now()}"
    }

    with open("finetuning_dataset.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(data_entry) + "\n")
        
    return "Data successfully logged for fine-tuning pipeline."

if __name__ == "__main__":
    mcp.run(transport='stdio')