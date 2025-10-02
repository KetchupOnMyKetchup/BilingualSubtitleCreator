import pysrt
import sys

def clean_srt(input_file, output_file, min_chars=15):
    subs = pysrt.open(input_file)
    cleaned = pysrt.SubRipFile()

    buffer = ""
    start_time = None

    for sub in subs:
        text = sub.text.strip()

        # Skip empty or blank-only subtitles
        if not text:
            continue

        if start_time is None:
            start_time = sub.start

        buffer += (" " if buffer else "") + text

        # If the line is long enough or ends with punctuation, flush it
        if len(buffer) >= min_chars or text.endswith((".", "?", "!", "…")):
            new_sub = pysrt.SubRipItem(
                index=len(cleaned) + 1,
                start=start_time,
                end=sub.end,
                text=buffer.strip()
            )
            cleaned.append(new_sub)
            buffer = ""
            start_time = None

    # If something remains in buffer, flush it
    if buffer:
        new_sub = pysrt.SubRipItem(
            index=len(cleaned) + 1,
            start=start_time or subs[-1].start,
            end=subs[-1].end,
            text=buffer.strip()
        )
        cleaned.append(new_sub)

    cleaned.save(output_file, encoding='utf-8')
    print(f"✅🦖 Cleaned subtitles saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python cleanup_subs.py input.srt output.srt")
    else:
        clean_srt(sys.argv[1], sys.argv[2])
