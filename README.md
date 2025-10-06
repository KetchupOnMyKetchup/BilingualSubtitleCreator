# 🎬 Bilingual Subtitle Project
<img width="1145" height="632" alt="image" src="https://github.com/user-attachments/assets/374bb04e-7f51-459a-ac98-bd3d32e7ae66" />

Are you learning a language and do you have a video file in a foreign language with no subtitles but you want dual subtitles in both the target language and your language?

This project automates the process of **transcribing, cleaning, translating, and merging bilingual subtitles files** alongside video files on a media server and naming them the same as the video file with `.<language-shorthand>.srt` for example `bg.srt` appended so that Jellyfin or similar can pick them up automatically. 
- There are 3 main Python scripts that need to be run sequentially. All of these can be re-run on an existing directory and will check and make sure it doesn't duplicate work or files.
- This will output you 3 subtitle files that you can use with your video, 1 in the language of the video, 1 in your target translated video, and 1 bilingual subtitle with a merge of both languages.

I created this project because I am learning Bulgarian from English, and it helps me a lot to have subtitles that match the spoken audio more closely and a direct translation of those words into English so I can better learn new vocabularly.

_Note: There are, of course, errors and this is far from a perfect transcription or translation but I'd say it gets you ~80-90% of the way there for movies with clear diction and little background noise. Some known errors include: adding subs when there is no speech, sub dupes, getting the wrong words when the audio is murky/hard to hear/accented/robotic, difficulty with handling transcriptions in songs, subtitles that are too long from run-on sentences, etc._

---

## ⚙️ Environment Setup (Install Python, Playwright, Whisper, and packages)

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

### 3. Install OpenAI Whisper for GPU

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

### 4. Install Faster Whisper for GPU
1. Run:
```
.\whisper-env\Scripts\activate
pip install "faster-whisper[all]"
python -c "from faster_whisper import WhisperModel; print('Faster-Whisper installed!')"
```

### 5. Install Playwright Browsers
```
.\whisper-env\Scripts\activate
pip install playwright
playwright install
playwright install-deps
```

This ensures Chrome/Chromium is available for automation.

### 6. Enable GPU for Whisper

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


---

## 📌 How to Run Scripts

### **Setup config file**:  
  1. Go to [the configuration file](config.py) and choose your primary and secondary languages. Set the correct ISO codes (like "en", "es", "fr") for LANG_PREFIX. 
  2. Ensure you change the `BASE_DIR` in [the configuration file](config.py) to your desired folder. 
  3. Choose your "traversal behavior" as well.

_Note: In the following instructions, I will use the example of transcribing Bulgarian (BG) audio movie files into subtitles, then translating them into secondary English (EN) which will be displayed underneath the Bulgarian subtitles._

### **Transcribe**:  
  1. Open PowerShell and start the whisper environment - `.\whisper-env\Scripts\activate` so you can run the batch whisper script. 
        - This will skip the folder if `movie.bg.srt` exists already.
  2. Run `.\batch_whisper.py` to **[Call Open AI's Whisper Whisper](batch_whisper.py)**.
        - Run through Open AI's Whisper to Transcribe video's audio into Bulgarian subtitles. This will run through your target folder `BASE_DIR`.
        - This could take ~10 mins - 30 mins per 1.5-2 hour video, for example if you are using a fast GPU, longer with CPU or older GPUs.

### **Clean, Translate, and Merge BG/EN subs**:  
  _(Do the following steps in regular PowerShell, don't need whisper env. Or call them with whatever shell or OS you prefer to use). These will run through your target folder `BASE_DIR` and go into each folder non-recursively._

  1. Run with `python translate_subs.py` to **[Translate & Clean (translate_subs.py)](translate_subs.py)** —  
      - This will first call **[cleanup_subs.py](cleanup_subs.py)** — which will remove tiny/fragmented lines and normalize timing from Bulgarian subtitles. There is no need to call this script directly. 
      - If `BG_clean_*.srt` exists already, it will use the existing file and not create a dupe. 
      - Then, if `EN_clean_*.srt` does not exist yet, it will upload cleaned BG subtitles to [translatesubtitles.co](https://translatesubtitles.co) and auto-download English `.srt`.  
      - This could take ~1-3 mins per 1.5-2 hour video. It has a high failure rate due to issues uploading to the webpage and sometimes coming up empty or timing out, so don't worry about cancelling and restarting this a few times. 
  2. Run with `python merge_subs.py` to **[Merge BG/EN cleaned subtitles (merge_subs.py)](merge_subs.py)** —  
        - This will combine the Bulgarian and English subs into one `.srt` (`movie.bg.srt`), with BG text above and EN text below. 
        - This will check first that `movie.bg.srt` does not exist before processing.  
        - Then, it will check that both `BG_clean_*.srt` and `EN_clean_*.srt` exist and have the same number of SRT entries.
        - This is super fast and can run through 50+ movies in a couple of minutes. 

### **Logging**:  
  A `/logs` directory is created in the repo where each run’s log is timestamped for the merge step.

---

### **Output & Sample Subtitle Files Generated**:  
  Each movie folder ends up with:
  - `BG_*.srt` → raw Bulgarian subs
    - For example - [BG_Soul 2020.srt](<Samples/BG_Soul 2020.srt>)
  - `BG_clean_*.srt` → cleaned Bulgarian subs  
      - For example - [EN_clean_Soul 2020.srt](<Samples/EN_clean_Soul 2020.srt>)
  - `EN_clean_*.srt` → translated English subs  
      - For example - [EN_clean_Soul 2020.srt](<Samples/EN_clean_Soul 2020.srt>)
  - `movie.bg.srt` → merged bilingual subs  
      - For example - [Soul 2020.bg.srt](<Samples/Soul 2020.bg.srt>)

<img width="1151" height="632" alt="image" src="https://github.com/user-attachments/assets/2e2e8dae-a006-47d4-9548-92ff7ec0de83" />

This is a sample of what the final .SRT file can look like [Soul 2020.bg.srt](<Samples/Soul 2020.bg.srt>) and a small snippet is below:
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
