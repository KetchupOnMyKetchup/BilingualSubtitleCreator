# 🎬 Bilingual Subtitle Project
<img width="1145" height="632" alt="image" src="https://github.com/user-attachments/assets/374bb04e-7f51-459a-ac98-bd3d32e7ae66" />

This project automates the process of **transcribing, cleaning, translating, and merging bilingual subtitles files** alongside video files on a media server and naming them the same as the video file with `.<language-shorthand>.srt` for example `bg.srt` appended so that Jellyfin or similar can pick them up automatically. There are 3 main Python scripts that need to be run sequentially. All of these can be re-run on an existing directory and will check and make sure it doesn't duplicate work or files. 

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

---

## 📌 How to Run

### **Setup config file**:  
  1. Go to [the configuration file](config.py) and choose your primary and secondary languages. Set the correct ISO codes (like "en", "es", "fr") for LANG_PREFIX. 
  2. Ensure you change the `BASE_DIR` in [the configuration file](config.py) to your desired folder. 
  3. Choose your "traversal behavior" as well.

_Note: In the following instructions, I will use the example of transcribing Bulgarian (BG) audio movie files into subtitles, then translating them into secondary English (EN) which will be displayed underneath the Bulgarian subtitles._

### **Transcribe**:  
  1. Open PowerShell and start the whisper environment - `.\whisper-env\Scripts\activate` so you can run the batch whisper script. 
        - This will skip the folder if `movie.bg.srt` exists already.
  2. **[Call Open AI's Whisper Whisper](batch_whisper.py)** — Run `.\batch_whisper.py`
        - Run through Open AI's Whisper to Transcribe video's audio into Bulgarian subtitles. This will run through your target folder `BASE_DIR` and go into each folder non-recursively. 

### **Clean, Translate, and Merge BG/EN subs**:  
  _(Do the followins steps in regular PowerShell, don't need whisper env). These will run through your target folder `BASE_DIR` and go into each folder non-recursively._

  1. **[Translate & Clean (translate_subs.py)](translate_subs.py)** — Run with `python translate_subs.py` 
      - This will first call **[cleanup_subs.py](cleanup_subs.py)** — which will remove tiny/fragmented lines and normalize timing from Bulgarian subtitles. There is no need to call this script directly. 
      - If `BG_clean_*.srt` exists already, it will use the existing file and not create a dupe. 
      - Then, if `EN_clean_*.srt` does not exist yet, it will upload cleaned BG subtitles to [translatesubtitles.co](https://translatesubtitles.co) and auto-download English `.srt`.  
  2. **[Merge BG/EN cleaned subtitles (merge_subs.py)](merge_subs.py)** — Run with `python merge_subs.py`.  
        - This will combine the Bulgarian and English subs into one `.srt` (`movie.bg.srt`), with BG text above and EN text below. 
        - This will check first that `movie.bg.srt` does not exist before processing.  
        - Then, it will check that both `BG_clean_*.srt` and `EN_clean_*.srt` exist and have the same number of SRT entries.

### **Output**:  
  Each movie folder ends up with:
  - `BG_clean_*.srt` → cleaned Bulgarian subs  
  - `EN_clean_*.srt` → translated English subs  
  - `movie.bg.srt` → merged bilingual subs  

### **Logging**:  
  A `/logs` directory is created in the repo where each run’s log is timestamped for the merge step.


This is a sample of what the final .SRT file can look like:
```
2
00:00:30,000 --> 00:00:34,880
Добре, да опитаме нещо друго.
Okay, let's try something else.

3
00:00:38,420 --> 00:00:42,380
От начало. Готови. Раз, два, три.
From the beginning. Ready. One, two, three.

4
00:00:52,120 --> 00:00:56,500
Раз, два, три, четири. Дръжте ритом.
One, two, three, four. Keep the rhythm.

5
00:00:57,200 --> 00:00:59,340
Два, три, четири.
Two, three, four.
```
