# config.py

# Path to your Movies folder
BASE_DIR = r"\\192.168.1.5\Media\Movies"

# Recognized video extensions
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mkv", ".mov", ".mpg", ".ts"]

# Whisper settings
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
SCAN_FILES_IN_BASEDIR = False   # True = scan video files in BASE_DIR itself, False = skip them
RECURSIVE = False              # True = recurse into subfolders of subfolders, False = only top-level subfolders
PROCESS_ONE_PER_FOLDER = True  # True = process only first valid video per folder, False = process all

# Fallback folder for saving .srt if target folder fails
FALLBACK_SRT_DIR = r"C:\Users\caten\Desktop"

# Folder exclusion list (can be substrings or exact names)
EXCLUDE_FOLDERS = [
    "Stargate Atlantis",
    "Stargate SG-1",
    "Stargate Universe"
]