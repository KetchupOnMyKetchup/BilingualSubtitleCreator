import os
import re
import logging
import config
from datetime import datetime

# ---------- logging setup ----------
def setup_logger():
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    log_file = os.path.join(log_dir, f"merge_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

# ---------- helpers ----------
def find_subs_by_prefix(folder, prefix):
    """Return all .srt paths with prefix (case-insensitive)."""
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".srt") and f.lower().startswith(prefix.lower() + "_")
    ]

def read_srt_blocks(path):
    """Parse an .srt into blocks or None if unreadable."""
    if not os.path.exists(path):
        logger.warning(f"Subtitle file missing: {path}")
        return None
    try:
        raw = open(path, "r", encoding="utf-8", errors="ignore").read().strip()
    except Exception as e:
        logger.warning(f"Could not read subtitle {path}: {e}")
        return None

    if not raw:
        return []

    blocks = re.split(r'\r?\n\s*\r?\n', raw)
    out = []
    for b in blocks:
        lines = b.splitlines()
        if len(lines) < 2:
            out.append({'index': None, 'time': None, 'text': ""})
            continue
        idx = lines[0].strip()
        timecode = lines[1].strip()
        text = "\n".join(line.rstrip() for line in lines[2:]).strip()
        out.append({'index': idx, 'time': timecode, 'text': text})
    return out

def merge_blocks(primary_blocks, secondary_blocks):
    """Merge two subtitle tracks."""
    if primary_blocks is None or secondary_blocks is None:
        return None, "One of the subtitle files could not be read."
    if len(primary_blocks) == 0 or len(secondary_blocks) == 0:
        return None, "One of the subtitle files is empty."
    if len(primary_blocks) != len(secondary_blocks):
        return None, f"subtitle count mismatch ({len(primary_blocks)} vs {len(secondary_blocks)})"

    merged_blocks = []
    for i, (p, s) in enumerate(zip(primary_blocks, secondary_blocks), start=1):
        if p.get('index') is None or s.get('index') is None:
            return None, f"malformed block at position {i}"
        if p['index'] != s['index']:
            return None, f"index mismatch at block {i}: {p['index']} vs {s['index']}"
        if p['time'] != s['time']:
            return None, f"timecode mismatch at block {i}: {p['time']} vs {s['time']}"

        primary_text = p['text'] or ""
        secondary_text = s['text'] or ""
        merged_text = f"{primary_text}\n{secondary_text}" if primary_text and secondary_text else primary_text or secondary_text
        merged_block = f"{p['index']}\n{p['time']}\n{merged_text}"
        merged_blocks.append(merged_block)

    return "\n\n".join(merged_blocks) + "\n", "ok"

# ---------- main ----------
def process_folder(folder):
    """Merge matching BG_clean and EN_clean subtitles in one folder."""
    folder_name = os.path.basename(folder)
    if folder_name in getattr(config, "EXCLUDE_FOLDERS", []):
        logger.info(f"🚫 Skipping excluded folder: {folder_name}")
        return

    logger.info(f"Processing folder: {folder}")

    bg_clean_files = find_subs_by_prefix(folder, f"{config.LANG_PREFIX}_clean")
    en_clean_files = find_subs_by_prefix(folder, f"{config.SECOND_LANG_PREFIX}_clean")

    if not bg_clean_files or not en_clean_files:
        logger.info(f" ❗ Missing BG_clean or EN_clean subtitles — skipping folder.")
        return

    # Build dict for fast matching
    en_dict = {os.path.basename(f).lower().replace(f"{config.SECOND_LANG_PREFIX.lower()}_clean_", ""): f for f in en_clean_files}

    for bg_file in bg_clean_files:
        bg_name = os.path.basename(bg_file)
        rest = bg_name.lower().replace(f"{config.LANG_PREFIX.lower()}_clean_", "", 1)
        movie_base = os.path.splitext(rest)[0]

        # Skip "sample" files
        if "sample" in movie_base:
            logger.info(f" ⏭ Skipping sample file: {movie_base}")
            continue

        # Find matching EN_clean file
        en_file = en_dict.get(rest)
        if not en_file:
            logger.warning(f" ⚠ No matching EN_clean for {bg_name}")
            continue

        # Output name (movie.<lang>.srt)
        output_name = f"{movie_base}.{config.LANG_PREFIX.lower()}.srt"
        output_path = os.path.join(folder, output_name)

        if os.path.exists(output_path):
            logger.info(f" 🐱 {output_name} already exists — skipping.")
            continue

        logger.info(f"  Found pair → BG: {os.path.basename(bg_file)} | EN: {os.path.basename(en_file)}")

        primary_blocks = read_srt_blocks(bg_file)
        secondary_blocks = read_srt_blocks(en_file)
        merged_content, status = merge_blocks(primary_blocks, secondary_blocks)
        if merged_content is None:
            logger.error(f"  Failed to merge {movie_base}: {status}")
            continue

        try:
            with open(output_path, "w", encoding="utf-8") as out:
                out.write(merged_content)
            logger.info(f"  ✅🦖 Merged saved: {output_path}")
        except Exception as e:
            logger.error(f"  Could not write merged file: {e}")

def main():
    logger.info("=== Subtitle merge run started ===")
    if not os.path.isdir(config.BASE_DIR):
        logger.error(f"Base dir not found: {config.BASE_DIR}")
        return

    # Optionally scan base directory
    if getattr(config, "SCAN_FILES_IN_BASEDIR", False):
        process_folder(config.BASE_DIR)

    # Recursive or flat scan
    if getattr(config, "RECURSIVE", False):
        for root, dirs, files in os.walk(config.BASE_DIR):
            dirs[:] = [d for d in dirs if d not in getattr(config, "EXCLUDE_FOLDERS", [])]
            for d in dirs:
                folder_path = os.path.join(root, d)
                try:
                    process_folder(folder_path)
                except Exception as e:
                    logger.exception(f"Unhandled error processing {folder_path}: {e}")
    else:
        for entry in os.listdir(config.BASE_DIR):
            full = os.path.join(config.BASE_DIR, entry)
            if os.path.isdir(full) and entry not in getattr(config, "EXCLUDE_FOLDERS", []):
                try:
                    process_folder(full)
                except Exception as e:
                    logger.exception(f"Unhandled error processing {full}: {e}")
            elif entry in getattr(config, "EXCLUDE_FOLDERS", []):
                logger.info(f"🚫 Skipping excluded top-level folder: {entry}")

    logger.info("=== Subtitle merge run finished ===")

if __name__ == "__main__":
    main()
