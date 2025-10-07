import os
import subprocess
from pathlib import Path
import config

MODEL_SIZE = "medium"
LANGUAGE = "bg"
OUTPUT_PREFIX = f"{LANGUAGE.upper()}_"  # Optional prefix for SRTs


def has_existing_srt(movie_path):
    """Check if an SRT for this file already exists."""
    movie_path = Path(movie_path)
    # Strip "_vocals" if present in stem
    stem = movie_path.stem
    if stem.endswith("_vocals"):
        stem = stem[:-7]
    srt_name = f"{OUTPUT_PREFIX}{stem}.srt"
    srt_path = movie_path.with_name(srt_name)
    return srt_path.exists()


def transcribe_audio(movie_path):
    """Run Whisper/Faster-Whisper directly in the movie folder."""
    movie_path = Path(movie_path)
    output_dir = movie_path.parent
    # Use original stem for output
    stem = movie_path.stem
    if stem.endswith("_vocals"):
        stem = stem[:-7]
    srt_name = f"{OUTPUT_PREFIX}{stem}.srt"
    srt_path = output_dir / srt_name

    if has_existing_srt(movie_path):
        print(f"⏭ Skipping {movie_path.name} (SRT already exists)")
        # Delete _vocals.wav if SRT exists
        if movie_path.name.endswith("_vocals.wav"):
            try:
                movie_path.unlink()
                print(f"🗑️ Deleted existing {movie_path.name}")
            except Exception as e:
                print(f"⚠️ Could not delete {movie_path.name}: {e}")
        return

    print(f"\n🎞️ Processing: {movie_path.name}")

    cmd = [
        "whisper",
        str(movie_path),
        "--model", MODEL_SIZE,
        "--language", LANGUAGE,
        "--output_format", "srt",
        "--output_dir", str(output_dir)
    ]

    try:
        print(f"🎬 Transcribing {movie_path.name} ...")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Transcription failed for {movie_path.name}: {e}")
        return
    except Exception as e:
        print(f"❌ Unexpected error while transcribing {movie_path.name}: {e}")
        return

    # Whisper sometimes outputs without prefix
    possible_outputs = [
        srt_path,
        output_dir / f"{movie_path.stem}.srt"
    ]

    found_srt = False
    for path in possible_outputs:
        if path.exists():
            if path.name != srt_name:
                new_path = output_dir / srt_name
                os.rename(path, new_path)
                srt_path = new_path
            print(f"✅🦖 Saved subtitles as {srt_path}")
            found_srt = True
            break

    if not found_srt:
        print(f"⚠️ Could not find SRT output for {movie_path.name}")
        return

    # Delete _vocals.wav after successful transcription
    if movie_path.name.endswith("_vocals.wav"):
        try:
            movie_path.unlink()
            print(f"🗑️ Deleted {movie_path.name} after transcription")
        except Exception as e:
            print(f"⚠️ Could not delete {movie_path.name}: {e}")


def collect_files(base_dir):
    """
    Collect all files to transcribe depending on config.BACKGROUND_SUPPRESSION:
    - True: only *_vocals.wav
    - False: only video files
    """
    targets = []
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in getattr(config, "EXCLUDE_FOLDERS", [])]

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            full_path = os.path.join(root, f)

            if config.BACKGROUND_SUPPRESSION:
                if ext == ".wav" and f.endswith("_vocals.wav"):
                    targets.append(full_path)
            else:
                if ext in [".mp4", ".mkv", ".mov", ".avi"]:
                    targets.append(full_path)

    return sorted(targets)


def main():
    base_dir = Path(config.BASE_DIR)
    if not base_dir.exists():
        print(f"❌ BASE_DIR not found: {base_dir}")
        return

    files = collect_files(base_dir)
    if not files:
        print("⚠️ No supported files found.")
        return

    print(f"🎥 Found {len(files)} file(s) to transcribe.")
    for file in files:
        transcribe_audio(file)


if __name__ == "__main__":
    main()
