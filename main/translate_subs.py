import os
import subprocess
import time
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
    return [
        f for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in config.VIDEO_EXTENSIONS
    ]


def run_cleanup(src_srt, cleaned_srt):
    """Run cleanup_subs.py on the source file and save as cleaned_srt."""
    print(f"🧹 Cleaning {src_srt} -> {cleaned_srt} ...")
    subprocess.run(["python", "main/additional/cleanup_subs.py", src_srt, cleaned_srt], check=True)


def translate_with_playwright(src_srt, out_srt, folder_path):
    """Translate using translatesubtitles.co via Playwright, retrying if the first translation finishes too early."""
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        page = browser.new_page()
        page.goto("https://translatesubtitles.co")

        # Upload cleaned subtitle
        page.set_input_files("input[type=file]", src_srt)

        # Select target language and verify it's applied
        page.select_option("select.goog-te-combo", config.SECOND_LANG_PREFIX.lower())
        page.wait_for_function(
            f"() => document.querySelector('select.goog-te-combo').value === '{config.SECOND_LANG_PREFIX.lower()}'"
        )

        # Capture original text before translation
        original_text = ""
        try:
            original_text = page.eval_on_selector(
                "td.notranslate.target-sub", "el => el.textContent"
            ) or ""
        except Exception:
            pass

        # Click Translate
        print("🕹️ Clicking Translate...")
        page.locator("button:has-text('Translate')").first.click()

        # Wait for the success message
        page.wait_for_selector("h4.skiptranslate.success-msg", state="visible", timeout=120000)

        # Wait for translated text to change
        print("⌛ Waiting for text to change...")
        translation_changed = False
        try:
            page.wait_for_function(
                """(orig) => {
                    const el = document.querySelector('td.notranslate.target-sub');
                    return el && el.textContent.trim() !== orig.trim() && el.textContent.trim() !== '';
                }""",
                arg=original_text,
                timeout=10000,  # short initial wait to handle short subtitles file bug. Was failing on SRT files for videos < 1 min long
            )
            translation_changed = True
        except Exception:
            print("⚠️ No text change yet, retrying translate click once...")

        # If not changed, click Translate again once
        if not translation_changed:
            try:
                page.locator("button:has-text('Translate')").first.click()
                page.wait_for_selector("h4.skiptranslate.success-msg", state="visible", timeout=60000)
                page.wait_for_function(
                    """(orig) => {
                        const el = document.querySelector('td.notranslate.target-sub');
                        return el && el.textContent.trim() !== orig.trim() && el.textContent.trim() !== '';
                    }""",
                    arg=original_text,
                    timeout=30000,
                )
                print("✅ Translation confirmed after retry.")
            except Exception:
                print("⚠️ Retry translate click didn’t help — proceeding anyway (may be untranslated).")

        # Brief pause for safety
        page.wait_for_timeout(1000)

        # Trigger download
        with page.expect_download() as download_info:
            page.locator("button:has-text('Download')").click()
        download = download_info.value
        download.save_as(out_srt)

        browser.close()


def process_movie(folder_path, movie_file):
    """Process a single movie: clean primary subtitles and translate to secondary language."""
    movie_name = os.path.splitext(movie_file)[0]

    if "sample" in movie_name.lower():
        print(f"⏭ Skipping sample file: {movie_file}")
        return

    # Expected file names
    bg_srt = os.path.join(folder_path, f"{config.LANG_PREFIX}_{movie_name}.srt")
    bg_clean_srt = os.path.join(folder_path, f"{config.LANG_PREFIX}_clean_{movie_name}.srt")
    second_clean_srt = os.path.join(folder_path, f"{config.SECOND_LANG_PREFIX}_clean_{movie_name}.srt")

    # Step 1: Ensure cleaned primary exists
    if not os.path.exists(bg_clean_srt):
        if os.path.exists(bg_srt):
            run_cleanup(bg_srt, bg_clean_srt)
        else:
            print(f"⚠️ No {config.LANG_PREFIX} or cleaned subtitle found for {movie_name}, skipping.")
            return
    else:
        print(f"⏩ Using existing cleaned file: {bg_clean_srt}")

    # Skip if cleaned file is empty
    if os.path.getsize(bg_clean_srt) == 0:
        print(f"⏭ Cleaned file is empty for {movie_name}, skipping.")
        return

    # Step 2: Translate if secondary cleaned does not exist
    if os.path.exists(second_clean_srt):
        print(f"🐱 {second_clean_srt} already exists, skipping translation.")
        return

    translation_success = False
    try:
        translate_with_playwright(bg_clean_srt, second_clean_srt, folder_path)
        translation_success = True
    except Exception as e:
        print(f"⚠️ Translation failed for {movie_name}: {e}")
        if os.path.exists(second_clean_srt):
            print(f"🔁 Retrying translation for {movie_name}...")
            try:
                translate_with_playwright(bg_clean_srt, second_clean_srt, folder_path)
                translation_success = True
            except Exception as e2:
                print(f"❌ Retry failed for {movie_name}: {e2}")
        else:
            print(f"⏭ Skipping {movie_name}, no prior success to retry.")

    if translation_success:
        print(f"✅🦖 Translated and saved as {second_clean_srt}")


def process_folder(folder_path):
    """Process all movie files in one folder."""
    folder_name = os.path.basename(folder_path)
    if folder_name in getattr(config, "EXCLUDE_FOLDERS", []):
        print(f"🚫 Skipping excluded folder: {folder_name}")
        return

    print(f"\n📂 Processing folder: {folder_path}")
    movie_files = find_movie_files(folder_path)

    if not movie_files:
        print(f"⚠️ No movie files found in {folder_path}")
        return

    for movie_file in movie_files:
        process_movie(folder_path, movie_file)


def main():
    exclude_list = set(getattr(config, "EXCLUDE_FOLDERS", []))

    # Optional: scan base dir directly
    if config.SCAN_FILES_IN_BASEDIR and os.path.basename(config.BASE_DIR) not in exclude_list:
        print(f"📂 Scanning base directory: {config.BASE_DIR}")
        process_folder(config.BASE_DIR)
    elif os.path.basename(config.BASE_DIR) in exclude_list:
        print(f"🚫 Base directory {config.BASE_DIR} is excluded — skipping.")

    # Recursive or flat scan
    if config.RECURSIVE:
        for root, dirs, files in os.walk(config.BASE_DIR):
            dirs[:] = [d for d in dirs if d not in exclude_list]
            for d in dirs:
                folder_path = os.path.join(root, d)
                process_folder(folder_path)
    else:
        for folder in os.listdir(config.BASE_DIR):
            if folder in exclude_list:
                print(f"🚫 Skipping excluded folder: {folder}")
                continue
            full_path = os.path.join(config.BASE_DIR, folder)
            if os.path.isdir(full_path):
                process_folder(full_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Single movie mode: process specific movie file
        movie_path = sys.argv[1]
        if os.path.exists(movie_path):
            folder_path = os.path.dirname(movie_path)
            movie_file = os.path.basename(movie_path)
            print(f"Processing single movie: {movie_file}")
            process_movie(folder_path, movie_file)
        else:
            print(f"Error: Movie file not found: {movie_path}")
            sys.exit(1)
    else:
        # Process all movies
        main()
