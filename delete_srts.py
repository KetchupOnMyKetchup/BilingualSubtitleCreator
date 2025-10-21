# Cleanup script to delete .srt files based on configuration settings
import os
from pathlib import Path
import config

def delete_srt_files(base_dir):
    """Delete all .srt files in BASE_DIR following config rules."""
    base_dir = Path(base_dir)
    if not base_dir.exists():
        print(f"❌ BASE_DIR not found: {base_dir}")
        return

    deleted_count = 0

    # --- Scan BASE_DIR directly if enabled ---
    if getattr(config, "SCAN_FILES_IN_BASEDIR", True):
        for f in base_dir.iterdir():
            if f.is_file() and f.suffix.lower() == ".srt":
                try:
                    f.unlink()
                    print(f"🗑️ Deleted {f.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to delete {f.name}: {e}")

    # --- Recursively scan subfolders if enabled ---
    if getattr(config, "RECURSIVE", True):
        for root, dirs, files in os.walk(base_dir):
            # Remove excluded folders from traversal
            dirs[:] = [d for d in dirs if d not in getattr(config, "EXCLUDE_FOLDERS", [])]

            for file in files:
                if file.lower().endswith(".srt"):
                    file_path = Path(root) / file
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