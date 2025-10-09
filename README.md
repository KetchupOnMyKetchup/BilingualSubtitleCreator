# 🎬 Bilingual Subtitle Project
<img width="1145" height="632" alt="image" src="https://github.com/user-attachments/assets/374bb04e-7f51-459a-ac98-bd3d32e7ae66" />

Are you learning a language and do you have a video file in a foreign language with no subtitles but you want dual subtitles in both the target language and your language? This project automates the process of **transcribing, cleaning, translating, and merging bilingual subtitles files** alongside video files on a media server and naming them the same as the video file with `.<language-shorthand>.srt` for example `bg.srt` appended (so that Jellyfin or similar can pick them up automatically). 

_Note: There are mistakes in the transcription/translation and this is far from a perfect, but I'd say it gets you ~80-90% of the way there for movies._

---

## ⚙️ Environment Setup (Install Python, Playwright, Whisper, and packages)

### Install Python
1. Install **Python 3.10+** from [python.org](https://www.python.org/downloads/)  
1. Run the installer. **IMPORTANT:** Check the box that says “Add Python 3.x to PATH” at the bottom, if not add this to PATH manually.
1. Check that it is installed correctly by running `python --version` and you should see something like `Python 3.13.1`

### Run setup script
1. Download this project
1. Navigate to your project folder on your machine in command line
1. Run `.\setup.py`

### Optional: See if GPU is enabled for Whisper and Faster Whisper
If you installed PyTorch with CUDA, you can run this to verify the GPU is recognized: `python -c "import torch; print(torch.cuda.is_available())"`
- True → GPU available
- False → GPU not detected

---

## 📌 How to Run Scripts
1. Navigate to your home directory `cd ~`
1. Run `.\whisper-env\Scripts\activate` to activate the environment the setup file installed everything into.
1. Go to [config.py](main/config.py) and change the following:
    - `BASE_DIR` - the folder of video file(s) you want subtitles for
    - `FALLBACK_SRT_DIR` - a folder on your local machine to fallback to in case it fails to write subs to your desired folder (this can happen with permissions issues on a network drive, for example)
    - `EXCLUDE_FOLDERS` - Add the names of any directories you want excluded that are part of `BASE_DIR`
    - `LANGUAGE` - Language that the video's audio is in
    - `LANG_PREFIX` - ISO codes for the language that the video's audio is in (like "EN", "ES", "FR")
    - `SECOND_LANGUAGE` - Language you want to translate into, these are the bottom/secondary subtitles
    - `SECOND_LANG_PREFIX` - ISO codes for the second language, must be a correct ISO code or translation will not work properly (like "EN", "ES", "FR")
    - `SCAN_FILES_IN_BASEDIR` - `True` if you want to scan video files inside the `BASE_DIR`, `False` if you want to skip those
    - `RECURSIVE` - `True` if you want to go into all subfolders of `BASE_DIR`, `False` if you only want top level folders to be searched
1. Navigate to where downloaded your project folder on your machine
1. Run `.\run.py`

---

## How to This Project Works
1. 

### **Transcribe**:  
  1. Open PowerShell and start the whisper environment - `.\whisper-env\Scripts\activate` so you can run the batch whisper script. 
        - This will skip the folder if `movie.bg.srt` exists already.
  2. Run `.\transcribe.py` to **[Call Open AI's Whisper Whisper](transcribe.py)**.
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
