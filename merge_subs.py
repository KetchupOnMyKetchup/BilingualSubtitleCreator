import os
import re
import logging
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

# ---------- config ----------
BASE_DIR = r"\\192.168.1.5\Media\Movies"
VIDEO_EXTS = [".mp4", ".avi", ".mkv", ".mov", ".mpg", ".ts"]

# ---------- helpers ----------
def find_first_movie(folder):
    """Return first movie filename (no extension) or None"""
    for f in os.listdir(folder):
        if f.lower().endswith(VIDEO_EXTENSIONS):
            return os.path.splitext(f)[0]
    return None

def find_sub_by_prefix(folder, prefix):
    """Find the first .srt with prefix (case-insensitive)"""
    for f in os.listdir(folder):
        if f.lower().endswith(".srt") and f.lower().startswith(prefix.lower()):
            return os.path.join(folder, f)
    return None

def read_srt_blocks(path):
    """
    Parse an .srt into a list of blocks: [{'index','time','text'}...]
    Returns [] if file exists but empty, or None if file missing/unreadable.
    """
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

    # split on blank line (handles CRLF and LF)
    blocks = re.split(r'\r?\n\s*\r?\n', raw)
    out = []
    for b in blocks:
        lines = b.splitlines()
        if len(lines) < 2:
            # malformed block
            out.append({'index': None, 'time': None, 'text': "\n".join(lines[2:]).strip() if len(lines)>2 else ""})
            continue
        idx = lines[0].strip()
        timecode = lines[1].strip()
        text = "\n".join(line.rstrip() for line in lines[2:]).strip()
        out.append({'index': idx, 'time': timecode, 'text': text})
    return out

def merge_blocks(bg_blocks, en_blocks):
    """Given parsed blocks from BG and EN, validate and merge them; returns merged string or (None, reason)."""
    if bg_blocks is None or en_blocks is None:
        return None, "One of the subtitle files could not be read."
    if len(bg_blocks) == 0 or len(en_blocks) == 0:
        return None, "One of the subtitle files is empty."
    if len(bg_blocks) != len(en_blocks):
        return None, f"subtitle count mismatch ({len(bg_blocks)} vs {len(en_blocks)})"

    merged_blocks = []
    for i, (bg, en) in enumerate(zip(bg_blocks, en_blocks), start=1):
        # Basic index/time validation (some files use different numbering style; we require match)
        if bg.get('index') is None or en.get('index') is None:
            return None, f"malformed block at position {i}"
        if bg['index'] != en['index']:
            return None, f"index mismatch at block {i}: {bg['index']} vs {en['index']}"
        if bg['time'] != en['time']:
            return None, f"timecode mismatch at block {i}: {bg['time']} vs {en['time']}"

        # Merge texts: BG first, then EN (skip empty bodies gracefully)
        bg_text = bg['text'] or ""
        en_text = en['text'] or ""
        if bg_text and en_text:
            merged_text = f"{bg_text}\n{en_text}"
        else:
            merged_text = bg_text or en_text

        # Build block
        merged_block = f"{bg['index']}\n{bg['time']}\n{merged_text}"
        merged_blocks.append(merged_block)

    merged_content = "\n\n".join(merged_blocks) + "\n"  # trailing newline
    return merged_content, "ok"

# ---------- main processing ----------
def process_folder(folder):
    logger.info(f"Processing: {folder}")
    movie_base = find_first_movie(folder)
    if not movie_base:
        logger.info("  No movie file found — skipping.")
        return

    # create target filename: <movie>.bg.srt
    output_name = f"{movie_base}.bg.srt"
    output_path = os.path.join(folder, output_name)

    # case-insensitive existence check
    if any(f.lower() == output_name.lower() for f in os.listdir(folder)):
        logger.info(f"  {output_name} already exists — skipping.")
        return

    # find BG_clean and EN_clean (first match)
    bg_file = find_sub_by_prefix(folder, "BG_clean")
    en_file = find_sub_by_prefix(folder, "EN_clean")

    if not bg_file or not en_file:
        logger.warning("  Missing BG_clean or EN_clean subtitle — skipping.")
        return

    logger.info(f"  Found BG: {os.path.basename(bg_file)}")
    logger.info(f"  Found EN: {os.path.basename(en_file)}")

    bg_blocks = read_srt_blocks(bg_file)
    en_blocks = read_srt_blocks(en_file)

    merged_content, status = merge_blocks(bg_blocks, en_blocks)
    if merged_content is None:
        logger.error(f"  Failed to merge: {status}")
        return

    try:
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(merged_content)
        logger.info(f"  ✅ Merged saved: {output_path}")
    except Exception as e:
        logger.error(f"  Could not write merged file: {e}")

def main():
    logger.info("=== Subtitle merge run started ===")
    if not os.path.isdir(BASE_DIR):
        logger.error(f"Base dir not found: {BASE_DIR}")
        return

    for entry in os.listdir(BASE_DIR):
        full = os.path.join(BASE_DIR, entry)
        if os.path.isdir(full):
            try:
                process_folder(full)
            except Exception as e:
                logger.exception(f"Unhandled error processing {full}: {e}")

    logger.info("=== Subtitle merge run finished ===")

if __name__ == "__main__":
    main()
