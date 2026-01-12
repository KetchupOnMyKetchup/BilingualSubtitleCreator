# Cleanup script to delete .srt files based on configuration settings
import os
from pathlib import Path
import main.config as config

def delete_srt_files(base_dir):
    """
    Delete all .srt files in BASE_DIR following config rules.
    
    Config options:
    - SCAN_FILES_IN_BASEDIR: whether to delete .srt files directly in BASE_DIR
    - RECURSIVE: whether to recurse into subdirectories
    - EXCLUDE_FOLDERS: list of folder names to skip (prevents traversal)
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        print(f"❌ BASE_DIR not found: {base_dir}")
        return

    deleted_count = 0
    exclude_folders = set(getattr(config, "EXCLUDE_FOLDERS", []))
    scan_base = getattr(config, "SCAN_FILES_IN_BASEDIR", True)
    recurse = getattr(config, "RECURSIVE", True)

    if not scan_base and not recurse:
        print("⚠️ Both SCAN_FILES_IN_BASEDIR and RECURSIVE are False. Nothing to do.")
        return

    # Use os.walk for unified handling (respects directory structure)
    for root, dirs, files in os.walk(base_dir):
        current_path = Path(root)
        
        # Check if current directory should be skipped
        if current_path != base_dir:  # Don't exclude BASE_DIR itself
            # Check if any parent is in EXCLUDE_FOLDERS
            if current_path.name in exclude_folders:
                dirs.clear()  # Don't recurse into this folder
                continue
        
        # Skip this level if not at base_dir and RECURSIVE is False
        if current_path != base_dir and not recurse:
            dirs.clear()
            continue
        
        # Remove excluded folders from traversal (prevents os.walk from entering them)
        dirs[:] = [d for d in dirs if d not in exclude_folders]
        
        # Delete .srt files in current directory
        for file in files:
            if file.lower().endswith(".srt"):
                file_path = current_path / file
                try:
                    file_path.unlink()
                    print(f"🗑️ Deleted {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to delete {file_path}: {e}")

    print(f"\n✅ Finished deleting .srt files. Total deleted: {deleted_count}")


if __name__ == "__main__":
    base = getattr(config, "BASE_DIR", None)
    if not base:
        print("❌ BASE_DIR is not defined in config.py")
    else:
        delete_srt_files(base)