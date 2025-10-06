import pysrt
import sys

def clean_srt(input_file, output_file, min_chars=15):
    subs = pysrt.open(input_file)
    cleaned = pysrt.SubRipFile()

    buffer = ""
    start_time = None

    # --- PHASE 1: Text merge cleanup ---
    for sub in subs:
        text = sub.text.strip()

        if not text:
            continue  # skip blank subtitles

        if start_time is None:
            start_time = sub.start

        buffer += (" " if buffer else "") + text

        # Flush if line is long or ends with punctuation
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

    if buffer:
        new_sub = pysrt.SubRipItem(
            index=len(cleaned) + 1,
            start=start_time or subs[-1].start,
            end=subs[-1].end,
            text=buffer.strip()
        )
        cleaned.append(new_sub)

    # --- PHASE 2: Timing adjustments ---
    MIN_GAP = 0.2  # sec between lines
    MIN_DURATION = 0.4  # sec per subtitle
    DRIFT_SMOOTHING = 0.00003  # gradual drift compensation factor per ms gap issue

    drift_offset = 0.0  # cumulative drift correction

    for i in range(len(cleaned)):
        sub = cleaned[i]

        # Apply gradual drift correction (helps stabilize long movies)
        sub.shift(seconds=drift_offset)

        # Ensure minimum duration
        duration = sub.end.ordinal - sub.start.ordinal
        if duration < MIN_DURATION * 1000:
            sub.end = sub.start + pysrt.timedelta(seconds=MIN_DURATION)

        # Fix overlap or too-small gap with previous
        if i > 0:
            prev = cleaned[i - 1]
            gap = (sub.start.ordinal - prev.end.ordinal) / 1000.0

            # If overlap, push it forward
            if gap < 0:
                shift = abs(gap) + MIN_GAP
                sub.shift(seconds=shift)
                drift_offset += shift * DRIFT_SMOOTHING  # accumulate drift awareness

            # If too close (< MIN_GAP), nudge it forward slightly
            elif gap < MIN_GAP:
                shift = MIN_GAP - gap
                sub.shift(seconds=shift)
                drift_offset += shift * DRIFT_SMOOTHING

        # Optional: drift correction reset if stable for long
        if i % 50 == 0 and abs(drift_offset) > 0.1:
            drift_offset *= 0.5  # dampen correction over time

    cleaned.save(output_file, encoding='utf-8')
    print(f"✅🦖 Cleaned & timing-corrected subtitles saved to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python cleanup_subs.py input.srt output.srt")
    else:
        clean_srt(sys.argv[1], sys.argv[2])
