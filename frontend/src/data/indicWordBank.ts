export interface ClinicalWordItem {
  id: string;
  language: "hi" | "kn" | "ta" | "te" | "en-IN";
  nativeScript: string;
  romanized: string;
  englishMeaning: string;
  phonemeTarget: string;
  phoneticPosition: "initial" | "medial" | "final";
  ipa: string;
  phonemeArray: string[];
  syllables: string[];
  syllableCount: number;
  developmentalAgeYears: number;
  semanticCategory: "basic_needs" | "family" | "animals" | "food" | "body_parts" | "objects" | "transport" | "descriptors";
  clinicalCue: string;
  anatomicalTarget: string;
}

export const INDIC_WORD_BANK: ClinicalWordItem[] = [
  // ---------------------------------------------------------------------------
  // HINDI (हिंदी)
  // ---------------------------------------------------------------------------
  {
    id: "hi-p-01",
    language: "hi",
    nativeScript: "पानी",
    romanized: "pani",
    englishMeaning: "water",
    phonemeTarget: "/p/",
    phoneticPosition: "initial",
    ipa: "/p aː n iː/",
    phonemeArray: ["P", "AA", "N", "IY"],
    syllables: ["pa", "ni"],
    syllableCount: 2,
    developmentalAgeYears: 2.5,
    semanticCategory: "basic_needs",
    clinicalCue: "Press lips firmly together, release air suddenly without vibrating vocal cords.",
    anatomicalTarget: "Voiceless Bilabial Plosive",
  },
  {
    id: "hi-p-02",
    language: "hi",
    nativeScript: "चप्पल",
    romanized: "chappal",
    englishMeaning: "slipper",
    phonemeTarget: "/p/",
    phoneticPosition: "medial",
    ipa: "/tʃʰ ə p p ə l/",
    phonemeArray: ["CH", "AH", "P", "P", "AH", "L"],
    syllables: ["chap", "pal"],
    syllableCount: 2,
    developmentalAgeYears: 3.0,
    semanticCategory: "objects",
    clinicalCue: "Intervocalic geminate bilabial: Lip closure holds briefly before gentle release.",
    anatomicalTarget: "Medial Bilabial Stop",
  },
  {
    id: "hi-p-03",
    language: "hi",
    nativeScript: "साँप",
    romanized: "saap",
    englishMeaning: "snake",
    phonemeTarget: "/p/",
    phoneticPosition: "final",
    ipa: "/s aː p/",
    phonemeArray: ["S", "AA", "P"],
    syllables: ["saap"],
    syllableCount: 1,
    developmentalAgeYears: 3.5,
    semanticCategory: "animals",
    clinicalCue: "Word-final voiceless bilabial: Close lips firmly to seal sound.",
    anatomicalTarget: "Final Bilabial Stop",
  },
  {
    id: "hi-k-01",
    language: "hi",
    nativeScript: "कुत्ता",
    romanized: "kutta",
    englishMeaning: "dog",
    phonemeTarget: "/k/",
    phoneticPosition: "initial",
    ipa: "/k ʊ t̪ t̪ aː/",
    phonemeArray: ["K", "UH", "T_DENTAL", "AA"],
    syllables: ["kut", "ta"],
    syllableCount: 2,
    developmentalAgeYears: 3.0,
    semanticCategory: "animals",
    clinicalCue: "Back of tongue elevates against soft palate; release like a throat cough.",
    anatomicalTarget: "Voiceless Velar Plosive",
  },
  {
    id: "hi-k-02",
    language: "hi",
    nativeScript: "नाक",
    romanized: "naak",
    englishMeaning: "nose",
    phonemeTarget: "/k/",
    phoneticPosition: "final",
    ipa: "/n aː k/",
    phonemeArray: ["N", "AA", "K"],
    syllables: ["naak"],
    syllableCount: 1,
    developmentalAgeYears: 3.0,
    semanticCategory: "body_parts",
    clinicalCue: "Stop airflow abruptly at back of throat with back of tongue.",
    anatomicalTarget: "Final Velar Stop",
  },
  {
    id: "hi-t-01",
    language: "hi",
    nativeScript: "तोता",
    romanized: "tota",
    englishMeaning: "parrot",
    phonemeTarget: "/t̪/",
    phoneticPosition: "initial",
    ipa: "/t̪ oː t̪ aː/",
    phonemeArray: ["T_DENTAL", "OW", "T_DENTAL", "AA"],
    syllables: ["to", "ta"],
    syllableCount: 2,
    developmentalAgeYears: 2.5,
    semanticCategory: "animals",
    clinicalCue: "Place tongue tip gently against upper front teeth, not the roof of mouth.",
    anatomicalTarget: "Voiceless Dental Plosive",
  },
  {
    id: "hi-t-02",
    language: "hi",
    nativeScript: "हाथ",
    romanized: "haath",
    englishMeaning: "hand",
    phonemeTarget: "/t̪ʰ/",
    phoneticPosition: "final",
    ipa: "/h aː t̪ʰ/",
    phonemeArray: ["HH", "AA", "TH_ASPIRATED"],
    syllables: ["haath"],
    syllableCount: 1,
    developmentalAgeYears: 4.0,
    semanticCategory: "body_parts",
    clinicalCue: "Tongue to teeth with an audible puff of warm breath.",
    anatomicalTarget: "Aspirated Dental Plosive",
  },
  {
    id: "hi-tr-01",
    language: "hi",
    nativeScript: "टमाटर",
    romanized: "tamatar",
    englishMeaning: "tomato",
    phonemeTarget: "/ʈ/",
    phoneticPosition: "initial",
    ipa: "/ʈ ə m aː ʈ ə ɾ/",
    phonemeArray: ["TR_RETRO", "AH", "M", "AA", "TR_RETRO", "AH", "R"],
    syllables: ["ta", "maa", "tar"],
    syllableCount: 3,
    developmentalAgeYears: 4.5,
    semanticCategory: "food",
    clinicalCue: "Curl tip of tongue upwards touching hard palate dome before releasing.",
    anatomicalTarget: "Voiceless Retroflex Plosive",
  },
  {
    id: "hi-s-01",
    language: "hi",
    nativeScript: "सेब",
    romanized: "seb",
    englishMeaning: "apple",
    phonemeTarget: "/s/",
    phoneticPosition: "initial",
    ipa: "/s eː b/",
    phonemeArray: ["S", "EY", "B"],
    syllables: ["seb"],
    syllableCount: 1,
    developmentalAgeYears: 4.0,
    semanticCategory: "food",
    clinicalCue: "Teeth lightly closed, tongue tip near top ridge, blow steady cool hiss.",
    anatomicalTarget: "Voiceless Alveolar Fricative",
  },

  // ---------------------------------------------------------------------------
  // KANNADA (ಕನ್ನಡ)
  // ---------------------------------------------------------------------------
  {
    id: "kn-p-01",
    language: "kn",
    nativeScript: "ಪಾಪ",
    romanized: "paapa",
    englishMeaning: "baby / innocent",
    phonemeTarget: "/p/",
    phoneticPosition: "initial",
    ipa: "/p aː p a/",
    phonemeArray: ["P", "AA", "P", "AH"],
    syllables: ["paa", "pa"],
    syllableCount: 2,
    developmentalAgeYears: 2.0,
    semanticCategory: "family",
    clinicalCue: "Pop lips softly like making bubbles.",
    anatomicalTarget: "Bilabial Plosive",
  },
  {
    id: "kn-b-01",
    language: "kn",
    nativeScript: "ಬಾಳೆ",
    romanized: "baale",
    englishMeaning: "banana",
    phonemeTarget: "/b/",
    phoneticPosition: "initial",
    ipa: "/b aː ɭ e/",
    phonemeArray: ["B", "AA", "L_RETRO", "EY"],
    syllables: ["baa", "le"],
    syllableCount: 2,
    developmentalAgeYears: 3.5,
    semanticCategory: "food",
    clinicalCue: "Voice humming from throat while releasing lip seal into retroflex /ɭ/.",
    anatomicalTarget: "Voiced Bilabial Plosive",
  },
  {
    id: "kn-t-01",
    language: "kn",
    nativeScript: "ತಾತ",
    romanized: "thatha",
    englishMeaning: "grandfather",
    phonemeTarget: "/t̪/",
    phoneticPosition: "initial",
    ipa: "/t̪ aː t̪ a/",
    phonemeArray: ["T_DENTAL", "AA", "T_DENTAL", "AH"],
    syllables: ["thaa", "tha"],
    syllableCount: 2,
    developmentalAgeYears: 2.5,
    semanticCategory: "family",
    clinicalCue: "Tongue touches back of front upper teeth gently on both syllables.",
    anatomicalTarget: "Dental Plosive",
  },
  {
    id: "kn-tr-01",
    language: "kn",
    nativeScript: "ಟೋಪಿ",
    romanized: "topi",
    englishMeaning: "cap / hat",
    phonemeTarget: "/ʈ/",
    phoneticPosition: "initial",
    ipa: "/ʈ oː p i/",
    phonemeArray: ["TR_RETRO", "OW", "P", "IY"],
    syllables: ["to", "pi"],
    syllableCount: 2,
    developmentalAgeYears: 4.0,
    semanticCategory: "objects",
    clinicalCue: "Retroflex stop: Curl tongue back to touch roof before popping open.",
    anatomicalTarget: "Retroflex Plosive",
  },
  {
    id: "kn-k-01",
    language: "kn",
    nativeScript: "ಕಾಗೆ",
    romanized: "kaage",
    englishMeaning: "crow",
    phonemeTarget: "/k/",
    phoneticPosition: "initial",
    ipa: "/k aː ɡ e/",
    phonemeArray: ["K", "AA", "G", "EY"],
    syllables: ["kaa", "ge"],
    syllableCount: 2,
    developmentalAgeYears: 3.0,
    semanticCategory: "animals",
    clinicalCue: "Back of throat sound into voiced velar stop.",
    anatomicalTarget: "Velar Plosive",
  },

  // ---------------------------------------------------------------------------
  // TAMIL (தமிழ்)
  // ---------------------------------------------------------------------------
  {
    id: "ta-p-01",
    language: "ta",
    nativeScript: "பாப்பா",
    romanized: "paapa",
    englishMeaning: "baby",
    phonemeTarget: "/p/",
    phoneticPosition: "initial",
    ipa: "/p aː p p aː/",
    phonemeArray: ["P", "AA", "P", "AA"],
    syllables: ["paa", "paa"],
    syllableCount: 2,
    developmentalAgeYears: 2.0,
    semanticCategory: "family",
    clinicalCue: "Gentle lip pop on both syllables with steady vocalization.",
    anatomicalTarget: "Bilabial Plosive",
  },
  {
    id: "ta-t-01",
    language: "ta",
    nativeScript: "தண்ணீர்",
    romanized: "thannir",
    englishMeaning: "water",
    phonemeTarget: "/t̪/",
    phoneticPosition: "initial",
    ipa: "/t̪ ə ɳ ɳ iː ɾ/",
    phonemeArray: ["T_DENTAL", "AH", "N_RETRO", "IY", "R"],
    syllables: ["than", "neer"],
    syllableCount: 2,
    developmentalAgeYears: 3.5,
    semanticCategory: "basic_needs",
    clinicalCue: "Dental stop initial into retroflex nasal geminate.",
    anatomicalTarget: "Dental Plosive",
  },
  {
    id: "ta-zh-01",
    language: "ta",
    nativeScript: "பழம்",
    romanized: "pazham",
    englishMeaning: "fruit",
    phonemeTarget: "/ɻ/",
    phoneticPosition: "medial",
    ipa: "/p ə ɻ ə m/",
    phonemeArray: ["P", "AH", "ZH_RETRO", "AH", "M"],
    syllables: ["pa", "zham"],
    syllableCount: 2,
    developmentalAgeYears: 6.0,
    semanticCategory: "food",
    clinicalCue: "Classic Tamil retroflex /ɻ/: Curl tongue far back without touching palate roof.",
    anatomicalTarget: "Retroflex Approximant (Zha)",
  },
  {
    id: "ta-k-01",
    language: "ta",
    nativeScript: "கால்",
    romanized: "kaal",
    englishMeaning: "leg / foot",
    phonemeTarget: "/k/",
    phoneticPosition: "initial",
    ipa: "/k aː l/",
    phonemeArray: ["K", "AA", "L"],
    syllables: ["kaal"],
    syllableCount: 1,
    developmentalAgeYears: 3.0,
    semanticCategory: "body_parts",
    clinicalCue: "Velar stop opening cleanly into alveolar lateral coda.",
    anatomicalTarget: "Velar Plosive",
  },

  // ---------------------------------------------------------------------------
  // TELUGU (తెలుగు)
  // ---------------------------------------------------------------------------
  {
    id: "te-p-01",
    language: "te",
    nativeScript: "పాలు",
    romanized: "paalu",
    englishMeaning: "milk",
    phonemeTarget: "/p/",
    phoneticPosition: "initial",
    ipa: "/p aː l ʊ/",
    phonemeArray: ["P", "AA", "L", "UH"],
    syllables: ["paa", "lu"],
    syllableCount: 2,
    developmentalAgeYears: 2.5,
    semanticCategory: "basic_needs",
    clinicalCue: "Lip pop plosive followed by clean alveolar lateral.",
    anatomicalTarget: "Bilabial Plosive",
  },
  {
    id: "te-b-01",
    language: "te",
    nativeScript: "బంతి",
    romanized: "banthi",
    englishMeaning: "ball",
    phonemeTarget: "/b/",
    phoneticPosition: "initial",
    ipa: "/b ə n t̪ i/",
    phonemeArray: ["B", "AH", "N", "T_DENTAL", "IY"],
    syllables: ["ban", "thi"],
    syllableCount: 2,
    developmentalAgeYears: 3.0,
    semanticCategory: "objects",
    clinicalCue: "Close both lips, hum with vocal cords, then release into dental stop.",
    anatomicalTarget: "Voiced Bilabial Plosive",
  },
  {
    id: "te-t-01",
    language: "te",
    nativeScript: "తలుపు",
    romanized: "talupu",
    englishMeaning: "door",
    phonemeTarget: "/t̪/",
    phoneticPosition: "initial",
    ipa: "/t̪ ə l ʊ p ʊ/",
    phonemeArray: ["T_DENTAL", "AH", "L", "UH", "P", "UH"],
    syllables: ["ta", "lu", "pu"],
    syllableCount: 3,
    developmentalAgeYears: 3.5,
    semanticCategory: "objects",
    clinicalCue: "Dental voiceless stop followed by lateral and final bilabial.",
    anatomicalTarget: "Dental Plosive",
  },

  // ---------------------------------------------------------------------------
  // INDIAN ENGLISH (en-IN)
  // ---------------------------------------------------------------------------
  {
    id: "en-in-sp-01",
    language: "en-IN",
    nativeScript: "Spoon",
    romanized: "spoon",
    englishMeaning: "eating spoon",
    phonemeTarget: "/sp/ cluster",
    phoneticPosition: "initial",
    ipa: "[s p uː n]",
    phonemeArray: ["S", "P", "UW", "N"],
    syllables: ["spoon"],
    syllableCount: 1,
    developmentalAgeYears: 4.5,
    semanticCategory: "objects",
    clinicalCue: "Hiss like a snake /s/ directly into lip pop /p/ without inserting an 'uh' or 'ih' sound.",
    anatomicalTarget: "Alveolar-Bilabial S-Cluster",
  },
  {
    id: "en-in-sk-01",
    language: "en-IN",
    nativeScript: "School",
    romanized: "school",
    englishMeaning: "school",
    phonemeTarget: "/sk/ cluster",
    phoneticPosition: "initial",
    ipa: "[s k uː l]",
    phonemeArray: ["S", "K", "UW", "L"],
    syllables: ["school"],
    syllableCount: 1,
    developmentalAgeYears: 5.0,
    semanticCategory: "objects",
    clinicalCue: "Keep continuous hiss going right into velar stop /k/. Avoid 'is-kool'.",
    anatomicalTarget: "Alveolar-Velar S-Cluster",
  },
  {
    id: "en-in-w-01",
    language: "en-IN",
    nativeScript: "Water",
    romanized: "water",
    englishMeaning: "water",
    phonemeTarget: "[ʋ] vs [w]",
    phoneticPosition: "initial",
    ipa: "[ʋ aː ʈ ə ɾ]",
    phonemeArray: ["V_APPROX", "AA", "TR_RETRO", "AH", "R"],
    syllables: ["wa", "ter"],
    syllableCount: 2,
    developmentalAgeYears: 3.5,
    semanticCategory: "basic_needs",
    clinicalCue: "Round lips gently for /w/ or light upper teeth contact for Indian English [ʋ].",
    anatomicalTarget: "Labiodental Approximant",
  },
  {
    id: "en-in-th-01",
    language: "en-IN",
    nativeScript: "Think",
    romanized: "think",
    englishMeaning: "to ponder",
    phonemeTarget: "[t̪ʰ] (dental)",
    phoneticPosition: "initial",
    ipa: "[t̪ʰ ɪ ŋ k]",
    phonemeArray: ["TH_DENTAL", "IH", "NG", "K"],
    syllables: ["think"],
    syllableCount: 1,
    developmentalAgeYears: 4.5,
    semanticCategory: "descriptors",
    clinicalCue: "Tongue tip touches upper front teeth with clear breath release; distinguish from /s/ hiss.",
    anatomicalTarget: "Aspirated Dental Stop",
  },
];

/**
 * High-fidelity in-browser speech synthesis for authentic model reference audio.
 * Allows patient/therapist to hear native pronunciations at 1.0x and slow 0.75x clinical drills.
 */
export function speakTargetReference(
  word: string,
  language: "hi" | "kn" | "ta" | "te" | "en-IN",
  rate: number = 1.0
): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      resolve(false);
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(word);
    utterance.rate = Math.max(0.5, Math.min(rate, 1.2));
    utterance.pitch = 1.0;

    const langCodes: Record<string, string> = {
      hi: "hi-IN",
      kn: "kn-IN",
      ta: "ta-IN",
      te: "te-IN",
      "en-IN": "en-IN",
    };
    utterance.lang = langCodes[language] || "en-IN";

    // Attempt to locate matching Indian voice
    const voices = window.speechSynthesis.getVoices();
    const matchedVoice = voices.find(
      (v) => v.lang.startsWith(utterance.lang) || v.lang.includes("IN")
    );
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onend = () => resolve(true);
    utterance.onerror = () => resolve(false);

    window.speechSynthesis.speak(utterance);
  });
}
