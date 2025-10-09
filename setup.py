import os
import subprocess
import sys

VENV_NAME = "whisper-env-test2"

def run(cmd, check=True):
    """Run a shell command with live output."""
    print(f"\n🔧 Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=check)

def create_virtualenv(env_name=VENV_NAME):
    """Create the virtual environment if it doesn't exist."""
    if not os.path.exists(env_name):
        print(f"📦 Creating virtual environment: {env_name}")
        run([sys.executable, "-m", "venv", env_name])
    else:
        print(f"✅ Virtual environment already exists: {env_name}")

def install_packages():
    """Install all dependencies required for the full pipeline."""
    pip_path = os.path.join(VENV_NAME, "Scripts", "pip") if os.name == "nt" else os.path.join(VENV_NAME, "bin", "pip")

    # Upgrade pip/wheel/setuptools first
    run([pip_path, "install", "--upgrade", "pip", "wheel", "setuptools"])

    # Torch + torchaudio — try CUDA first, fallback to CPU
    try:
        print("\n🚀 Installing PyTorch + torchaudio with CUDA (if available)...")
        run([pip_path, "install", "--no-cache-dir", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu121"])
    except subprocess.CalledProcessError:
        print("\n⚙️ CUDA install failed, installing CPU-only PyTorch instead.")
        run([pip_path, "install", "--no-cache-dir", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"])

    # Whisper + Faster Whisper + pysrt
    run([pip_path, "install", "--no-cache-dir", "openai-whisper", "faster-whisper", "pysrt", "pydub"])

    # Demucs
    run([pip_path, "install", "--no-cache-dir", "demucs"])

    # Playwright (for translation automation)
    run([pip_path, "install", "--no-cache-dir", "playwright"])
    # Install Playwright browser binaries
    python_path = pip_path.replace('pip', 'python')
    run([python_path, "-m", "playwright", "install"])

    # Utilities
    run([pip_path, "install", "--no-cache-dir", "numpy", "ffmpeg-python", "tqdm", "pydub", "langdetect", "googletrans==4.0.0-rc1"])

    print("\n✅ All dependencies installed successfully!")

def print_activation_instructions():
    """Show how to activate the virtual environment."""
    if os.name == "nt":
        print(f"\n💡 To activate the environment, run:\n   .\\{VENV_NAME}\\Scripts\\activate")
    else:
        print(f"\n💡 To activate the environment, run:\n   source {VENV_NAME}/bin/activate")

    print("\nThen you can run your pipeline scripts, e.g.:")
    print("   python main/extract_vocals_to_wav.py")
    print("   python main/transcribe.py")
    print("   python main/translate_subs.py")
    print("   python main/merge_subs.py")

def main():
    print("🎬 Setting up your Whisper + Demucs environment...\n")
    create_virtualenv()
    install_packages()
    print_activation_instructions()

if __name__ == "__main__":
    main()
