import difflib
import re
import string
from typing import Dict, List, Any, Optional

try:
    import pronouncing
except ImportError:
    pronouncing = None

# Phonetic guides for UI display & clinical feedback
PHONEME_ARTICULATION_GUIDE: Dict[str, str] = {
    "HH": "H (breath from throat)",
    "T": "T (alveolar tongue tap)",
    "TR": "T (retroflex tongue curl - Indic accent)",
    "K": "K (velar stop, back of throat)",
    "D": "D (tongue taps palate)",
    "DR": "D (retroflex tongue curl - Indic accent)",
    "G": "G (voiced velar, back of throat)",
    "P": "P (bilabial plosive, lip pop)",
    "B": "B (bilabial voiced, lip pop)",
    "S": "S (alveolar fricative, hiss snake)",
    "SH": "SH (palato-alveolar fricative, quiet sound)",
    "Z": "Z (voiced fricative, buzz bee)",
    "TH": "TH (dental fricative, tongue between teeth)",
    "DH": "DH (voiced dental fricative)",
    "AH": "a (uh - short central vowel)",
    "AE": "a (cat - front open vowel)",
    "AA": "a (father - back open vowel)",
    "OW": "o (go - rounded back vowel)",
    "IY": "ee (see - close front vowel)",
    "IH": "i (sit - near-close vowel)",
    "L": "L (lateral liquid, tongue up)",
    "R": "R (alveolar/retroflex liquid)",
    "M": "M (nasal, lips closed)",
    "N": "N (nasal, tongue against alveolar ridge)",
    "NG": "NG (velar nasal, back of mouth)",
    "W": "W (bilabial approximant, lips round)",
    "V": "V (labiodental voiced fricative)",
    "F": "F (labiodental voiceless fricative)",
    "CH": "CH (affricate, train sound)",
    "JH": "J (voiced affricate)",
}

# Indic Romanized transliteration phoneme approximations
INDIC_PHONETIC_MAP = {
    "namaste": ["N", "AH", "M", "AH", "S", "T", "EY"],
    "dhanyavad": ["DH", "AH", "N", "Y", "AH", "V", "AA", "D"],
    "pani": ["P", "AA", "N", "IY"],
    "khana": ["K", "AA", "N", "AA"],
    "doodh": ["D", "UW", "DH"],
    "kutta": ["K", "UH", "T", "AA"],
    "billi": ["B", "IH", "L", "IY"],
    "amma": ["AH", "M", "AA"],
    "appa": ["AH", "P", "AA"],
}


