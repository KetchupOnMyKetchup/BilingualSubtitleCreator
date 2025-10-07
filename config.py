# config.py

# Path to your Movies folder
BASE_DIR = r"\\192.168.1.5\Media\Movies\The Wild Robot"
# BASE_DIR = r"\\192.168.1.5\Media\TV Shows"
# BASE_DIR = r"C:\Users\caten\Desktop\Test"

# Recognized video extensions
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mkv", ".mov", ".mpg", ".ts", ".webm"]

# Whisper settings "small", "medium", "large"
WHISPER_MODEL = "medium"
WHISPER_DEVICE = "cuda"

# Primary subtitle language that the movie audio uses
LANGUAGE = "Bulgarian"
LANG_PREFIX = "BG"

# Secondary (reference) subtitle language to translate into
# NOTE: Google Translate expects ISO codes (like "en", "es", "fr") for LANG_PREFIX, please use the correct ISO code for your language
SECOND_LANGUAGE = "English"
SECOND_LANG_PREFIX = "EN"

# Traversal behavior
SCAN_FILES_IN_BASEDIR = True   # True = scan video files in BASE_DIR itself, False = skip them
RECURSIVE = True              # True = recurse into subfolders of subfolders, False = only top-level subfolders
PROCESS_ONE_PER_FOLDER = False  # True = process only first valid video per folder, False = process all

# Fallback folder for saving .srt if target folder fails
FALLBACK_SRT_DIR = r"C:\Users\caten\Desktop"

# Fine-tuning the subtitle accuracy for movies
CONDITION_ON_PREVIOUS_TEXT = True
TEMPERATURE = 0.0
CARRY_INITIAL_PROMPT = True
NO_SPEECH_THRESHOLD = 0.6

# Use Faster Whisper and Faster Whisper additional arguments
USE_FASTER_WHISPER = True
# CHUNK_SIZE =  30
# CHUNK_OVERLAP = 1.0
    # For CPU: "int8". For GPU: "float16", "float32"
COMPUTE_TYPE = "float16"
BEAM_SIZE = 5
MAX_LINE_WIDTH = 42
MAX_LINE_COUNT = 2
MAX_WORDS_PER_LINE = 12
VERBOSE = True

# =========================
# Subtitle timing tweaks
# =========================
MIN_CHARS = 8                       # Minimum characters before flushing buffer
MAX_CHARS_PER_LINE = 40             # Maximum characters in a single subtitle line
MIN_DURATION = 0.3                  # Minimum seconds a subtitle is on screen
MAX_DURATION = 2.0                  # Maximum seconds a subtitle is on screen
MIN_GAP = 0.1                        # Minimum gap between consecutive subtitles (seconds)

# Folder exclusion list (can be substrings or exact names)
EXCLUDE_FOLDERS = [
    "Stargate Atlantis",
    "Stargate SG-1",
    "Stargate Universe",
    "Avatar.The.Last.Airbender.S01-S03.TVRIP.x264.BGAUDiO-GOD"
]