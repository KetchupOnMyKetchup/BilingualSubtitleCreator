# =========================
# Path & File Settings
# =========================
# Base folder for your movies/TV shows
BASE_DIR = r"\\192.168.1.5\Media\Movies\Bulgarian\Tangled"

# Folder exclusion list (substrings or exact names)
EXCLUDE_FOLDERS = [
    "Stargate Atlantis",
    "Stargate SG-1",
    "Stargate Universe",
    "Avatar.The.Last.Airbender.S01-S03.TVRIP.x264.BGAUDiO-GOD",
    "Soul",
    "Ratatouille",
    "Cars 3",
    "Clueless (1995)",
]

# =========================
# Subtitle Language Settings
# =========================
# Primary subtitle language (audio language)
LANGUAGE = "Bulgarian"
LANG_PREFIX = "BG"

# Secondary/reference subtitle language (for translation, optional)
SECOND_LANGUAGE = "English"
SECOND_LANG_PREFIX = "EN"

# =========================
# Directory Traversal & Processing Behavior
# =========================
SCAN_FILES_IN_BASEDIR = True          # Scan video files directly in BASE_DIR
RECURSIVE = True                      # Recurse into subfolders

# =========================
# Recognized File Extensions
# =========================
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mkv", ".mov", ".mpg", ".ts", ".webm"]
AUDIO_EXTENSIONS = [".wav"]
BACKGROUND_SUPPRESSION = True            # Use background noise suppression (Demucs) before transcription and create .wav file, if false do transcribe directly on video file

# =========================
# Whisper / Transcription Settings
# =========================
WHISPER_MODEL = "large-v2"            # "small", "medium", "large-v2"
USE_GPU = True                        # Use GPU if available and sets it to "cuda", otherwise "cpu" in the code


# Use Faster-Whisper (optional)
USE_FASTER_WHISPER = True


# =========================
# Subtitle Quality, Timing & Display Settings
# =========================
COMPUTE_TYPE = "float16"              # GPU: float16/float32, CPU: int8
BEAM_SIZE = 14                        # Beam size for transcription (higher = better quality, slower)
NO_SPEECH_THRESHOLD = 0.2             # Threshold for no speech detection (0.0 - 1.0), higher = more strict

MAX_CHARS_PER_LINE = 40                # Maximum characters in a single subtitle line. 
CHARS_PER_SECOND = 20                  # Reading speed for dynamic duration. Higher value (18-20) = Faster reading speed assumption. Subtitles vanish quickly.

MIN_DURATION = 0.01                    # Minimum seconds a subtitle is on screen
MAX_DURATION = 3.0                     # Maximum seconds a subtitle is on screen
MIN_GAP = 0.0                          # Minimum gap between consecutive subtitles (seconds)
PAUSE_THRESHOLD = 0.2                  # Pause (in seconds) between words to split subtitles

# =========================
# Perform multiple (3) transcription passes with different Whisper Settings and merge SRT files to improve accuracy if set to True and will ignore above settings
# =========================
MULTIPLE_TRANSCRIBE_RUNS = True        # If False, only one pass is done.

# =========================
# Debugging & Verbose Options
# =========================
VERBOSE = True                         # Enable verbose logging
KEEP_WAV = True                       # If True, do not delete the _vocals.wav files after processing

# =========================
# Subtitle Cleaning Options
# =========================
# Offset (in seconds) to add to all cleaned subtitle start times (to delay slightly if needed) can be positive or negative
CLEAN_OFFSET_SECONDS = 0

# If True, create a  WAV file. If False, use video file audio directly. 
USE_AUDIO_WAV = False

# Add a flag to optionally keep multiple SRT files (accurate, balanced, coverage for example)
KEEP_ACCURATE_BALANCED_COVERAGE_SRT_FILES = True