# =========================
# Path & File Settings
# =========================
# Base folder for your movies/TV shows
BASE_DIR = r"\\192.168.1.5\Media\Movies\Soul"
# BASE_DIR = r"\\192.168.1.5\Media\TV Shows"
# BASE_DIR = r"C:\Users\caten\Desktop\Test"

# Recognized video file extensions
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mkv", ".mov", ".mpg", ".ts", ".webm"]

# Folder exclusion list (substrings or exact names)
EXCLUDE_FOLDERS = [
    "Stargate Atlantis",
    "Stargate SG-1",
    "Stargate Universe",
    "Avatar.The.Last.Airbender.S01-S03.TVRIP.x264.BGAUDiO-GOD"
]

# Fallback folder for saving .srt if the target folder fails
FALLBACK_SRT_DIR = r"C:\Users\caten\Desktop"


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
RECURSIVE = True                       # Recurse into subfolders
PROCESS_ONE_PER_FOLDER = False         # Only process the first valid video per folder


# =========================
# Whisper / Transcription Settings
# =========================
WHISPER_MODEL = "medium"               # "small", "medium", "large"
WHISPER_DEVICE = "cuda"                # "cuda", "cpu", etc.

# Fine-tuning transcription accuracy
CONDITION_ON_PREVIOUS_TEXT = True
TEMPERATURE = 0.0
CARRY_INITIAL_PROMPT = True
NO_SPEECH_THRESHOLD = 0.6

# Use Faster-Whisper (optional)
USE_FASTER_WHISPER = True
COMPUTE_TYPE = "float16"              # GPU: float16/float32, CPU: int8
BEAM_SIZE = 5

# Text formatting options
MAX_LINE_WIDTH = 42
MAX_LINE_COUNT = 2
MAX_WORDS_PER_LINE = 12
VERBOSE = True


# =========================
# Subtitle Timing & Display Settings
# =========================
MIN_CHARS = 8                         # Minimum characters before flushing buffer
MAX_CHARS_PER_LINE = 40                # Maximum characters in a single subtitle line
CHARS_PER_SECOND = 15                  # Reading speed for dynamic duration

MIN_DURATION = 0.3                     # Minimum seconds a subtitle is on screen
MAX_DURATION = 2.0                     # Maximum seconds a subtitle is on screen
MIN_GAP = 0.1             # Minimum gap between consecutive subtitles (seconds)

# Optional: chunking settings for Faster Whisper
CHUNK_SIZE = 30                         # seconds per chunk
CHUNK_OVERLAP = 1.0                     # seconds overlap between chunks to avoid cutting words


# =========================
# Debugging & Verbose Options
# =========================
VERBOSE = True
