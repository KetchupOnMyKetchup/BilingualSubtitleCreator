import os
import subprocess

# Path to your Movies folder
BASE_DIR = r"\\192.168.1.5\Media\Movies"

# Recognized video extensions
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mkv", ".mov", ".mpg", ".ts"]

def has_bg_srt(folder):
    """Check if a BG_*.srt file exists in this folder."""
    return any(f.lower().startswith("bg_") and f.lower().endswith(".srt") for f in os.listdir(folder))

def get_movie_file(folder):
    """Return the first movie file found in the folder, or None."""
    for f in os.listdir(folder):
        if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS:
            return f
    return None

def main():
    for folder in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, folder)
        if not os.path.isdir(full_path):
            continue  # skip files, only process folders

        if has_bg_srt(full_path):
            print(f"⏭ Skipping {folder} (BG_*.srt already exists)")
            continue

        movie_file = get_movie_file(full_path)
        if not movie_file:
            print(f"⚠ No video file found in {folder}")
            continue

        movie_path = os.path.join(full_path, movie_file)
        srt_output = os.path.join(full_path, f"BG_{os.path.splitext(movie_file)[0]}.srt")

        print(f"🎬 Processing {movie_file} in {folder}...")

        # Run Whisper
        cmd = [
            "whisper", movie_path,
            "--model", "medium",
            "--device", "cuda",
            "--language", "Bulgarian",
            "--output_format", "srt",
            "--output_dir", full_path
        ]

        subprocess.run(cmd)

        # Rename Whisper's output to have "BG_" prefix
        default_srt = os.path.splitext(movie_path)[0] + ".srt"
        if os.path.exists(default_srt):
            os.rename(default_srt, srt_output)
            print(f"✅🦖 Saved subtitles as {srt_output}")
        else:
            print(f"❌ Whisper did not generate expected file for {movie_file}")

if __name__ == "__main__":
    main()
