import os
import logging
from datetime import datetime

def setup_logger():
    # Ensure logs directory exists
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Create timestamped log filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    log_file = os.path.join(log_dir, f"merge_{timestamp}.log")

    # Configure logging to file + console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()  # print to console
        ]
    )

    return logging.getLogger(__name__)


logger = setup_logger()

def read_srt(path):
    if not os.path.exists(path):
        logger.warning(f"⚠️ Subtitle file not found: {path}")
        return None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().splitlines()

def merge_subs(bg_lines, en_lines):
    if len(bg_lines) != len(en_lines):
        logger.error("❌ Subtitle line counts do not match. Skipping merge.")
        return None

    merged = []
    i = 0
    while i < len(bg_lines):
        line = bg_lines[i]
        en_line = en_lines[i]

        if line.strip().isdigit():
            # subtitle number
            merged.append(line)
            i += 1
            continue

        if "-->" in line:
            # timestamp line
            merged.append(line)
            i += 1
            continue

        if line.strip() == "" and en_line.strip() == "":
            merged.append("")
            i += 1
            continue

        # Actual subtitle text (merge BG first, then EN)
        if line.strip() and en_line.strip():
            merged.append(line)
            merged.append(en_line)
        else:
            merged.append(line or en_line)

        i += 1

    return "\n".join(merged)


def process_folder(folder):
    logger.info(f"📂 Processing folder: {folder}")

    # Find first movie file (any common video extension)
    video_exts = (".mkv", ".mp4", ".avi", ".mov")
    movie_file = next((f for f in os.listdir(folder) if f.lower().endswith(video_exts)), None)

    if not movie_file:
        logger.warning("⚠️ No movie file found, skipping.")
        return

    movie_name, _ = os.path.splitext(movie_file)
    output_file = os.path.join(folder, f"{movie_name}.bg.srt")

    # Skip if already exists (case-insensitive check)
    if any(f.lower() == f"{movie_name.lower()}.bg.srt" for f in os.listdir(folder)):
        logger.info(f"⏭ {output_file} already exists, skipping.")
        return

    # Look for BG_clean and EN_clean files
    bg_file = next((os.path.join(folder, f) for f in os.listdir(folder) if f.startswith("BG_clean") and f.endswith(".srt")), None)
    en_file = next((os.path.join(folder, f) for f in os.listdir(folder) if f.startswith("EN_clean") and f.endswith(".srt")), None)

    if not bg_file or not en_file:
        logger.warning("⚠️ Missing BG_clean or EN_clean subtitles, skipping.")
        return

    logger.info(f"🧹 Found BG: {bg_file}")
    logger.info(f"🧹 Found EN: {en_file}")

    bg_lines = read_srt(bg_file)
    en_lines = read_srt(en_file)

    if not bg_lines or not en_lines:
        logger.warning("⚠️ Could not read one of the subtitle files, skipping.")
        return

    merged_content = merge_subs(bg_lines, en_lines)
    if not merged_content:
        return

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(merged_content)

    logger.info(f"✅ Merged subtitles saved to {output_file}")


def main():
    root_dir = r"\\192.168.1.5\Media\Movies"
    for foldername in os.listdir(root_dir):
        full_path = os.path.join(root_dir, foldername)
        if os.path.isdir(full_path):
            process_folder(full_path)


if __name__ == "__main__":
    main()
