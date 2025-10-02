import sys
import re

def read_srt(filename):
    """Reads an .srt file and returns a list of (index, time, text)."""
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read().strip()

    blocks = re.split(r"\n\s*\n", content)
    subs = []

    for block in blocks:
        lines = block.split("\n")
        if len(lines) >= 3:
            index = lines[0].strip()
            time = lines[1].strip()
            text = "\n".join(lines[2:]).strip()
            subs.append((index, time, text))
    return subs

def merge_srt(bg_file, en_file, out_file):
    bg_subs = read_srt(bg_file)
    en_subs = read_srt(en_file)

    if len(bg_subs) != len(en_subs):
        print("Warning: Number of subtitle blocks differ!")
    
    merged = []
    for (idx, time, bg_text), (_, _, en_text) in zip(bg_subs, en_subs):
        # Merge BG + EN with a blank line in between for readability
        merged.append(f"{idx}\n{time}\n{bg_text}\n{en_text}\n")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(merged))

    print(f"✅ Merged subtitles saved to {out_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python merge_srt_simple.py bulgarian.srt english.srt merged.srt")
    else:
        merge_srt(sys.argv[1], sys.argv[2], sys.argv[3])
