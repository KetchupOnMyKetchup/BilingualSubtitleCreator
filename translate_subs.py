import os
import time
import subprocess
import config
from playwright.sync_api import sync_playwright

def find_srts_with_prefix(folder, prefix):
    """Return all <prefix>_*.srt files in folder."""
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().startswith(prefix.lower() + "_") and f.lower().endswith(".srt")
    ]

def find_movie_files(folder):
    """Return a list of video filenames in the folder."""
    VIDEO_EXTENSIONS = [".mp4", ".avi", ".mkv", ".mov", ".mpg", ".ts"]
    return [
        f for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS
    ]

def run_cleanup(src_srt, cleaned_srt):
    """Run cleanup_subs.py on the source file and save as cleaned_srt."""
    print(f"🧹 Cleaning {src_srt} -> {cleaned_srt} ...")
    subprocess.run(["python", "cleanup_subs.py", src_srt, cleaned_srt], check=True)

def translate_with_playwright(src_srt, out_srt, folder_path):
    """Translate using translatesubtitles.co via Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        page = browser.new_page()
        page.goto("https://translatesubtitles.co")

        page.set_input_files("input[type=file]", src_srt)
        page.select_option("select.goog-te-combo", config.SECOND_LANG_PREFIX.lower())

        page.locator("button:has-text('Translate')").first.click()
        page.wait_for_selector("h4.success-msg", state="visible", timeout=300000)

        with page.expect_download() as download_info:
            page.click("button:has-text('Download')")
        download = download_info.value
        download.save_as(out_srt)

        browser.close()

def process_movie(folder_path, movie_file):
    """Process a single movie: clean BG subtitles and translate to EN."""
    movie_name = os.path.splitext(movie_file)[0]

    if "sample" in movie_name.lower():
        print(f"⏭ Skipping sample file: {movie_file}")
        return

    # Expected file names
    bg_srt = os.path.join(folder_path, f"{config.LANG_PREFIX}_{movie_name}.srt")
    bg_clean_srt = os.path.join(folder_path, f"{config.LANG_PREFIX}_clean_{movie_name}.srt")
    en_clean_srt = os.path.join(folder_path, f"{config.SECOND_LANG_PREFIX}_clean_{movie_name}.srt")

    # Step 1: Ensure BG_clean exists
    if not os.path.exists(bg_clean_srt):
        if os.path.exists(bg_srt):
            run_cleanup(bg_srt, bg_clean_srt)
        else:
            print(f"⚠️ No BG or BG_clean subtitle found for {movie_name}, skipping.")
            return
    else:
        print(f"⏩ Using existing cleaned file: {bg_clean_srt}")

    # Skip if cleaned file is empty
    if os.path.getsize(bg_clean_srt) == 0:
        print(f"⏭ Cleaned file is empty for {movie_name}, skipping.")
        return

    # Step 2: Translate if EN_clean does not exist
    if os.path.exists(en_clean_srt):
        print(f"🐱 {en_clean_srt} already exists, skipping translation.")
        return

    translation_success = False
    try:
        translate_with_playwright(bg_clean_srt, en_clean_srt, folder_path)
        translation_success = True
    except Exception as e:
        print(f"⚠️ Translation failed for {movie_name}: {e}")
        if os.path.exists(en_clean_srt):
            print(f"🔁 Retrying translation for {movie_name}...")
            try:
                translate_with_playwright(bg_clean_srt, en_clean_srt, folder_path)
                translation_success = True
            except Exception as e2:
                print(f"❌ Retry failed for {movie_name}: {e2}")
        else:
            print(f"⏭ Skipping {movie_name}, no prior success to retry.")

    if translation_success:
        print(f"✅🦖 Translated and saved as {en_clean_srt}")

def process_folder(folder_path):
    """Process all movie files in one folder."""
    print(f"\n📂 Processing folder: {folder_path}")
    movie_files = find_movie_files(folder_path)

    if not movie_files:
        print(f"⚠️ No movie files found in {folder_path}")
        return

    for movie_file in movie_files:
        process_movie(folder_path, movie_file)

def main():
    # Optional: scan base dir directly
    if config.SCAN_FILES_IN_BASEDIR:
        print(f"📂 Scanning base directory: {config.BASE_DIR}")
        process_folder(config.BASE_DIR)

    # Recursive or flat scan
    if config.RECURSIVE:
        for root, dirs, files in os.walk(config.BASE_DIR):
            for d in dirs:
                folder_path = os.path.join(root, d)
                process_folder(folder_path)
    else:
        for folder in os.listdir(config.BASE_DIR):
            full_path = os.path.join(config.BASE_DIR, folder)
            if os.path.isdir(full_path):
                process_folder(full_path)

if __name__ == "__main__":
    main()