class PhoneticsDiagnosticEngine:
    """
    Advanced phonetic error analyzer supporting English and Indian dialect
    articulation patterns.
    """

    def clean_phonemes(self, text: str, language: str = "en") -> str:
        text = text.translate(str.maketrans("", "", string.punctuation)).lower().strip()
        if not text:
            return ""

        # Check Indic lookup dictionary first
        if text in INDIC_PHONETIC_MAP:
            return "".join(INDIC_PHONETIC_MAP[text])

        phoneme_string = ""
        words = text.split()

        for word in words:
            if word in INDIC_PHONETIC_MAP:
                phoneme_string += "".join(INDIC_PHONETIC_MAP[word])
                continue

            if pronouncing:
                phones = pronouncing.phones_for_word(word)
                if phones:
                    # Strip stress digits (e.g. AH0 -> AH, T1 -> T)
                    cleaned = "".join([p[:-1] if p[-1].isdigit() else p for p in phones[0].split()])
                    phoneme_string += cleaned
                    continue

            # Fallback for regional or un-indexed words: approximate character to phone
            approx = []
            i = 0
            w_len = len(word)
            while i < w_len:
                if i + 1 < w_len and word[i:i+2] in ["sh", "ch", "th", "dh", "kh", "gh", "ph", "jh"]:
                    approx.append(word[i:i+2].upper())
                    i += 2
                elif word[i] in ["a", "e", "i", "o", "u"]:
                    approx.append("AH" if word[i] in ["a", "u"] else "IY" if word[i] in ["e", "i"] else "OW")
                    i += 1
                else:
                    approx.append(word[i].upper())
                    i += 1
            phoneme_string += "".join(approx)

        return phoneme_string

    def analyze(self, target_text: str, spoken_text: str, language: str = "en") -> Dict[str, Any]:
        target_phonemes = self.clean_phonemes(target_text, language=language)
        spoken_phonemes = self.clean_phonemes(spoken_text, language=language)

        matcher = difflib.SequenceMatcher(None, target_phonemes, spoken_phonemes)

        errors: List[Dict[str, str]] = []
        is_correct = True
        target_achieved = False

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                is_correct = False
                errors.append({
                    "type": tag,
                    "target_slice": target_phonemes[i1:i2],
                    "spoken_slice": spoken_phonemes[j1:j2],
                })

        # Check prefix match for target achievement
        if target_phonemes and spoken_phonemes.startswith(target_phonemes):
            target_achieved = True
            if len(target_phonemes) == len(spoken_phonemes):
                is_correct = True
                errors = []
            else:
                errors = [e for e in errors if e["type"] == "insert"]

        # Calculate accuracy score (0.0 to 100.0)
        accuracy_score = round(matcher.ratio() * 100.0, 1)

        # Generate clinical feedback
        clinical_feedback = self.generate_clinical_feedback(
            target_text=target_text,
            spoken_text=spoken_text,
            target_phonemes=target_phonemes,
            spoken_phonemes=spoken_phonemes,
            errors=errors,
            target_achieved=target_achieved,
            is_correct=is_correct
        )

        return {
            "target": target_text,
            "spoken": spoken_text,
            "language": language,
            "target_phonemes": target_phonemes,
            "spoken_phonemes": spoken_phonemes,
            "is_correct": is_correct,
            "target_achieved": target_achieved,
            "accuracy_score": accuracy_score,
            "errors": errors,
            "clinical_feedback": clinical_feedback,
        }

    def generate_clinical_feedback(
        self,
        target_text: str,
        spoken_text: str,
        target_phonemes: str,
        spoken_phonemes: str,
        errors: List[Dict[str, str]],
        target_achieved: bool,
        is_correct: bool,
    ) -> str:
        if is_correct:
            return (
                "Clinical Observation: Accurate articulation achieved. "
                "Target phonemes were accurately produced without substitution or omission."
            )

        if len(spoken_phonemes) > (len(target_phonemes) * 3) and not target_achieved:
            return (
                "Clinical Observation: Off-target utterance detected. "
                "The child may need visual refocusing or task simplification before re-prompting."
            )

        bullet_points = []
        for err in errors:
            e_type = err.get("type")
            t_slice = err.get("target_slice", "")
            s_slice = err.get("spoken_slice", "")

            if e_type == "replace":
                t_guide = f" ({PHONEME_ARTICULATION_GUIDE.get(t_slice, '')})" if t_slice in PHONEME_ARTICULATION_GUIDE else ""
                s_guide = f" ({PHONEME_ARTICULATION_GUIDE.get(s_slice, '')})" if s_slice in PHONEME_ARTICULATION_GUIDE else ""
                bullet_points.append(
                    f"Substitution: Replaced sound /{t_slice}/{t_guide} with /{s_slice}/{s_guide}. "
                    f"Practice phonetic placement using visual cues."
                )
            elif e_type == "delete":
                t_guide = f" ({PHONEME_ARTICULATION_GUIDE.get(t_slice, '')})" if t_slice in PHONEME_ARTICULATION_GUIDE else ""
                bullet_points.append(
                    f"Omission: Missed sound /{t_slice}/{t_guide}. Practice isolating the sound slowly."
                )
            elif e_type == "insert":
                bullet_points.append(f"Insertion: Extra phonetic material detected: /{s_slice}/.")

        if not bullet_points:
            bullet_points.append("Minor acoustic deviation. Continue practicing repetitions.")

        return "Clinical Observation:\n" + "\n".join(f"- {p}" for p in bullet_points)


phonetics_engine = PhoneticsDiagnosticEngine()
