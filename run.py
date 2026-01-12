import subprocess
import sys
from datetime import datetime
import time

# -------------------------
# CONFIG: paths to your scripts
# -------------------------
SCRIPTS = [
    "main/extract_vocals_to_wav.py",
    "main/transcribe.py",
    "main/remove_spammy_text_srts.py",
    "main/merge_multiple_transcribe_run_srts.py",
    "main/translate_subs.py",
    "main/merge_subs.py"
]

MAX_RETRIES = 25  # Number of retry attempts if pipeline fails

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def run_script(script):
    log(f"▶ Starting {script}")
    try:
        # subprocess.run will raise CalledProcessError if script fails
        subprocess.run([sys.executable, script], check=True)
        log(f"✅ Finished {script}\n")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Script {script} failed with exit code {e.returncode}. Exception: {e}")
        return False
    except FileNotFoundError:
        log(f"❌ Script {script} not found.")
        return False

def main():
    start_time = time.time()
    attempt = 1
    
    while attempt <= MAX_RETRIES:
        try:
            log(f"=== Starting full pipeline (Attempt {attempt}/{MAX_RETRIES}) ===")
            
            for script in SCRIPTS:
                success = run_script(script)
                if not success:
                    log("⛔ Pipeline halted due to error.")
                    raise Exception(f"Script {script} failed")
            
            # If we got here, pipeline succeeded
            log("✅ Pipeline completed successfully!")
            break
            
        except Exception as e:
            if attempt < MAX_RETRIES:
                log(f"⚠️ Pipeline failed: {e}")
                log(f"🔄 Retrying in 5 seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(5)
                attempt += 1
            else:
                log(f"❌ Pipeline failed after {MAX_RETRIES} attempts. Giving up.")
                break
    
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    
    if hours > 0:
        time_str = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        time_str = f"{minutes}m {seconds}s"
    else:
        time_str = f"{seconds}s"
    
    log(f"=== Pipeline finished === (Total time: {time_str})")
    log(f"=== Pipeline finished === (Total retries during run: {attempt - 1})")

if __name__ == "__main__":
    main()
