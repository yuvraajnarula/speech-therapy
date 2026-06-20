import io
import json
import wave
import string
import pronouncing
import difflib
import base64
import sys
import os

from mcp.server.fastmcp import FastMCP
from faster_whisper import WhisperModel

# Prevent HF spam on stdio transport
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

mcp = FastMCP("SpeechTherapyTools")

print("Loading Whisper model for MCP Tool...", file=sys.stderr)

try:
    whisper_model = WhisperModel(
        "small",
        device="cpu",
        compute_type="int8"
    )
    print("Whisper loaded.", file=sys.stderr)
except Exception as e:
    print(f"Whisper failed to load: {e}", file=sys.stderr)
    raise


@mcp.tool()
def transcribe_audio(audio_bytes_base64: str) -> str:
    try:
        audio_bytes = base64.b64decode(audio_bytes_base64)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(audio_bytes)

        wav_buffer.seek(0)

        segments, _ = whisper_model.transcribe(wav_buffer, beam_size=5)
        return " ".join([s.text.strip() for s in segments])

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def evaluate_english_phonetics(target_word: str, spoken_text: str) -> str:
    try:
        def clean_phonemes(text):
            text = text.translate(str.maketrans("", "", string.punctuation)).lower()

            phoneme_string = ""
            for word in text.split():
                phones = pronouncing.phones_for_word(word)

                if phones:
                    cleaned = "".join(
                        [p[:-1] if p[-1].isdigit() else p for p in phones[0].split()]
                    )
                    phoneme_string += cleaned
                else:
                    phoneme_string += word.upper()

            return phoneme_string

        target_phonemes = clean_phonemes(target_word)
        spoken_phonemes = clean_phonemes(spoken_text)

        matcher = difflib.SequenceMatcher(None, target_phonemes, spoken_phonemes)

        errors = []
        is_correct = True
        target_achieved = False

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                is_correct = False
                errors.append(
                    {
                        "type": tag,
                        "target_slice": target_phonemes[i1:i2],
                        "spoken_slice": spoken_phonemes[j1:j2],
                    }
                )

        if target_phonemes and spoken_phonemes.startswith(target_phonemes):
            target_achieved = True

            if len(target_phonemes) == len(spoken_phonemes):
                is_correct = True
                errors = []
            else:
                errors = [e for e in errors if e["type"] == "insert"]

        return json.dumps(
            {
                "language": "en",
                "target_phonemes": target_phonemes,
                "spoken_phonemes": spoken_phonemes,
                "is_correct": is_correct,
                "target_achieved": target_achieved,
                "errors": errors,
            }
        )

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def analyze_indian_context(target_text: str, spoken_text: str, language_code: str) -> str:
    result = {
        "language": language_code,
        "analysis": f"Compared '{spoken_text}' vs '{target_text}'",
        "is_correct": spoken_text.lower().strip() == target_text.lower().strip(),
    }
    return json.dumps(result)

@mcp.tool()
def log_session_for_finetuning(audio_bytes_base64: str, target_text: str, spoken_text: str, diagnostic_result: str) -> str:
    try:
        from pathlib import Path
        diag_dict = json.loads(diagnostic_result)
        
        audio_dir = Path("dataset/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_filename = f"audio_{hash(audio_bytes_base64)}.wav"
        audio_path = audio_dir / audio_filename
        
        with open(audio_path, "wb") as f:
            f.write(base64.b64decode(audio_bytes_base64))
            
        whisper_entry = {"audio_filepath": str(audio_path.resolve()), "text": spoken_text}
        with open("whisper_train.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(whisper_entry) + "\n")
            
        target_phonemes = diag_dict.get('target_phonemes', '')
        spoken_phonemes = diag_dict.get('spoken_phonemes', '')
        errors = diag_dict.get('errors', [])
        
        if not errors:
            sft_output = "Perfect pronunciation! The child successfully produced all target phonemes. No therapy intervention needed for this word."
        else:
            report_lines = ["Diagnostic Analysis:"]
            for err in errors:
                err_type = err.get('type')
                target_slice = err.get('target_slice', '')
                spoken_slice = err.get('spoken_slice', '')
                
                if err_type == 'replace':
                    report_lines.append(f"- Substitution Error: The child substituted the sound /{target_slice}/ with /{spoken_slice}/.")
                elif err_type == 'delete':
                    report_lines.append(f"- Omission Error: The child completely omitted the sound /{target_slice}/.")
                elif err_type == 'insert':
                    if spoken_slice:
                        report_lines.append(f"- Insertion Error: The child added extra sounds /{spoken_slice}/.")
                    else:
                        report_lines.append(f"- Insertion Error: The child added extra phonetic material.")
                        
            report_lines.append("\nActionable Therapy Feedback:")
            report_lines.append("1. Use a mirror to provide visual feedback on tongue and lip placement.")
            report_lines.append("2. Practice the specific missing or substituted sound in isolation.")
            report_lines.append("3. Once mastered in isolation, blend the sound back into the target word slowly.")
            sft_output = "\n".join(report_lines)
            
        sarvam_entry = {
            "instruction": "You are an expert pediatric speech therapist. Analyze the child's spoken phrase against the target phrase. Identify phonetic errors (insertions, deletions, substitutions) and provide actionable therapy feedback.",
            "input": f"Target Phrase: {target_text}\nChild's Spoken Phrase: {spoken_text}\nTarget Phonemes: {target_phonemes}\nChild Phonemes: {spoken_phonemes}",
            "output": sft_output
        }
        
        with open("sarvam_train.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(sarvam_entry) + "\n")
            
        return f"High-quality SFT data generated! Saved audio to {audio_path}."
        
    except Exception as e:
        return f"Error logging data: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
    
# demo