import os
import subprocess
from pathlib import Path
import tempfile
import config
from faster_whisper import WhisperModel
import pysrt
from pydub import AudioSegment, effects

OUTPUT_PREFIX = f"{config.LANG_PREFIX.upper()}_"  # Optional prefix for SRTs


# --- WAV conversion (includes normalization and FFmpeg fallback) ---
def reencode_wav(input_path: Path) -> Path:
    """
    Re-encode a possibly float32 or nonstandard WAV file into clean 16-bit PCM.
    This prevents Faster-Whisper from crashing on Demucs or float32 WAVs.
    """
    if not input_path.suffix.lower().endswith(".wav"):
        return input_path  # Only re-encode WAV files

    clean_path = Path(tempfile.gettempdir()) / f"{input_path.stem}_clean.wav"
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-af",
        (
            "highpass=f=100,"
            "lowpass=f=8000,"
            "afftdn=nf=-25,"
            "compand=attacks=0.02:decays=0.3:points=-80/-900|-60/-20|-40/-12|-20/-6|0/-3"
        ),
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        str(clean_path)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"🎧 Re-encoded clean WAV for transcription: {clean_path.name}")
        return clean_path
    except subprocess.CalledProcessError:
        print(f"⚠️ FFmpeg re-encode failed, using original file: {input_path}")
        return input_path


def convert_wav_for_whisper(vocals_path: Path) -> Path:
    """Convert Demucs WAV to standard 16-bit 16kHz mono WAV for Whisper."""
    # Store the whisper-ready wav in the same folder as the input file
    temp_file = vocals_path.parent / f"{vocals_path.stem}_whisper_ready.wav"
    audio = AudioSegment.from_file(vocals_path)

    # Normalize audio
    audio = effects.normalize(audio)

    # Optional: reduce bass bleed from background music
    if getattr(config, "APPLY_HIGH_PASS", True):
        audio = audio.high_pass_filter(80)

    # Convert to mono, 16 kHz, 16-bit PCM
    audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
    audio.export(temp_file, format="wav", codec="pcm_s16le")

    print(f"🔧 Converted WAV for Whisper: {temp_file}")
    return temp_file


# --- Subtitle utilities ---
def has_existing_srt(movie_path):
    stem = Path(movie_path).stem
    if stem.endswith("_vocals"):
        stem = stem[:-7]
    
    srt_name = f"{OUTPUT_PREFIX}{stem}"

    for file in os.listdir(Path(movie_path).parent):
        if file.startswith(srt_name) and file.endswith(".srt"):
            return True


def compute_duration(text):
    duration = max(len(text) / config.CHARS_PER_SECOND, config.MIN_DURATION)
    return min(duration, config.MAX_DURATION)


def safe_start_time(detected_start, previous_end):
    return max(detected_start, previous_end)


