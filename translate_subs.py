import os
import time
import subprocess
import config
from playwright.sync_api import sync_playwright

# Base movies folder
BASE_DIR = r"\\192.168.1.5\Media\Movies"

def find_lang_srt(folder, prefix):
    """Return path to <prefix>_*.srt file if exists, else None."""
    for f in os.listdir(folder):
        if f.lower().startswith(prefix.lower() + "_") and f.lower().endswith(".srt"):
            return os.path.join(folder, f)
    return None

def has_second_lang_srt(folder, prefix):
    """Check if a <prefix>_*.srt file already exists."""
    return any(f.lower().startswith(prefix.lower() + "_") and f.lower().endswith(".srt") for f in os.listdir(folder))

def run_cleanup(src_srt, cleaned_srt):
    """Run cleanup_subs.py on the source file and save as cleaned_srt."""
    print(f"🧹 Cleaning {src_srt} -> {cleaned_srt} ...")
    subprocess.run(["python", "cleanup_subs.py", src_srt, cleaned_srt], check=True)

def translate_with_playwright(src_srt, out_srt, full_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        page = browser.new_page()
        page.goto("https://translatesubtitles.co")

        # Upload subtitle
        page.set_input_files("input[type=file]", src_srt)

        # Select target language in dropdown (config.SECOND_LANGUAGE)
        # NOTE: Google Translate expects lowercase ISO codes (like "en", "es", "fr")
        page.select_option("select.goog-te-combo", config.SECOND_LANG_PREFIX.lower())

        # Click Translate button
        page.locator("button:has-text('Translate')").first.click()

        # Wait for success message
        page.wait_for_selector("h4.success-msg", state="visible", timeout=300000)

        # Download translated file
        with page.expect_download() as download_info:
            page.click("button:has-text('Download')")
        download = download_info.value
        download.save_as(out_srt)

        browser.close()

def main():
    for folder in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, folder)
        if not os.path.isdir(full_path):
            continue

        # Look for source language subtitles
        src_srt = find_lang_srt(full_path, config.LANG_PREFIX)
        if not src_srt:
            print(f"⏭ No {config.LANG_PREFIX}_*.srt in {folder}, skipping")
            continue

        # Skip if target language already exists
        if has_second_lang_srt(full_path, config.SECOND_LANG_PREFIX):
            print(f"🐱 {config.SECOND_LANG_PREFIX}_*.srt already exists in {folder}, skipping")
            continue

        # Construct output filename (SECOND_LANG)
        filename = os.path.basename(src_srt)
        out_srt = os.path.join(
            full_path,
            filename.replace(f"{config.LANG_PREFIX}_", f"{config.SECOND_LANG_PREFIX}_clean_", 1)
                   .replace(f"-{config.LANG_PREFIX}", "")
        )

        # Step 1: Cleanup
        if filename.startswith(f"{config.LANG_PREFIX}_clean_"):
            cleaned_srt_name = filename
        else:
            cleaned_srt_name = filename.replace(f"{config.LANG_PREFIX}_", f"{config.LANG_PREFIX}_clean_", 1)

        cleaned_srt = os.path.join(full_path, cleaned_srt_name)

        if not os.path.exists(cleaned_srt):
            run_cleanup(src_srt, cleaned_srt)
        else:
            print(f"⏩ Using existing cleaned file: {cleaned_srt}")

        # Skip if cleaned file is empty
        if os.path.getsize(cleaned_srt) == 0:
            print(f"⏭ Cleaned file is empty for {folder}, skipping")
            continue

        # Step 2: Translate with retry
        translation_success = False
        try:
            translate_with_playwright(cleaned_srt, out_srt, full_path)
            translation_success = True
        except Exception as e:
            print(f"⚠️ Translation failed for {full_path}: {e}")
            if os.path.exists(out_srt):
                print(f"🔁 Retrying translation for {full_path}...")
                try:
                    translate_with_playwright(cleaned_srt, out_srt, full_path)
                    translation_success = True
                except Exception as e2:
                    print(f"❌ Retry failed for {full_path}: {e2}")
            else:
                print(f"⏭ Skipping {full_path}, no prior success to retry.")

        if translation_success:
            print(f"✅🦖 Saved {config.SECOND_LANGUAGE} subs as {out_srt}")

if __name__ == "__main__":
    main()
