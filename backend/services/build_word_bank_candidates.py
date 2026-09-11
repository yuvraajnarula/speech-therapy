import argparse
import csv
import re
 
import nltk
from wordfreq import top_n_list, zipf_frequency
from nltk.corpus import wordnet as wn
from g2p_en import G2p
from better_profanity import profanity
 
VOWEL_PATTERN = re.compile(r"^(AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW)")
 
SOUND_CATEGORY_PHONEMES = {
    "s": "S",
    "r": "R",
    "l": "L",
    "sh": "SH",
    "th": "TH",
    "k": "K",
    "g": "G",
}
 
 
def ensure_nltk_resources():
    for resource in ["averaged_perceptron_tagger_eng", "wordnet", "punkt_tab"]:
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(resource, quiet=True)
 
 
def is_physical_noun(word: str) -> bool:
    """Imperfect concreteness heuristic — false positives expected, hence
    this feeds a review CSV rather than being trusted outright."""
    noun_synsets = wn.synsets(word, pos=wn.NOUN)
    verb_synsets = wn.synsets(word, pos=wn.VERB)
    if not noun_synsets or verb_synsets:
        return False
    syn = noun_synsets[0]
    for path in syn.hypernym_paths():
        if "physical_entity.n.01" in [s.name() for s in path]:
            return True
    return False
 
 
def clean_phones(g2p_output):
    return [re.sub(r"\d", "", p) for p in g2p_output if re.match(r"^[A-Z]+\d?$", p)]
 
 
def has_consonant_cluster(phones):
    for i in range(len(phones) - 1):
        if not VOWEL_PATTERN.match(phones[i]) and not VOWEL_PATTERN.match(phones[i + 1]):
            return True
    return False
 
 
def ends_in_consonant(phones):
    return bool(phones) and not VOWEL_PATTERN.match(phones[-1])
 
 
def categorize(phones):
    categories = []
    phone_set = set(phones)
    for category, phoneme in SOUND_CATEGORY_PHONEMES.items():
        if phoneme in phone_set:
            categories.append(category)
    if has_consonant_cluster(phones):
        categories.append("clusters")
    if ends_in_consonant(phones):
        categories.append("final_consonants")
    return categories
 
 
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top_n", type=int, default=20000, help="How many top-frequency English words to consider")
    parser.add_argument("--min_zipf", type=float, default=3.0, help="Minimum frequency score (higher = more common)")
    parser.add_argument("--out", default="review_candidates.csv")
    args = parser.parse_args()
 
    ensure_nltk_resources()
    g2p = G2p()
 
    print(f"Pulling top {args.top_n} English words by frequency...")
    candidates = top_n_list("en", args.top_n)
 
    print("Applying alphabetic/length/frequency filter...")
    candidates = [
        w for w in candidates
        if re.fullmatch(r"[a-z]{3,8}", w) and zipf_frequency(w, "en") >= args.min_zipf
    ]
    print(f"  -> {len(candidates)} remain")
 
    print("Applying profanity filter (mandatory safety net)...")
    before = len(candidates)
    candidates = [w for w in candidates if not profanity.contains_profanity(w)]
    print(f"  -> removed {before - len(candidates)}, {len(candidates)} remain")
 
    print("Applying concreteness heuristic (imperfect — review CSV will catch misses)...")
    candidates = [w for w in candidates if is_physical_noun(w)]
    print(f"  -> {len(candidates)} remain")
 
    print("Phonemizing and categorizing by target sound...")
    rows = []
    for word in candidates:
        phones = clean_phones(g2p(word))
        if not phones:
            continue
        categories = categorize(phones)
        if not categories:
            continue
        rows.append({
            "word": word,
            "zipf_frequency": round(zipf_frequency(word, "en"), 2),
            "phonemes": "".join(phones),
            "sound_categories": ",".join(categories),
            "approved": "",  # left blank for human review
        })
 
    rows.sort(key=lambda r: -r["zipf_frequency"])
 
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["word", "zipf_frequency", "phonemes", "sound_categories", "approved"])
        writer.writeheader()
        writer.writerows(rows)
 
    print(f"\nWrote {len(rows)} candidate words to {args.out}")
    print("This is a REVIEW file, not a final word bank. Please:")
    print("  1. Open it and skim for anything inappropriate the automated filters missed")
    print("  2. Mark 'approved' as yes/no per row (or just delete rows you reject)")
    print("  3. Feed the approved subset into generate_sarvam_data.py's word bank")
 
 
if __name__ == "__main__":
    main()