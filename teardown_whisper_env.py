import shutil
import os

# ---------- CONFIG ----------
VENV_NAME = "whisper-env-test2"
# ----------------------------

def delete_virtualenv(env_name=VENV_NAME):
    if os.path.exists(env_name):
        try:
            shutil.rmtree(env_name)
            print(f"✅ Virtual environment '{env_name}' deleted successfully.")
        except Exception as e:
            print(f"❌ Failed to delete '{env_name}': {e}")
    else:
        print(f"⚠ Virtual environment '{env_name}' does not exist.")

if __name__ == "__main__":
    delete_virtualenv()
