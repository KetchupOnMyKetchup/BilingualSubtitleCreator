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
1. Run `.\setup.py`. _Note this is an unfinished project and I tried my best to get everything into the setup, I'm sorry if anything is missing from it, please open a PR if you find something missing._

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



## How This Project Works & Output Example

The main workflow is orchestrated by `run.py`, which calls the following scripts in order _(note in the following examples: Primary video audio language is Bulgarian (BG) getting translated into the Secondary language English)_:

1. **extract_vocals_to_wav.py**
    - Extracts the vocal track from each video file using Demucs (if background suppression is enabled) in order to remove background music and noises and get a clearer audio file of just speech.
    - Produces a `_vocals.wav` file for each video, which is used for transcription.

2. **transcribe.py**
    - Transcribes the audio (from the vocals `.wav` or directly from the video) into subtitles using OpenAI's Whisper or Faster-Whisper.
    - Produces a raw Bulgarian subtitle file (`BG_*.srt`).
      - For example: [BG_Soul 2020.srt](<Samples/BG_Soul 2020.srt>)

3. **cleanup_subs.py** (called automatically by the next step)
    - Cleans up the raw Bulgarian subtitles by removing tiny/fragmented lines and normalizing timing.
    - Produces a cleaned Bulgarian subtitle file (`BG_clean_*.srt`).
      - For example: [BG_clean_Soul 2020.srt](<Samples/EN_clean_Soul 2020.srt>)

4. **translate_subs.py**
    - Translates the cleaned Bulgarian subtitles into English (or your chosen second language) using an online translation service.
    - Produces a cleaned English subtitle file (`EN_clean_*.srt`).
      - For example: [EN_clean_Soul 2020.srt](<Samples/EN_clean_Soul 2020.srt>)

5. **merge_subs.py**
    - Merges the cleaned Bulgarian and English subtitles into a single bilingual `.srt` file (`movie.bg.srt`), with BG text above and EN text below each timestamp.
      - For example: [Soul 2020.bg.srt](<Samples/Soul 2020.bg.srt>)
  Each script checks for existing output files and skips processing if the expected result already exists, making the workflow resumable and efficient.

### Final Product

<img width="1151" height="632" alt="image" src="https://github.com/user-attachments/assets/2e2e8dae-a006-47d4-9548-92ff7ec0de83" />

This is a sample of what the final .SRT file can look like ([Soul 2020.bg.srt](<Samples/Soul 2020.bg.srt>)) and a small snippet is below:
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
