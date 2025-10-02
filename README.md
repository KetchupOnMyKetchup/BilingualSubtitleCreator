# 🎬 Bulgarian → English Subtitle Project

This project automates the process of **cleaning, translating, and merging Bulgarian subtitles into bilingual subtitle files** alongside movies on a media server.

---

## 📌 Project Overview

- **Input**:  
  Movie folders containing Bulgarian `.srt` subtitles (named like `BG_movie.srt`).

- **Process**:  
  1. **[Batch Whisper](batch_whisper_missing_bg.py)** — Run through Open AI's Whisper to Transcribe video's audio into Bulgarian subtitles
  2. **[translate_subs.py](translate_subs.py)** — 
      - This will first call **cleanup_subs.py** — remove tiny/fragmented lines and normalize timing from Bulgarian subtitles 
      - Then upload cleaned BG subtitles to [translatesubtitles.co](https://translatesubtitles.co) and auto-download English `.srt`.  
  4. **[Merge](merge_subs.py)** — combine the Bulgarian and English subs into one `.srt` (`movie.bg.srt`), with BG text above and EN text below which can be auto-detected by Jellyfin.

- **Output**:  
  Each movie folder ends up with:
  - `BG_clean_*.srt` → cleaned Bulgarian subs  
  - `EN_clean_*.srt` → translated English subs  
  - `movie.bg.srt` → merged bilingual subs  

- **Logging**:  
  A `/logs` directory is created in the repo where each run’s log is timestamped.

---

## ⚙️ Environment Setup

### 1. Install Python
- Install **Python 3.10+** from [python.org](https://www.python.org/downloads/)  
- During installation, check **“Add Python to PATH”**

Verify:
```bash
python --version
pip --version
```

### 2. Install Required Packages
- `pip install pysrt playwright torch torchvision torchaudio`

### 3. Enable GPU for Whisper (if using Whisper later)

Install PyTorch with CUDA matching your GPU/driver:
👉 Find the correct install command at PyTorch.org
.

Example for CUDA 12.1:

`pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`


Verify GPU is recognized:
```
import torch
print(torch.cuda.is_available())   # should be True
print(torch.cuda.get_device_name(0))
```

### 4. Install Playwright Browsers
```
playwright install
playwright install-deps
```

This ensures Chrome/Chromium is available for automation.

### 5. Install OpenAI Whisper for GPU

1. Install Whisper via pip:
```bash
pip install git+https://github.com/openai/whisper.git 
```

Ensure you have PyTorch with CUDA installed, so Whisper can use your GPU. Verify:
```
import torch
print(torch.cuda.is_available())   # should return True
```

Test Whisper with a sample audio file:
```
whisper sample.mp3 --model small --device cuda
```

Options:
- --device cuda ensures GPU usage.
- Replace small with other model sizes (tiny, base, medium, large) as needed.
- ⚠️ If Whisper doesn’t detect the GPU, make sure:
    - You installed PyTorch with CUDA (matching your GPU & driver version).
    - Your NVIDIA drivers are up to date.
    - You have a compatible GPU (CUDA-enabled).