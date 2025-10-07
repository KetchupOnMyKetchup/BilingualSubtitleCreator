import subprocess
import sys
from datetime import datetime

# -------------------------
# CONFIG: paths to your scripts
# -------------------------
SCRIPTS = [
    "main/extract_vocals_to_wav.py",
    "main/transcribe.py",
    "main/translate_subs.py",
    "main/merge_subs.py"
]

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
        log(f"❌ Script {script} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        log(f"❌ Script {script} not found.")
        return False

def main():
    log("=== Starting full pipeline ===")
    for script in SCRIPTS:
        success = run_script(script)
        if not success:
            log("⛔ Pipeline halted due to error.")
            break
    log("=== Pipeline finished ===")

if __name__ == "__main__":
    main()
