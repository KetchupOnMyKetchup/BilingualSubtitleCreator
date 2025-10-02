import os
import glob
import datetime

def read_srt(path):
    """Read an SRT file into blocks, return list of blocks."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()
    if not content:
        return None
    blocks = content.split("\n\n")
    return [b.strip() for b in blocks]

def merge_subs(bg_file, en_file, output_file):
    """Merge BG + EN subtitles line by line into one file."""
    bg_blocks = read_srt(bg_file)
    en_blocks = read_srt(en_file)

    if not bg_blocks or not en_blocks:
        return False, "One of the subtitle files is empty."

    if len(bg_blocks) != len(en_blocks):
        return False, f"Subtitle count mismatch ({len(bg_blocks)} vs {len(en_blocks)})"

    merged_blocks = []
    for bg, en in zip(bg_blocks, en_blocks):
        bg_lines = bg.splitlines()
        en_lines = en.splitlines()

        # Ensure indices and timestamps align
        if len(bg_lines) < 2 or len(en_lines) < 2:
            return False, "Malformed block(s) found."
        if bg_lines[0] != en_lines[0] or bg_lines[1] != en_lines[1]:
            return False, "Mismatch in index/timestamp."

        index = bg_lines[0]
        timecode = bg_lines[1]
        bg_text = "\n".join(bg_lines[2:])
        en_text = "\n".join(en_lines[2:])

        merged_block = f"{index}\n{timecode}\n{bg_text}\n{en_text}"
        merged_blocks.append(merged_block)

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("\n\n".join(merged_blocks))

    return True, "Merged successfully."

def process_folders(base_dir, log_file):
    for root, dirs, files in os.walk(base_dir):
        # Find first movie file
        movie_files = [f for f in files if f.lower().endswith((".mp4", ".mkv", ".avi", ".mov"))]
        if not movie_files:
            continue

        movie_name = os.path.splitext(movie_files[0])[0]
        merged_srt = os.path.join(root, f"{movie_name}.bg.srt")

        # Skip if merged already exists
        if any(f.lower() == f"{movie_name.lower()}.bg.srt" for f in files):
            log_file.write(f"[SKIP] {root} → {movie_name}.bg.srt already exists.\n")
            continue

        # Find subtitle files
        bg_subs = glob.glob(os.path.join(root, "BG_clean*.srt"))
        en_subs = glob.glob(os.path.join(root, "EN_clean*.srt"))

        if not bg_subs or not en_subs:
            log_file.write(f"[FAIL] {root} → Missing BG_clean or EN_clean subtitles.\n")
            continue

        bg_file = bg_subs[0]
        en_file = en_subs[0]

        success, msg = merge_subs(bg_file, en_file, merged_srt)
        if success:
            log_file.write(f"[OK]   {root} → Created {os.path.basename(merged_srt)}\n")
        else:
            log_file.write(f"[FAIL] {root} → {msg}\n")

def main():
    base_dir = r"\\192.168.1.5\Media\Movies"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(os.getcwd(), f"merge_log_{timestamp}.txt")

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"Subtitle Merge Log — {datetime.datetime.now()}\n")
        log_file.write("="*60 + "\n")
        process_folders(base_dir, log_file)

    print(f"✅ Finished. Log saved to {log_path}")

if __name__ == "__main__":
    main()
