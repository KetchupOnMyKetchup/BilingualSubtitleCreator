import os
import subprocess
import config

def has_lang_srt_for_movie(folder, movie_file):
    """Check if a <LANG_PREFIX>_*.srt file already exists for this movie file."""
    expected_srt = f"{config.LANG_PREFIX}_{os.path.splitext(movie_file)[0]}.srt"
    return expected_srt in os.listdir(folder)

def process_folder(root, files):
    """Process movie files inside a folder according to config rules."""
    processed_one = False
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext not in config.VIDEO_EXTENSIONS:
            continue

        if "sample" in f.lower():
            print(f"🧪 Skipping sample video: {f}")
            continue

        if has_lang_srt_for_movie(root, f):
            print(f"🐱 Skipping {f} ({config.LANG_PREFIX}_*.srt already exists)")
            continue

        movie_path = os.path.join(root, f)
        srt_output = os.path.join(root, f"{config.LANG_PREFIX}_{os.path.splitext(f)[0]}.srt")

        print(f"🎬 Processing {f} in {root}...")

        cmd = [
            "whisper", movie_path,
            "--model", config.WHISPER_MODEL,
            "--device", config.WHISPER_DEVICE,
            "--language", config.LANGUAGE,
            "--output_format", "srt",
            "--output_dir", root
        ]

        subprocess.run(cmd)

        default_srt = os.path.splitext(movie_path)[0] + ".srt"
        if os.path.exists(default_srt):
            os.rename(default_srt, srt_output)
            print(f"✅🦖 Saved subtitles as {srt_output}")
        else:
            print(f"❌ Whisper did not generate expected file for {f}")

        if config.PROCESS_ONE_PER_FOLDER:
            processed_one = True
            break

    return processed_one

def main():
    # Step 1: optionally process BASE_DIR itself
    if config.SCAN_FILES_IN_BASEDIR:
        files = os.listdir(config.BASE_DIR)
        process_folder(config.BASE_DIR, files)
    else:
        print("⏭ Skipping files in BASE_DIR itself")

    # Step 2: process subfolders
    if config.RECURSIVE:
        # Walk all subfolders recursively
        for root, _, files in os.walk(config.BASE_DIR):
            if root == config.BASE_DIR:
                continue  # already handled by SCAN_FILES_IN_BASEDIR
            process_folder(root, files)
    else:
        # Only top-level subfolders (non-recursive)
        for entry in os.listdir(config.BASE_DIR):
            full_path = os.path.join(config.BASE_DIR, entry)
            if os.path.isdir(full_path):
                files = os.listdir(full_path)
                process_folder(full_path, files)

if __name__ == "__main__":
    main()
