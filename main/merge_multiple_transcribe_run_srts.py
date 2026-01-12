# main/merge_multiple_transcribe_run_srts.py
import os
from pathlib import Path
import pysrt
import config


def find_movie_files():
    """
    Locate all movie files in BASE_DIR that match VIDEO_EXTENSIONS.
    Honors SCAN_FILES_IN_BASEDIR and RECURSIVE.
    """
    base = Path(config.BASE_DIR)
    exts = [ext.lower() for ext in getattr(config, "VIDEO_EXTENSIONS", [".mp4", ".mkv", ".mov", ".avi", ".mpg", ".ts", ".webm"])]

    files = []
    if getattr(config, "SCAN_FILES_IN_BASEDIR", True):
        if base.is_dir():
            files.extend([p for p in base.iterdir() if p.suffix.lower() in exts and p.is_file()])
    if getattr(config, "RECURSIVE", False):
        files.extend([p for p in base.rglob("*") if p.suffix.lower() in exts and p.is_file()])

    # dedupe & sort
    files = sorted({p.resolve() for p in files}, key=lambda p: p.name.lower())
    return files


def _valid_item(it) -> bool:
    try:
        return bool(it.start and it.end and it.start.ordinal < it.end.ordinal)
    except Exception:
        return False


def safe_open_srt(path: Path) -> pysrt.SubRipFile:
    """
    Open an SRT and return a file with only valid, well-ordered items.
    Invalid rows are dropped. Output is sorted by start time.
    """
    try:
        subs = pysrt.open(str(path), encoding="utf-8")
    except Exception as e:
        print(f"⚠️ Could not parse {path.name}: {e}")
        return pysrt.SubRipFile()

    cleaned = [s for s in subs if _valid_item(s)]
    cleaned.sort(key=lambda s: (s.start.ordinal, s.end.ordinal))
    return pysrt.SubRipFile(items=cleaned)


def _shift_safe(srt_time, ms):
    """Return shifted time or None if invalid."""
    if not srt_time:
        return None
    try:
        return srt_time.shift(milliseconds=ms)
    except Exception:
        return None


def _time_leq(a, b):
    if a is None or b is None:
        return False
    return a.ordinal <= b.ordinal


def _time_lt(a, b):
    if a is None or b is None:
        return False
    return a.ordinal < b.ordinal


def _time_ge(a, b):
    if a is None or b is None:
        return False
    return a.ordinal >= b.ordinal


def _overlaps(a, b):
    """Strict overlap: (a.start < b.end) and (a.end > b.start)"""
    if not (_valid_item(a) and _valid_item(b)):
        return False
    return (a.start.ordinal < b.end.ordinal) and (a.end.ordinal > b.start.ordinal)


def _merge_in_gaps(
    merged: pysrt.SubRipFile,
    source: pysrt.SubRipFile,
    label: str,
    tolerance_ms: int = 100
) -> int:
    """
    Merge source subtitles into gaps of the merged subtitle list.
    
    Strategy:
    1. Find all gaps between consecutive merged items
    2. For each gap, collect all source items that fit (with no/minimal overlap)
    3. For items that touch or slightly overlap boundaries, include them if they enhance coverage
    4. Return the total number of items added
    """
    
    if not merged:
        merged.extend(source)
        merged.sort(key=lambda s: (s.start.ordinal, s.end.ordinal))
        merged.clean_indexes()
        print(f"✅ Added {len(source)} subs from {label} (merged was empty)")
        return len(source)

    merged.sort(key=lambda s: (s.start.ordinal, s.end.ordinal))
    source.sort(key=lambda s: (s.start.ordinal, s.end.ordinal))

    merged_items = list(merged)
    source_items = list(source)
    
    # Track which source items we've already added to avoid duplicates
    added_indices = set()
    
    # Iterate through gaps between consecutive merged items
    for i in range(len(merged_items) - 1):
        left = merged_items[i]
        right = merged_items[i + 1]

        if not (_valid_item(left) and _valid_item(right)):
            continue

        # Define gap boundaries with tolerance
        gap_start_ms = left.end.ordinal + tolerance_ms
        gap_end_ms = right.start.ordinal - tolerance_ms

        # No valid gap if boundaries cross
        if gap_start_ms >= gap_end_ms:
            continue

        # Collect all source items that fit in this gap
        for src_idx, cand in enumerate(source_items):
            if src_idx in added_indices:
                continue  # Already added
            if not _valid_item(cand):
                continue

            cand_start_ms = cand.start.ordinal
            cand_end_ms = cand.end.ordinal

            # ---- CASE 1: Candidate fits completely in the gap (clean fit) ----
            if cand_start_ms >= gap_start_ms and cand_end_ms <= gap_end_ms:
                merged_items.append(cand)
                added_indices.add(src_idx)
                continue

            # ---- CASE 2: Candidate slightly overlaps gap boundaries (minor tolerance) ----
            # Allow items that have slight overlap (< 200ms) with boundaries
            gap_overlap_tolerance_ms = 200
            
            # Check if item mostly fits in the gap (starts before gap_end and ends after gap_start)
            if (cand_start_ms < gap_end_ms and cand_end_ms > gap_start_ms):
                # Calculate overlap with gap boundaries
                overlap_left = max(0, gap_start_ms - cand_start_ms)
                overlap_right = max(0, cand_end_ms - gap_end_ms)
                
                # If overlaps are minimal, include it
                if overlap_left < gap_overlap_tolerance_ms and overlap_right < gap_overlap_tolerance_ms:
                    merged_items.append(cand)
                    added_indices.add(src_idx)
                    continue

    # Update merged with new items
    if added_indices:
        merged.clear()
        merged.extend(merged_items)
        merged.sort(key=lambda s: (s.start.ordinal, s.end.ordinal))
        merged.clean_indexes()

    added_count = len(added_indices)
    print(f"✅ Added {added_count} subs from {label}")
    return added_count


