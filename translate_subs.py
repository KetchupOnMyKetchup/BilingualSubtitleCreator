import os
import time
import subprocess
from playwright.sync_api import sync_playwright

# Base movies folder
BASE_DIR = r"\\192.168.1.5\Media\Movies"

def find_bg_srt(folder):
    """Return path to BG_*.srt file if exists, else None."""
    for f in os.listdir(folder):
        if f.lower().startswith("bg_") and f.lower().endswith(".srt"):
            return os.path.join(folder, f)
    return None

def has_en_srt(folder):
    """Check if an EN_*.srt file already exists."""
    return any(f.lower().startswith("en_") and f.lower().endswith(".srt") for f in os.listdir(folder))

def run_cleanup(bg_srt, cleaned_srt):
    """Run cleanup_subs.py on the BG file and save as cleaned_srt."""
    print(f"🧹 Cleaning {bg_srt} -> {cleaned_srt} ...")
    subprocess.run(["python", "cleanup_subs.py", bg_srt, cleaned_srt], check=True)


def translate_with_playwright(bg_srt, en_srt, full_path):
    with sync_playwright() as p:
        # Use Chrome instead of default Chromium
        browser = p.chromium.launch(channel="chrome", headless=False)
        page = browser.new_page()
        page.goto("https://translatesubtitles.co")

        # Upload subtitle
        page.set_input_files("input[type=file]", bg_srt)

        # Select English in Google Translate dropdown
        page.select_option("select.goog-te-combo", "en")
        
        # Click the correct Translate button
        page.locator("button:has-text('Translate')").first.click()

        # Wait for "Subtitle Translated!" message to actually be visible (green text)
        page.wait_for_selector("h4.success-msg", state="visible", timeout=300000)

        # Download translated file
        with page.expect_download() as download_info:
            page.click("button:has-text('Download')")
        download = download_info.value
        download.save_as(en_srt)

        browser.close()

def main():
    for folder in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, folder)
        if not os.path.isdir(full_path):
            continue

        bg_srt = find_bg_srt(full_path)
        if not bg_srt:
            print(f"⏭ No BG_*.srt in {folder}, skipping")
            continue

        if has_en_srt(full_path):
            print(f"🐱 EN_*.srt already exists in {folder}, skipping")
            continue

        # Construct EN_ filename
        filename = os.path.basename(bg_srt)
        en_srt = os.path.join(full_path, filename.replace("BG_", "EN_clean_", 1).replace("-BG", ""))

        # Step 1: Cleanup
        filename = os.path.basename(bg_srt)

        # If already cleaned, keep name; otherwise add BG_clean_ prefix
        if filename.startswith("BG_clean_"):
            cleaned_srt_name = filename
        else:
            cleaned_srt_name = filename.replace("BG_", "BG_clean_", 1)

        cleaned_srt = os.path.join(full_path, cleaned_srt_name)

        # Only clean if the cleaned file doesn't already exist
        if not os.path.exists(cleaned_srt):
            run_cleanup(bg_srt, cleaned_srt)
        else:
            print(f"⏩ Using existing cleaned file: {cleaned_srt}")

        # ✅🦖 Skip if cleaned file is empty
        if os.path.getsize(cleaned_srt) == 0:
            print(f"⏭ Cleaned file is empty for {folder}, skipping")
            continue

        # Step 2: Translate with retry
        translation_success = False
        try:
            translate_with_playwright(cleaned_srt, en_srt, full_path)
            translation_success = True
        except Exception as e:
            print(f"⚠️ Translation failed for {full_path}: {e}")
            # Retry once if previous translation succeeded for this folder
            if os.path.exists(en_srt):
                print(f"🔁 Retrying translation for {full_path}...")
                try:
                    translate_with_playwright(cleaned_srt, en_srt, full_path)
                    translation_success = True
                except Exception as e2:
                    print(f"❌ Retry failed for {full_path}: {e2}")
            else:
                print(f"⏭ Skipping {full_path}, no prior success to retry.")

        if translation_success:
            print(f"✅🦖 Saved English subs as {en_srt}")

if __name__ == "__main__":
    main()