def generate_srt(segments, output_path):
    subs = pysrt.SubRipFile()


    previous_end = 0.0
    PAUSE_THRESHOLD = getattr(config, "PAUSE_THRESHOLD", 0.5)  # seconds; split if pause between words exceeds this

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue

        # If word-level timestamps are available, split on pauses between words
        if hasattr(segment, "words") and segment.words and hasattr(segment.words[0], "start"):
            words = segment.words
            current_line = words[0].word
            line_start = words[0].start
            for i in range(1, len(words)):
                gap = words[i].start - words[i-1].end
                if gap > PAUSE_THRESHOLD or len(current_line) > config.MAX_CHARS_PER_LINE:
                    # End current line and start a new one
                    start_time = safe_start_time(line_start, previous_end)
                    duration = compute_duration(current_line)
                    end_time = start_time + duration
                    subs.append(pysrt.SubRipItem(
                        index=len(subs) + 1,
                        start=pysrt.SubRipTime(seconds=start_time),
                        end=pysrt.SubRipTime(seconds=end_time),
                        text=current_line.strip()
                    ))
                    previous_end = end_time + config.MIN_GAP
                    # Start new line
                    current_line = words[i].word
                    line_start = words[i].start
                else:
                    current_line += ' ' + words[i].word
            # Add the last line in the segment
            if current_line.strip():
                start_time = safe_start_time(line_start, previous_end)
                duration = compute_duration(current_line)
                end_time = start_time + duration
                subs.append(pysrt.SubRipItem(
                    index=len(subs) + 1,
                    start=pysrt.SubRipTime(seconds=start_time),
                    end=pysrt.SubRipTime(seconds=end_time),
                    text=current_line.strip()
                ))
                previous_end = end_time + config.MIN_GAP
        else:
            # Fallback: original logic for segments without word-level timestamps
            # Split long lines
            lines = []
            while len(text) > config.MAX_CHARS_PER_LINE:
                split_at = text.rfind(" ", 0, config.MAX_CHARS_PER_LINE)
                if split_at == -1:
                    split_at = config.MAX_CHARS_PER_LINE
                lines.append(text[:split_at])
                text = text[split_at:].strip()
            if text:
                lines.append(text)

            seg_start = segment.start
            for line in lines:
                start_time = safe_start_time(seg_start, previous_end)
                duration = compute_duration(line)
                end_time = start_time + duration
                subs.append(pysrt.SubRipItem(
                    index=len(subs) + 1,
                    start=pysrt.SubRipTime(seconds=start_time),
                    end=pysrt.SubRipTime(seconds=end_time),
                    text=line
                ))
                previous_end = end_time + config.MIN_GAP

    subs.save(output_path, encoding="utf-8")
    print(f"✅🦖 Saved subtitles as {output_path}")


def format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# --- Transcription ---
def transcribe_audio(movie_path):
    movie_path = Path(movie_path)
    output_dir = movie_path.parent
    stem = movie_path.stem[:-7] if movie_path.stem.endswith("_vocals") else movie_path.stem

    if has_existing_srt(movie_path):
        print(f"⏭ Skipping {movie_path.name} (SRT already exists)")
        if config.KEEP_WAV == False and movie_path.name.endswith("_vocals.wav"):
            try:
                movie_path.unlink()
                print(f"🗑️ Deleted existing {movie_path.name}")
            except Exception as e:
                print(f"⚠️ Could not delete {movie_path.name}: {e}")
        return

    print(f"\n🎞️ Processing: {movie_path.name}")

    # --- 🔧 WAV fix integration point ---
    safe_input = reencode_wav(movie_path)
    whisper_ready_wav = convert_wav_for_whisper(safe_input)

    # --- Load model once ---
    model = WhisperModel(
        config.WHISPER_MODEL,
        device="cuda" if config.USE_GPU else "cpu",
        compute_type=config.COMPUTE_TYPE
    )

    # --- Define transcription passes ---
    if getattr(config, "MULTIPLE_TRANSCRIBE_RUNS", False):
        passes = [
        {
            "name": "accurate",
            "beam_size": 20,
            "temperature": 0,
            "condition_on_previous_text": False,
            "no_speech_threshold": 0.7,
            "compression_ratio_threshold": 10.0,
            "chunk_length": 25
        },
        {
            "name": "balanced",
            "beam_size": 8,
            "temperature": 0.15,
            "condition_on_previous_text": False,
            "no_speech_threshold": 0.35,
            "compression_ratio_threshold": 6.0,
            "chunk_length": 30
        },
        {
            "name": "coverage",
            "beam_size": 25,
            "temperature": 0.2,
            "condition_on_previous_text": True,
            "no_speech_threshold": 0.15,
            "compression_ratio_threshold": 8.0,
            "chunk_length": 15
        },
    ]

    else:
        passes = [
            {"name": None, "beam_size": getattr(config, "BEAM_SIZE", 15), "temperature": 0}
        ]

    # --- Run transcription(s) ---
    for run in passes:
        print(f"🔊 Transcribing ({run['name'] or 'single pass'}) with beam={run['beam_size']} temp={run['temperature']}")
        segments = []

        vad_params = dict(min_silence_duration_ms=500, threshold=0.4)
        try:
            result = model.transcribe(
                str(whisper_ready_wav),
                language=config.LANG_PREFIX.lower(),
                beam_size=run["beam_size"],
                temperature=run["temperature"],
                condition_on_previous_text=run["condition_on_previous_text"],
                no_speech_threshold=run["no_speech_threshold"],
                compression_ratio_threshold=run["compression_ratio_threshold"],
                chunk_length=run["chunk_length"],
                word_timestamps=True,
                vad_filter=False,
                vad_parameters=vad_params,
                initial_prompt=None,
                patience=3.0,
            )

            for segment in result[0]:
                segments.append(segment)
                print(f"[{format_time(segment.start)} -> {format_time(segment.end)}] {segment.text.strip()}")

            # Decide output name based on pass
            if run["name"]:
                srt_name = f"{OUTPUT_PREFIX}{stem}_{run['name']}.srt"
            else:
                srt_name = f"{OUTPUT_PREFIX}{stem}.srt"

            srt_path = output_dir / srt_name
            generate_srt(segments, srt_path)

        except Exception as e:
            print(f"❌ Transcription failed for {run['name'] or 'main'} pass: {e}")

    # Return temp files for cleanup by caller
    return whisper_ready_wav, safe_input


