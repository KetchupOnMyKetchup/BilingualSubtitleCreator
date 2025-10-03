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
def find_first_movie(folder):
    """Return first movie filename (no extension) or None"""
    for f in os.listdir(folder):
        if f.lower().endswith(tuple(config.VIDEO_EXTENSIONS)):
            return os.path.splitext(f)[0]
    return None

def find_sub_by_prefix(folder, prefix):
    """Find the first .srt with prefix (case-insensitive)"""
    for f in os.listdir(folder):
        if f.lower().endswith(".srt") and f.lower().startswith(prefix.lower()):
            return os.path.join(folder, f)
    return None

def read_srt_blocks(path):
    """Parse an .srt into blocks or None if unreadable"""
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
            out.append({'index': None, 'time': None, 'text': "\n".join(lines[2:]).strip() if len(lines) > 2 else ""})
            continue
        idx = lines[0].strip()
        timecode = lines[1].strip()
        text = "\n".join(line.rstrip() for line in lines[2:]).strip()
        out.append({'index': idx, 'time': timecode, 'text': text})
    return out

def merge_blocks(primary_blocks, secondary_blocks):
    """Merge two subtitle tracks"""
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

        # merge texts: primary first, then secondary
        primary_text = p['text'] or ""
        secondary_text = s['text'] or ""
        if primary_text and secondary_text:
            merged_text = f"{primary_text}\n{secondary_text}"
        else:
            merged_text = primary_text or secondary_text

        merged_block = f"{p['index']}\n{p['time']}\n{merged_text}"
        merged_blocks.append(merged_block)

    return "\n\n".join(merged_blocks) + "\n", "ok"

# ---------- main ----------
def process_folder(folder):
    logger.info(f"Processing: {folder}")
    movie_base = find_first_movie(folder)
    if not movie_base:
        logger.info(" ❗ No movie file found — skipping.")
        return

    # output file: <movie>.<langprefix>.srt (lowercase prefix)
    output_name = f"{movie_base}.{config.LANG_PREFIX.lower()}.srt"
    output_path = os.path.join(folder, output_name)

    if any(f.lower() == output_name.lower() for f in os.listdir(folder)):
        logger.info(f" 🐱 {output_name} already exists — skipping.")
        return

    # find cleaned subtitle files
    primary_file = find_sub_by_prefix(folder, f"{config.LANG_PREFIX}_clean")
    secondary_file = find_sub_by_prefix(folder, f"{config.SECOND_LANG_PREFIX}_clean")

    if not primary_file or not secondary_file:
        logger.warning(f"  Missing {config.LANG_PREFIX}_clean or {config.SECOND_LANG_PREFIX}_clean subtitle — skipping.")
        return

    logger.info(f"  Found {config.LANG_PREFIX}: {os.path.basename(primary_file)}")
    logger.info(f"  Found {config.SECOND_LANG_PREFIX}: {os.path.basename(secondary_file)}")

    primary_blocks = read_srt_blocks(primary_file)
    secondary_blocks = read_srt_blocks(secondary_file)

    merged_content, status = merge_blocks(primary_blocks, secondary_blocks)
    if merged_content is None:
        logger.error(f"  Failed to merge: {status}")
        return

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

    for entry in os.listdir(config.BASE_DIR):
        full = os.path.join(config.BASE_DIR, entry)
        if os.path.isdir(full):
            try:
                process_folder(full)
            except Exception as e:
                logger.exception(f"Unhandled error processing {full}: {e}")

    logger.info("=== Subtitle merge run finished ===")

if __name__ == "__main__":
    main()