def delete_model_srts(base_srt_path: Path):
    """
    Delete the *_accurate.srt, *_balanced.srt, and *_coverage.srt files
    only if the merged SRT (base_srt_path) exists.
    """
    if not base_srt_path.exists():
        print(f"⚠️ Merged file not found, skipping cleanup: {base_srt_path.name}")
        return

    suffixes = ["_accurate.srt", "_balanced.srt", "_coverage.srt"]

    for suffix in suffixes:
        target_file = base_srt_path.with_name(base_srt_path.stem + suffix)
        if target_file.exists():
            try:
                os.remove(target_file)
                print(f"🗑️ Deleted {target_file.name}")
            except Exception as e:
                print(f"⚠️ Could not delete {target_file.name}: {e}")
        else:
            if getattr(config, "VERBOSE", False):
                print(f"ℹ️ File not found: {target_file.name}")


def merge_srts_for_movie(movie_path: Path):
    """
    Merge BG_<stem>_accurate.srt + fill from balanced + fill from coverage.
    Output: BG_<stem>.srt
    """
    movie_stem = movie_path.stem
    srt_dir = movie_path.parent

    accurate_path = srt_dir / f"BG_{movie_stem}_accurate.srt"
    balanced_path = srt_dir / f"BG_{movie_stem}_balanced.srt"
    coverage_path = srt_dir / f"BG_{movie_stem}_coverage.srt"
    merged_path   = srt_dir / f"BG_{movie_stem}.srt"

    if merged_path.exists():
        print(f"🐱 {merged_path.name} already exists, skipping merge.")
        return

    if not balanced_path.exists():
        print(f"❌ Missing {balanced_path.name}, cannot merge.")
        return

    print(f"🧩 Merging subtitles for {movie_stem}")

    # Initialize merged with balanced subtitles
    merged = safe_open_srt(balanced_path)
    if not merged:
        print(f"⚠️ Balanced file had no valid entries; using accurate/coverage as base.")
        # Fall back to accurate if balanced is empty
        if accurate_path.exists():
            merged = safe_open_srt(accurate_path)
        elif coverage_path.exists():
            merged = safe_open_srt(coverage_path)
        else:
            print("❌ No valid SRTs to merge.")
            return

    # Progressive merge: balanced base -> fill from accurate -> fill from coverage
    if accurate_path.exists():
        print("🔄 Integrating accurate subtitles...")
        accurate = safe_open_srt(accurate_path)
        _merge_in_gaps(merged, accurate, "accurate")
    else:
        print("⏭️ Skipping accurate (file not found)")

    if coverage_path.exists():
        print("🔄 Integrating coverage subtitles...")
        coverage = safe_open_srt(coverage_path)
        _merge_in_gaps(merged, coverage, "coverage")
    else:
        print("⏭️ Skipping coverage (file not found)")

    # Finalize and save
    merged.clean_indexes()
    merged.save(str(merged_path), encoding="utf-8")
    print(f"💾 Merged file saved → {merged_path.name}")

    # Cleanup extra .srt files
    if not getattr(config, "KEEP_ACCURATE_BALANCED_COVERAGE_SRT_FILES", False):
        delete_model_srts(Path(merged_path))

def main():
    if not getattr(config, "MULTIPLE_TRANSCRIBE_RUNS", False):
        print("ℹ️ MULTIPLE_TRANSCRIBE_RUNS is False — nothing to merge.")
        return

    print("🎬 Searching for movie files to merge...")
    movie_files = find_movie_files()
    if not movie_files:
        print("❌ No movie files found. Check BASE_DIR or VIDEO_EXTENSIONS.")
        return

    for movie in movie_files:
        merge_srts_for_movie(movie)


if __name__ == "__main__":
    main()
