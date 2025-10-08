# DO NOT run this file directly, translate_subs.py will call this
import pysrt
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import config

def _add_seconds_to_srt_time(srt_time, seconds):
    """Return a new SubRipTime that is srt_time + seconds (float)."""
    ms = int(seconds * 1000)
    return srt_time + pysrt.SubRipTime(milliseconds=ms)

def clean_srt(input_file, output_file):
    # Try to open input SRT; if unreadable, exit cleanly
    try:
        subs = pysrt.open(input_file)
    except Exception as e:
        print(f"❌ Could not open {input_file}: {e}")
        return

    if not subs:
        print(f"⏭ Input subtitle {input_file} is empty — nothing to clean.")
        # create an empty output to be explicit
        pysrt.SubRipFile().save(output_file, encoding='utf-8')
        print(f"✅ Cleaned (empty) subtitles saved to {output_file}")
        return

    cleaned = pysrt.SubRipFile()

    buffer = ""
    start_time = None            # pysrt.SubRipTime for buffer start
    last_included_sub_end = None # pysrt.SubRipTime of last included sub.end
    prev_end = None              # end time of previously appended cleaned subtitle
    i = 1

    for idx, sub in enumerate(subs):
        # Defensive: ensure sub has text
        text = (sub.text or "").strip()
        if not text:
            # no spoken text here; skip but keep potential start_time if we are buffering
            continue

        # If starting a new buffer, record start_time as this sub's start
        if start_time is None:
            start_time = sub.start
            last_included_sub_end = sub.end
        else:
            # extend last included end to this sub's end since we're adding this sub to the buffer
            if sub.end > last_included_sub_end:
                last_included_sub_end = sub.end

        buffer += (" " if buffer else "") + text

        # Decide whether to flush now
        flush = False

        # Flush if buffer is long enough, ends with punctuation, or has grown too long duration-wise
        if len(buffer) >= getattr(config, "MAX_CHARS_PER_LINE", 40) or text.endswith((".", "?", "!", "…")):
            flush = True
        else:
            # duration of the original included content (from buffer start to last included sub end)
            original_span_sec = (last_included_sub_end.ordinal - start_time.ordinal) / 1000.0
            if original_span_sec >= getattr(config, "MAX_DURATION", 2.0):
                flush = True

        if not flush:
            # continue aggregating
            continue

        # Compute reading_time based on characters in buffer
        chars_per_second = getattr(config, "CHARS_PER_SECOND", 15)
        min_duration = getattr(config, "MIN_DURATION", 0.3)
        max_duration = getattr(config, "MAX_DURATION", 2.0)

        reading_time = max(min_duration, len(buffer) / max(1.0, chars_per_second))
        # Cap reading_time to max_duration for safety
        reading_time = min(reading_time, max_duration)

        # Base end_time candidate: prefer start_time + reading_time (so the text stays long enough for user)
        end_time_candidate = _add_seconds_to_srt_time(start_time, reading_time)

        # Ensure end_time is at least the original last included sub.end (don't cut speech)
        end_time = last_included_sub_end if last_included_sub_end > end_time_candidate else end_time_candidate

        # Consider lingering if next subtitle is far away
        linger = 0.0
        if idx + 1 < len(subs):
            # compute gap between last included sub end and next sub start
            next_start = subs[idx + 1].start
            gap = (next_start.ordinal - last_included_sub_end.ordinal) / 1000.0
            if gap > 0.3:
                # linger up to 2 seconds but not more than the available gap minus a small buffer
                linger = min(2.0, max(0.0, gap - 0.05))

        # Add linger
        if linger > 0:
            end_time = _add_seconds_to_srt_time(end_time, linger)

        # Do not overlap the next subtitle: enforce end_time <= next_start - MIN_GAP
        if idx + 1 < len(subs):
            next_start = subs[idx + 1].start
            min_gap = getattr(config, "MIN_GAP", 0.1)
            limit = pysrt.SubRipTime(milliseconds=int(( (next_start.ordinal - pysrt.SubRipTime(0,0,0,0).ordinal) / 1000.0 - min_gap ) * 1000))
            # Simpler: if end_time >= next_start - min_gap, set end_time to that bound:
            bound = next_start - pysrt.SubRipTime(milliseconds=int(min_gap * 1000))
            if end_time >= bound:
                end_time = bound

        # Ensure we don't start earlier than prev_end (shouldn't happen normally), if too close shift forward
        if prev_end:
            gap_from_prev = (start_time.ordinal - prev_end.ordinal) / 1000.0
            if gap_from_prev < getattr(config, "MIN_GAP", 0.1):
                # shift both start and end forward so there's MIN_GAP after prev_end
                shift = getattr(config, "MIN_GAP", 0.1) - gap_from_prev
                start_time = _add_seconds_to_srt_time(start_time, shift)
                end_time = _add_seconds_to_srt_time(end_time, shift)

        # Finally, append the cleaned subtitle
        cleaned.append(pysrt.SubRipItem(
            index=i,
            start=start_time,
            end=end_time,
            text=buffer.strip()
        ))

        if getattr(config, "VERBOSE", False):
            print(f"[{start_time} --> {end_time}] {buffer.strip()}")

        # Prepare for next buffer
        prev_end = end_time
        buffer = ""
        start_time = None
        last_included_sub_end = None
        i += 1

    # Flush any remaining buffer if present
    if buffer:
        # Use the last parsed sub as base for end time if available
        last_sub = subs[-1]
        chars_per_second = getattr(config, "CHARS_PER_SECOND", 15)
        min_duration = getattr(config, "MIN_DURATION", 0.3)
        reading_time = max(min_duration, len(buffer) / max(1.0, chars_per_second))
        # Give a slightly larger linger at the end of file so text stays readable
        final_linger = min(3.0, reading_time + 2.0)

        end_time = _add_seconds_to_srt_time(last_sub.end, final_linger)

        # Avoid tiny overlap with previous cleaned subtitle
        if prev_end:
            gap = (end_time.ordinal - prev_end.ordinal) / 1000.0
            if gap < getattr(config, "MIN_GAP", 0.1):
                end_time = _add_seconds_to_srt_time(prev_end, getattr(config, "MIN_GAP", 0.1))

        cleaned.append(pysrt.SubRipItem(
            index=i,
            start=start_time or last_sub.start,
            end=end_time,
            text=buffer.strip()
        ))

        if getattr(config, "VERBOSE", False):
            print(f"[{start_time or last_sub.start} --> {end_time}] {buffer.strip()}")

    # Save cleaned file
    try:
        cleaned.save(output_file, encoding='utf-8')
        print(f"✅🦖 Cleaned subtitles saved to {output_file}")
    except Exception as e:
        print(f"❌ Could not save cleaned subtitles to {output_file}: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python cleanup_subs.py input.srt output.srt")
    else:
        clean_srt(sys.argv[1], sys.argv[2])
