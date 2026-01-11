import re
from pathlib import Path
import pysrt
import config

# Some Whisper settings can cause spammy subtitles like "ААААААААА", "!!!!!", "......", "-k -k -k -k", etc.
# This script removes such spammy subtitles from all SRT files in BASE_DIR (and sub
# This has only been set to handle English and Cyrillic spammy patterns so far.
# Adjust/add more patterns as needed for other languages.
SPAMMY_PATTERN = re.compile(
    # repeated short words/syllables with optional dash/punctuation, 3+ times
    r"^(?:[-–]?\s*[А-Яа-яA-Za-z]{1,3}[!.,]?\s+){3,}$|"

    # repeated short words separated by comma, dash, or spaces, 3+ times
    r"^(?:\b([А-Яа-яA-Zazl]{1,3})[!.,]?\b[\s,.-]*){3,}$|"

    # same char repeated 6+ times
    r"(.)\1{5,}|"

    # 3+ dashes anywhere
    r"(?:[-–]){3,}|"

    # 3+ dots if it's the whole line
    r"^\s*\.{3,}\s*$|"

    # 4+ exclamations
    r"!{4,}|"

    # 4+ question marks
    r"\?{4,}|"

    # nonsense words
    r"\b(?:asdf|qwerty|lolol|hahaha|kkkkk|ahah|hehe|редактор|коректор|субтитров|устройството|абонирайте|абонирате|нашия канал|Благодаря ви, че|В .Сухашвили|lol)\b|"

    # repeated short English syllables, 2+ times
    r"\b([A-Za-z]{2,3}[-]?\1){2,}\b|"

    # repeated short Cyrillic syllables, 2+ times
    r"\b([А-Яа-я]{2,3}[-]?\1){2,}\b|"

    # long solid word
    r"[A-Za-zА-Яа-яЁё]{20,}|"

    # Generalized pattern to detect "- <text> - <text> - <text>" repeated 3 or more times
    r"(?:[-–]\s*[А-Яа-яA-Zazl]+\s*){3,}",

    re.UNICODE | re.IGNORECASE
)

# Separate repeated words and emoji checks
REPEATED_WORDS_PATTERN = re.compile(
    r"(?:\b(\w+)\b(?:[-\s,]+\1\b){2,})", re.UNICODE | re.IGNORECASE
)

EMOJI_PATTERN = re.compile(
    r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    r"\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF"
    r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
    r"\U00002702-\U000027B0\U000024C2-\U0001F251]+",
    re.UNICODE
)

# Only remove lines that consist entirely of short words if there are no normal-length words
def is_pure_short_words(line):
    words = line.split()
    if all(len(w) <= 2 for w in words) and any(len(w) > 2 for w in words) is False:
        return True
    return False

# Update _spammy to include separate checks
def _spammy(text: str) -> bool:
    spammy = bool(
        text and (
            SPAMMY_PATTERN.search(text.strip()) or
            REPEATED_WORDS_PATTERN.search(text.strip()) or
            EMOJI_PATTERN.search(text.strip()) or
            is_pure_short_words(text.strip())
        )
    )
    if spammy and getattr(config, "VERBOSE", False):
        print(f"🗑️ Detected spammy subtitle: {text}")
    return spammy

def _valid_sub(sub):
    return bool(sub.text.strip()) and not _spammy(sub.text)

def clean_srt_file(srt_path: Path):
    try:
        subs = pysrt.open(str(srt_path), encoding="utf-8")
    except Exception as e1:
        try:
            subs = pysrt.open(str(srt_path), encoding="utf-8-sig")
        except Exception as e2:
            print(f"⚠️ Could not open {srt_path}: {e2}")
            return False

    # Optimize double space replacement for large SRT files
    all_text = "\n".join(sub.text for sub in subs)
    all_text = re.sub(r"\s{2,}", " ", all_text)
    updated_texts = all_text.split("\n")
    for sub, updated_text in zip(subs, updated_texts):
        sub.text = updated_text

    # Keep only valid, non-spammy subtitles
    cleaned = [s for s in subs if _valid_sub(s)]

    # Renumber sequentially
    for i, s in enumerate(cleaned, start=1):
        s.index = i

    # Save back
    cleaned_srt = pysrt.SubRipFile(items=cleaned)
    cleaned_srt.save(str(srt_path), encoding="utf-8")
    print(f"Saved {srt_path}")
    return True

def find_srt_files(base_dir: Path):
    ex_dirs = set(getattr(config, "EXCLUDE_FOLDERS", []))
    files = []

    # Scan only top-level or recursively
    if getattr(config, "SCAN_FILES_IN_BASEDIR", True):
        if base_dir.is_dir():
            for f in base_dir.iterdir():
                if f.suffix.lower() == ".srt" and f.is_file() and f.parent.name not in ex_dirs:
                    files.append(f)

    if getattr(config, "RECURSIVE", False):
        for f in base_dir.rglob("*.srt"):
            if f.is_file() and f.parent.name not in ex_dirs:
                files.append(f)

    # Deduplicate & sort
    return sorted({f.resolve() for f in files}, key=lambda f: f.name.lower())

def main():
    print("🧠 remove_spammy_text_srts.py is being executed!")

    base_dir = Path(getattr(config, "BASE_DIR", "."))
    srt_files = find_srt_files(base_dir)

    if not srt_files:
        print("ℹ️ No SRT files found to clean.")
        return

    print(f"🧹🧹 Cleaning spam from {len(srt_files)} subtitle files in {base_dir}...")

    cleaned_count = 0
    skipped_count = 0

    for srt in srt_files:
        if clean_srt_file(srt):
            cleaned_count += 1
        else:
            skipped_count += 1

    print(f"✅ Finished cleaning: {cleaned_count} cleaned, {skipped_count} skipped.")

if __name__ == "__main__":
    main()
