import os
import subprocess
import config

# Optional: import Faster-Whisper only if needed
if config.USE_FASTER_WHISPER:
    from faster_whisper import WhisperModel

def has_lang_srt_for_movie(folder, movie_file):
    """Check if a <LANG_PREFIX>_*.srt file already exists for this movie file."""
    expected_srt = f"{config.LANG_PREFIX}_{os.path.splitext(movie_file)[0]}.srt"
    return expected_srt in os.listdir(folder)

def folder_is_excluded(folder_name):
    """Check if folder name matches any of the exclusion rules."""
    for excl in config.EXCLUDE_FOLDERS:
        if excl.lower() in folder_name.lower() or folder_name.lower() == excl.lower():
            return True
    return False

def transcribe_with_faster_whisper(model, movie_path, output_path):
    """Use Faster-Whisper to generate SRT."""
    segments, _ = model.transcribe(
        movie_path,
        language=config.LANG_PREFIX.lower(),
        beam_size=config.BEAM_SIZE,
        condition_on_previous_text=config.CONDITION_ON_PREVIOUS_TEXT
    )
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = segment.start
            end = segment.end
            text = segment.text.strip()
            f.write(f"{i}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{text}\n\n")

            # Print to console as well
            if config.VERBOSE:
                print(f"[{format_timestamp(start)} --> {format_timestamp(end)}] {text}")

def format_timestamp(seconds):
    """Format seconds into SRT timestamp HH:MM:SS,ms"""
    ms = int((seconds - int(seconds)) * 1000)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def process_folder(root, files):
    """Process movie files inside a folder according to config rules."""
    processed_one = False

    if folder_is_excluded(os.path.basename(root)):
        print(f"⛔ Skipping excluded folder: {root}")
        return False

    # Initialize Faster-Whisper model if needed
    if config.USE_FASTER_WHISPER:
        fw_model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.COMPUTE_TYPE
        )

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

        if config.USE_FASTER_WHISPER:
            # Use Faster-Whisper
            transcribe_with_faster_whisper(fw_model, movie_path, srt_output)
            print(f"✅🦖 Saved subtitles (Faster-Whisper) as {srt_output}")
        else:
            # Use standard Whisper CLI
            cmd = [
                "whisper", movie_path,
                "--model", config.WHISPER_MODEL,
                "--device", config.WHISPER_DEVICE,
                "--language", config.LANGUAGE,
                "--condition_on_previous_text", str(config.CONDITION_ON_PREVIOUS_TEXT),
                "--initial_prompt", "",
                "--carry_initial_prompt", str(config.CARRY_INITIAL_PROMPT),
                "--no_speech_threshold", str(config.NO_SPEECH_THRESHOLD),
                "--output_format", "srt",
                "--temperature", str(config.TEMPERATURE),
                "--output_dir", root
            ]
            subprocess.run(cmd)
            # Rename/move generated SRT if needed
            default_srt = os.path.splitext(movie_path)[0] + ".srt"
            try:
                if os.path.exists(default_srt):
                    os.rename(default_srt, srt_output)
                    print(f"✅🦖 Saved subtitles (Whisper) as {srt_output}")
                else:
                    print(f"❌ Whisper did not generate expected file for {f}")
            except PermissionError:
                fallback_path = os.path.join(config.FALLBACK_SRT_DIR, f"{config.LANG_PREFIX}_{os.path.splitext(f)[0]}.srt")
                os.makedirs(config.FALLBACK_SRT_DIR, exist_ok=True)
                os.rename(default_srt, fallback_path)
                print(f"⚠️ Could not save in target folder, saved to fallback: {fallback_path}")

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
        for root, _, files in os.walk(config.BASE_DIR):
            if root == config.BASE_DIR:
                continue  # already handled
            process_folder(root, files)
    else:
        for entry in os.listdir(config.BASE_DIR):
            full_path = os.path.join(config.BASE_DIR, entry)
            if os.path.isdir(full_path):
                files = os.listdir(full_path)
                process_folder(full_path, files)

if __name__ == "__main__":
    main()
