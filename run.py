import subprocess
import sys
from datetime import datetime
import time

# -------------------------
# CONFIG: New per-movie pipeline
# -------------------------
# Instead of running all movies through one step at a time,
# we now process one movie completely through all steps,
# then move to the next movie.

MAX_RETRIES = 3  # Number of retry attempts if pipeline fails

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def main():
    start_time = time.time()
    attempt = 1
    
    while attempt <= MAX_RETRIES:
        try:
            log(f"=== Starting per-movie pipeline (Attempt {attempt}/{MAX_RETRIES}) ===")
            
            # Run the new per-movie orchestration script
            result = subprocess.run(
                [sys.executable, "main/process_single_movie.py"],
                check=True
            )
            
            # If we got here, pipeline succeeded
            log("✅ Pipeline completed successfully!")
            break
            
        except subprocess.CalledProcessError as e:
            if attempt < MAX_RETRIES:
                log(f"⚠️ Pipeline failed with exit code {e.returncode}")
                log(f"🔄 Retrying in 5 seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(5)
                attempt += 1
            else:
                log(f"❌ Pipeline failed after {MAX_RETRIES} attempts. Giving up.")
                break
        except KeyboardInterrupt:
            log("⏸️ Pipeline interrupted by user")
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
    log(f"=== Pipeline finished on (Attempt {attempt + 1}/{MAX_RETRIES})")

if __name__ == "__main__":
    main()
