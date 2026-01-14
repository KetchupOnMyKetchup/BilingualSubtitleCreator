"""
Process a single movie through the entire pipeline.

This script handles one movie file completely through all steps:
1. Extract vocals (if needed)
2. Transcribe (accurate + balanced passes)
3. Clean spammy text
4. Merge transcription versions
5. Translate to secondary language
6. Merge bilingual subtitles

Call with: python process_single_movie.py <movie_file_path>
"""

import subprocess
import sys
from pathlib import Path
import config


def log(msg, level="INFO"):
    """Pretty print with log level."""
    emoji = {"INFO": "ℹ️", "ERROR": "❌", "SUCCESS": "✅", "STEP": "🔄", "SKIP": "⏭️"}
    print(f"[{level}] {emoji.get(level, '')} {msg}")


def file_exists(path: Path) -> bool:
    """Check if file exists."""
    return path.exists() and path.is_file()


def check_final_srt(movie_path: Path) -> bool:
    """Check if final merged SRT exists."""
    stem = movie_path.stem
    if stem.endswith("_vocals"):
        stem = stem[:-7]
    final_srt = movie_path.parent / f"{config.LANG_PREFIX.upper()}_{stem}.srt"
    return final_srt.exists()


def check_clean_srt(movie_path: Path) -> bool:
    """Check if cleaned SRT exists (indicates translation is needed)."""
    stem = movie_path.stem
    clean_srt = movie_path.parent / f"{config.LANG_PREFIX.upper()}_clean_{stem}.srt"
    return clean_srt.exists()


def get_merged_srt_path(movie_path: Path) -> Path:
    """Get path to the merged SRT file."""
    stem = movie_path.stem
    return movie_path.parent / f"{config.LANG_PREFIX.upper()}_{stem}.srt"


def get_clean_srt_path(movie_path: Path) -> Path:
    """Get path to the cleaned SRT file."""
    stem = movie_path.stem
    return movie_path.parent / f"{config.LANG_PREFIX.upper()}_clean_{stem}.srt"


def check_final_bilingual_srt(movie_path: Path) -> bool:
    """Check if final bilingual SRT exists."""
    stem = movie_path.stem
    # Final bilingual is named like: movie.bg.srt
    final_bilingual = movie_path.parent / f"{stem}.{config.LANG_PREFIX.lower()}.srt"
    return final_bilingual.exists()


def run_step(script_name: str, args: list = None) -> bool:
    """
    Run a script as a subprocess.
    
    Args:
        script_name: Name of script in main/ folder or subfolder (e.g., "transcribe.py" or "additional/cleanup_subs.py")
        args: Additional arguments to pass to script
    
    Returns:
        True if successful, False otherwise
    """
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        log(f"Script not found: {script_path}", "ERROR")
        return False
    
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        log(f"Step failed with exit code {e.returncode}: {script_name}", "ERROR")
        return False
    except Exception as e:
        log(f"Exception running {script_name}: {e}", "ERROR")
        return False


