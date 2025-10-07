# DO NOT run this file directly, translate_subs.py will call this
import pysrt
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import config

def clean_srt(input_file, output_file):
    """
    Clean and merge subtitles while enforcing min/max duration,
    lingering for silences, and preventing overlaps.
    """
    subs = pysrt.open(input_file)
    cleaned = pysrt.SubRipFile()

    buffer = ""
    start_time = None
    prev_end = None
    i = 1

    for idx, sub in enumerate(subs):
        text = sub.text.strip()
        if not text:
            continue

        if start_time is None:
            start_time = sub.start

        buffer += (" " if buffer else "") + text
        flush = False

        # Flush buffer if long enough or ends with punctuation
        if len(buffer) >= config.MAX_CHARS_PER_LINE or text.endswith((".", "?", "!", "…")):
            flush = True
        # Flush if duration too long
        elif start_time and (sub.end.ordinal - start_time.ordinal) / 1000 >= config.MAX_DURATION:
            flush = True

        if flush:
            # Compute reading-based duration
            reading_time = max(config.MIN_DURATION, len(buffer) / config.CHARS_PER_SECOND)

            # Calculate available gap until next subtitle
            linger = 0.0
            if idx + 1 < len(subs):
                next_start = subs[idx + 1].start
                gap = (next_start.ordinal - sub.end.ordinal) / 1000
                # Extend into the empty gap but no more than 2 seconds
                if gap > 0.3:
                    linger = min(2.0, gap)

            # Compute tentative end time (current sub end + reading + linger)
            end_time = sub.end + pysrt.SubRipTime(milliseconds=int((reading_time + linger) * 1000))

            # Do not overlap with next subtitle
            if idx + 1 < len(subs) and end_time > subs[idx + 1].start:
                end_time = subs[idx + 1].start - pysrt.SubRipTime(milliseconds=int(config.MIN_GAP * 1000))

            # Ensure no overlap with previous subtitle
            if prev_end:
                gap = (end_time.ordinal - prev_end.ordinal) / 1000
                if gap < config.MIN_GAP:
                    shift = config.MIN_GAP - gap
                    start_time = start_time + pysrt.SubRipTime(milliseconds=int(shift * 1000))
                    end_time = end_time + pysrt.SubRipTime(milliseconds=int(shift * 1000))

            cleaned.append(pysrt.SubRipItem(
                index=i,
                start=start_time,
                end=end_time,
                text=buffer.strip()
            ))

            if config.VERBOSE:
                print(f"[{start_time} --> {end_time}] {buffer.strip()}")

            buffer = ""
            start_time = None
            prev_end = end_time
            i += 1

    # Flush any remaining buffer
    if buffer:
        last_sub = subs[-1]
        # Default linger for final subtitle
        linger = 2.5  # 2.5 seconds linger if nothing follows
        end_time = last_sub.end + pysrt.SubRipTime(milliseconds=int((config.MIN_DURATION + linger) * 1000))
        if prev_end:
            gap = (end_time.ordinal - prev_end.ordinal) / 1000
            if gap < config.MIN_GAP:
                end_time = prev_end + pysrt.SubRipTime(milliseconds=int(config.MIN_GAP * 1000))

        cleaned.append(pysrt.SubRipItem(
            index=i,
            start=start_time or last_sub.start,
            end=end_time,
            text=buffer.strip()
        ))

        if config.VERBOSE:
            print(f"[{start_time} --> {end_time}] {buffer.strip()}")

    cleaned.save(output_file, encoding='utf-8')
    print(f"✅🦖 Cleaned subtitles saved to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python cleanup_subs.py input.srt output.srt")
    else:
        clean_srt(sys.argv[1], sys.argv[2])