# --- File collection ---
def collect_files(base_dir):
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

# --- Cleanup utility ---
def cleanup_temp_files(movie_path):
    movie_path = Path(movie_path)
    # Remove temp whisper wav (now stored in movie folder)
    temp_whisper = movie_path.parent / f"{movie_path.stem}_whisper_ready.wav"
    if temp_whisper.exists():
        if not getattr(config, "KEEP_WAV", False):
            try:
                temp_whisper.unlink()
                print(f"🗑️ Deleted temp Whisper WAV: {temp_whisper.name}")
            except Exception as e:
                print(f"⚠️ Could not delete temp Whisper WAV: {e}")
    # Remove reencoded wav if it exists and is not the original
    clean_wav = Path(tempfile.gettempdir()) / f"{movie_path.stem}_clean.wav"
    if clean_wav.exists():
        try:
            clean_wav.unlink()
            print(f"🗑️ Deleted temp clean WAV: {clean_wav.name}")
        except Exception as e:
            print(f"⚠️ Could not delete temp clean WAV: {e}")
    # Remove vocals file if needed and not keeping WAV
    if not getattr(config, "KEEP_WAV", False):
        if movie_path.name.endswith("_vocals.wav") and movie_path.exists():
            try:
                movie_path.unlink()
                print(f"🗑️ Deleted {movie_path.name} after transcription")
            except Exception as e:
                print(f"⚠️ Could not delete {movie_path.name}: {e}")


# --- Main ---
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

    import sys
    import subprocess
    script_path = Path(__file__).resolve()

    for file in files:
        print(f"▶️ Launching subprocess for: {file}")
        try:
            result = subprocess.run([
                sys.executable, str(script_path), '--transcribe-one', str(file)
            ])
            if result.returncode != 0:
                print(f"❌ Subprocess failed for {file} with exit code {result.returncode}")
            # Cleanup temp files after subprocess returns
            cleanup_temp_files(file)
        except Exception as e:
            print(f"❌ Exception launching subprocess for {file}: {e}")
            continue
    print("✅ All files processed (errors skipped gracefully).")


if __name__ == "__main__":
    import sys
    if '--transcribe-one' in sys.argv:
        idx = sys.argv.index('--transcribe-one')
        if len(sys.argv) > idx + 1:
            transcribe_audio(sys.argv[idx + 1])
        else:
            print("❌ No file provided for --transcribe-one")
            sys.exit(1)
    else:
        main()
