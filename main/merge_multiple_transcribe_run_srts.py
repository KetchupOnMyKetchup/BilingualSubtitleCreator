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


def _merge_in_gaps(merged: pysrt.SubRipFile, source: pysrt.SubRipFile, label: str, tolerance_ms: int = 100) -> int:
    """
    Add items from 'source' that fall completely inside gaps between items of 'merged'.
    Uses a two-pointer sweep for O(N) behavior on sorted inputs.
    Returns number of items added.
    """
    if not merged:
        # If merged is empty, just copy everything (already filtered)
        added = len(source)
        merged.extend(source)
        merged.sort(key=lambda s: (s.start.ordinal, s.end.ordinal))
        merged.clean_indexes()
        print(f"✅ Added {added} subs from {label} (merged was empty)")
        return added

    base = list(merged)  # snapshot to define gaps; we won't mutate during iteration
    src = list(source)   # list for pointer access
    n = len(src)
    j = 0                # pointer into source
    added_entries = []

    # Precompute last possible time to bound windows that go to EOF
    # (Not required, but helpful for reasoning. We just use None for open-ended.)
    for i, sub in enumerate(base):
        if not _valid_item(sub):
            continue

        # Define gap window (gap_start, gap_end)
        gap_start = _shift_safe(sub.end, +tolerance_ms)
        next_start = base[i + 1].start if i + 1 < len(base) else None
        gap_end = _shift_safe(next_start, -tolerance_ms) if next_start else None

        if gap_start is None:
            continue  # malformed base end

        # Advance j until src[j] could possibly fit after gap_start
        while j < n and _valid_item(src[j]) and _time_leq(src[j].end, gap_start):
            j += 1

        k = j
        # Examine candidates whose start is before gap_end (or any if open-ended)
        while k < n:
            cand = src[k]
            if not _valid_item(cand):
                k += 1
                continue

            # if cand starts beyond gap_end, break (source is sorted)
            if gap_end is not None and _time_ge(cand.start, gap_end):
                break

            # Must start after/equal gap_start
            if not _time_ge(cand.start, gap_start):
                k += 1
                continue

            # Must end before/equal gap_end (unless open-ended)
            if gap_end is not None and not _time_leq(cand.end, gap_end):
                k += 1
                continue

            # Double-check: ensure it doesn't overlap anything already in base snapshot
            # Given it's in the gap, overlap is unlikely, but we still guard.
            overlaps_base = False
            # Only check neighbors around the gap to keep it cheap:
            # previous base sub (i) and next base sub (i+1)
            if _overlaps(cand, sub):
                overlaps_base = True
            elif i + 1 < len(base) and _overlaps(cand, base[i + 1]):
                overlaps_base = True

            if not overlaps_base:
                added_entries.append(cand)

            k += 1

        # Next gap will start after this base item; keep j where it is (monotonic)

    if added_entries:
        merged.extend(added_entries)
        merged.sort(key=lambda s: (s.start.ordinal, s.end.ordinal))
        merged.clean_indexes()
    print(f"✅ Added {len(added_entries)} subs from {label}")
    return len(added_entries)

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

    merged = safe_open_srt(balanced_path)
    if not merged:
        print(f"⚠️ Balanced file had no valid entries; using accurate/coverage as base.")
        # fall back to accurate if accurate empty
        if accurate_path.exists():
            merged = safe_open_srt(accurate_path)
        elif coverage_path.exists():
            merged = safe_open_srt(coverage_path)
        else:
            print("❌ No valid SRTs to merge.")
            return

    # Progressive merge: balanced base -> fill from accurate -> fill from coverage
    if balanced_path.exists():
        print("🔄 Integrating balanced subtitles...")
        balanced = safe_open_srt(balanced_path)
        _merge_in_gaps(merged, balanced, "balanced")
    else:
        print("⏭️ Skipping balanced (file not found)")

    if coverage_path.exists():
        print("🔄 Integrating coverage subtitles...")
        coverage = safe_open_srt(coverage_path)
        _merge_in_gaps(merged, coverage, "coverage")
    else:
        print("⏭️ Skipping coverage (file not found)")

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
