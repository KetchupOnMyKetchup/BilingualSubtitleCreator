import os
import subprocess
from pathlib import Path
import config
import tempfile
import shutil

# --- CONFIGURABLE OPTIONS ---
AUDIO_OUTPUT_SUFFIX = "_vocals.wav"  # Suffix for extracted audio
DEMUCS_MODEL = "htdemucs"            # Model name (best for movies)
TWO_STEMS = "vocals"                 # Extract only vocals stem
# -----------------------------

def srt_exists(movie_path):
    """Check if primary language SRT already exists for this movie."""
    movie_path = Path(movie_path)
    srt_file = movie_path.parent / f"{config.LANG_PREFIX}_{movie_path.stem}.srt"
    return srt_file.exists()

def get_video_files(base_dir):
    """Collect video files based on config traversal settings, skip samples."""
    video_files = []

    # Scan BASE_DIR itself if enabled
    if config.SCAN_FILES_IN_BASEDIR:
        for f in os.listdir(base_dir):
            if "sample" in f.lower():
                continue
            if os.path.splitext(f)[1].lower() in config.VIDEO_EXTENSIONS:
                movie_path = Path(base_dir) / f
                if srt_exists(movie_path):
                    print(f"⏭ Skipping {f} (SRT already exists)")
                    continue
                video_files.append(str(movie_path))
                if config.PROCESS_ONE_PER_FOLDER:
                    break

    # Recursively scan subfolders if enabled
    if config.RECURSIVE:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in getattr(config, "EXCLUDE_FOLDERS", [])]
            for file in files:
                if "sample" in file.lower():
                    continue
                if os.path.splitext(file)[1].lower() in config.VIDEO_EXTENSIONS:
                    movie_path = Path(root) / file
                    if srt_exists(movie_path):
                        print(f"⏭ Skipping {file} (SRT already exists)")
                        continue
                    video_files.append(str(movie_path))
                    if config.PROCESS_ONE_PER_FOLDER:
                        break

    return sorted(set(video_files))


def extract_vocals(movie_path):
    """Run Demucs locally then move vocals.wav next to movie safely."""
    movie_path = Path(movie_path)
    output_dir = movie_path.parent
    output_wav = output_dir / f"{movie_path.stem}{AUDIO_OUTPUT_SUFFIX}"

    # Skip if already exists
    if output_wav.exists():
        print(f"⏭ Skipping {movie_path.name} (vocals already exist)")
        return None

    print(f"\n🎬 Processing: {movie_path.name}")
    print(f"   → Output: {output_wav.name}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        try:
            cmd = [
                "demucs",
                "--two-stems", TWO_STEMS,
                "-n", DEMUCS_MODEL,
                "-o", str(tmp_path),
                str(movie_path)
            ]
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Demucs failed for {movie_path.name}: {e}")
            return None

        possible_dirs = [
            tmp_path / DEMUCS_MODEL / movie_path.stem / TWO_STEMS / "vocals.wav",
            tmp_path / DEMUCS_MODEL / movie_path.stem / "vocals.wav",
            tmp_path / "separated" / DEMUCS_MODEL / movie_path.stem / "vocals.wav",
        ]

        demucs_output = next((p for p in possible_dirs if p.exists()), None)

        if not demucs_output:
            print(f"⚠️ Could not find vocals.wav for {movie_path.name}")
            return None

        shutil.copy2(demucs_output, output_wav)
        print(f"✅ Saved vocals: {output_wav}")

    return output_wav


def main():
    base_dir = Path(config.BASE_DIR)
    if not base_dir.exists():
        print(f"❌ BASE_DIR not found: {base_dir}")
        return

    video_files = get_video_files(base_dir)
    if not video_files:
        print("⚠️ No movie files found or all already have SRTs.")
        return

    print(f"🎞️ Found {len(video_files)} movie(s) to process.")

    for movie in video_files:
        extract_vocals(movie)


if __name__ == "__main__":
    main()