def process_movie(movie_path: Path) -> bool:
    """
    Process a single movie through the entire pipeline.
    
    Returns:
        True if successful or already complete, False if error
    """
    movie_path = Path(movie_path).resolve()
    
    if not movie_path.exists():
        log(f"Movie file not found: {movie_path}", "ERROR")
        return False
    
    movie_name = movie_path.name
    stem = movie_path.stem
    
    print(f"\n{'='*70}")
    log(f"Processing: {movie_name}", "STEP")
    print(f"{'='*70}")
    
    # Check if already fully processed
    if check_final_bilingual_srt(movie_path):
        log(f"Movie already fully processed (bilingual SRT exists)", "SKIP")
        return True
    
    # --- STEP 1: Extract vocals (if using WAV files) ---
    if config.USE_AUDIO_WAV and config.BACKGROUND_SUPPRESSION:
        vocals_path = movie_path.parent / f"{stem}_vocals.wav"
        if not vocals_path.exists():
            log("Extracting vocals...", "STEP")
            if not run_step("extract_vocals_to_wav.py", [str(movie_path)]):
                return False
        else:
            log("Vocals already extracted", "SKIP")
    
    # --- STEP 2: Transcribe ---
    # Check if we need to transcribe (final SRT doesn't exist yet)
    if not check_final_srt(movie_path):
        log("Transcribing audio...", "STEP")
        if not run_step("transcribe.py", ["--transcribe-one", str(movie_path)]):
            log("Transcription failed, but continuing pipeline (may skip translation)", "ERROR")
            # Don't abort - allow merging to happen if partial transcription exists
    else:
        log("Transcription already complete", "SKIP")
    
    # Only proceed to merge if MULTIPLE_TRANSCRIBE_RUNS is enabled
    if getattr(config, "MULTIPLE_TRANSCRIBE_RUNS", False):
        # --- STEP 3: Merge transcription versions (accurate + balanced) ---
        log("Merging transcription versions...", "STEP")
        if not run_step("merge_multiple_transcribe_run_srts.py", [str(movie_path)]):
            log("Merging failed, but continuing (may need manual intervention)", "ERROR")
    
    # --- STEP 4: Clean subtitles ---
    log("Cleaning subtitles...", "STEP")
    merged_srt = get_merged_srt_path(movie_path)
    clean_srt = get_clean_srt_path(movie_path)
    
    if clean_srt.exists():
        log(f"Clean SRT already exists", "SKIP")
    elif merged_srt.exists():
        log(f"Running cleanup on {merged_srt.name}", "STEP")
        if not run_step("additional/cleanup_subs.py", [str(merged_srt), str(clean_srt)]):
            log("Cleaning failed, but continuing", "ERROR")
    else:
        log(f"Merged SRT not found: {merged_srt.name}", "ERROR")
    
    # --- STEP 5: Translate subtitles ---
    # Only translate if clean SRT exists (meaning transcription is complete)
    if check_clean_srt(movie_path):
        log("Translating to secondary language...", "STEP")
        if not run_step("translate_subs.py", [str(movie_path)]):
            log("Translation failed, but continuing", "ERROR")
    else:
        log("Clean SRT not found, skipping translation", "SKIP")
    
    # --- STEP 6: Merge bilingual subtitles ---
    if check_clean_srt(movie_path):
        log("Merging bilingual subtitles...", "STEP")
        if not run_step("merge_subs.py", [str(movie_path)]):
            log("Bilingual merge failed, but continuing", "ERROR")
    else:
        log("Clean SRT not found, skipping bilingual merge", "SKIP")
    
    log(f"Pipeline complete for: {movie_name}", "SUCCESS")
    return True


def find_movies(base_dir: Path) -> list:
    """
    Find all movie files in base_dir, recursing into subdirectories.
    
    Respects:
    - SCAN_FILES_IN_BASEDIR
    - EXCLUDE_FOLDERS
    - VIDEO_EXTENSIONS
    """
    base = Path(base_dir).resolve()
    exts = [ext.lower() for ext in getattr(config, "VIDEO_EXTENSIONS", 
                                          [".mp4", ".mkv", ".mov", ".avi", ".mpg", ".ts", ".webm"])]
    exclude_folders = set(getattr(config, "EXCLUDE_FOLDERS", []))
    
    files = []
    
    for root, dirs, filenames in os.walk(base):
        # Remove excluded folders from traversal
        dirs[:] = [d for d in dirs if d not in exclude_folders]
        
        # Check SCAN_FILES_IN_BASEDIR at base level
        current_path = Path(root).resolve()
        is_base_level = (current_path == base)
        if is_base_level and not getattr(config, "SCAN_FILES_IN_BASEDIR", True):
            continue
        
        # Add matching files
        for f in filenames:
            if Path(f).suffix.lower() in exts:
                files.append(current_path / f)
    
    return sorted(files, key=lambda p: p.parent.name)  # Group by folder


def main():
    import os
    
    base_dir = Path(getattr(config, "BASE_DIR", "."))
    
    if not base_dir.exists():
        log(f"BASE_DIR not found: {base_dir}", "ERROR")
        return
    
    log(f"Starting per-movie pipeline processing", "INFO")
    log(f"Base directory: {base_dir}", "INFO")
    
    movies = find_movies(base_dir)
    
    if not movies:
        log("No movie files found", "ERROR")
        return
    
    log(f"Found {len(movies)} movie file(s)", "INFO")
    
    processed = 0
    failed = 0
    skipped = 0
    
    for idx, movie in enumerate(movies, 1):
        try:
            result = process_movie(movie)
            if result:
                processed += 1
            else:
                failed += 1
        except KeyboardInterrupt:
            log(f"Pipeline interrupted by user at movie {idx}/{len(movies)}", "INFO")
            log(f"Progress: {processed} complete, {failed} failed, {skipped} skipped", "INFO")
            sys.exit(0)
        except Exception as e:
            log(f"Unexpected error processing {movie.name}: {e}", "ERROR")
            failed += 1
    
    print(f"\n{'='*70}")
    log(f"Pipeline complete!", "SUCCESS")
    print(f"{'='*70}")
    log(f"Summary: {processed} processed, {failed} failed, {skipped} skipped", "INFO")


if __name__ == "__main__":
    import os
    if len(sys.argv) > 1 and sys.argv[1].endswith(('.mp4', '.mkv', '.mov', '.avi', '.mpg', '.ts', '.webm')):
        # Process single movie
        result = process_movie(sys.argv[1])
        sys.exit(0 if result else 1)
    else:
        # Process all movies
        main()
