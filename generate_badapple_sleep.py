#!/usr/bin/env python3
"""Convert Bad Apple video frames into sleep data CSV files.

Each frame maps to one night of sleep. The frame is divided into 4 horizontal
strips (Awake, REM, Core, Deep) and 48 time columns (10 min each, 22:00-06:00).
Dark pixels in a strip-column cell activate that sleep stage for that time slot.

Usage:
    source .venv/bin/activate
    python generate_badapple_sleep.py [--fps 15] [--interval 10] [--threshold 80]
"""

import argparse
import datetime
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

STAGES = ["awake", "rem", "core", "deep"]
STAGE_ORDER = {name: i for i, name in enumerate(STAGES)}


def parse_args():
    p = argparse.ArgumentParser(description="Bad Apple → sleep data CSV generator")
    p.add_argument("--fps", type=float, default=15, help="Frames per second (default: 15)")
    p.add_argument("--interval", type=int, default=2, help="Minutes per time column (default: 2)")
    p.add_argument("--start-hour", type=int, default=21, help="Sleep start hour (default: 21)")
    p.add_argument("--end-hour", type=int, default=7, help="Sleep end hour next day (default: 7)")
    p.add_argument("--threshold", type=int, default=80, help="Mean pixel value below which is 'black' (default: 80)")
    p.add_argument("--video", type=str, default="badapple-small.mp4", help="Input video path")
    p.add_argument("--output", type=str, default="badapple-sleep", help="Output directory for CSVs")
    p.add_argument("--reference-date", type=str, default=None, help="Reference date YYYY-MM-DD (default: today)")
    p.add_argument("--same-date", action="store_true", help="All CSVs use the same date, filenames are sleep_00001.csv etc.")
    p.add_argument("--max-frames", type=int, default=None, help="Limit to N frames")
    p.add_argument("--start-frame", type=int, default=None, help="Skip to frame N (generates one CSV)")
    return p.parse_args()


def iter_frames(video_path, fps):
    cmd = [
        "ffmpeg", "-v", "error",
        "-i", video_path,
        "-vf", f"fps={fps}",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Run a quick probe to get dimensions and frame count
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "csv=p=0",
        video_path,
    ]
    info = subprocess.check_output(probe_cmd, text=True).strip().split(",")
    width, height = int(info[0]), int(info[1])
    duration_s = float(info[2]) if len(info) > 2 and info[2] else 219.0
    total_frames = int(duration_s * fps)

    frame_size = width * height * 3
    frame_count = 0

    while True:
        raw = proc.stdout.read(frame_size)
        if len(raw) < frame_size:
            break
        img = Image.frombytes("RGB", (width, height), raw)
        yield frame_count, total_frames, img.copy()
        frame_count += 1

    proc.wait()


def to_grayscale(img, x_start, x_end, y_start, y_end):
    """Return mean grayscale value (0-255) for a rectangular region."""
    region = img.crop((x_start, y_start, x_end, y_end))
    gray = region.convert("L")
    pixels = gray.get_flattened_data()
    return sum(pixels) / len(pixels) if pixels else 255


def frame_to_segments(img, frame_idx, ref_date, args):
    w, h = img.size
    strip_h = h // 4
    sleep_minutes = ((24 + args.end_hour - args.start_hour) % 24) * 60
    num_cols = sleep_minutes // args.interval
    col_w = w / num_cols

    rotation = defaultdict(int)
    segments = []

    base = datetime.datetime(ref_date.year, ref_date.month, ref_date.day,
                             args.start_hour, 0, 0)

    for col in range(num_cols):
        x_start = int(col * col_w)
        x_end = int((col + 1) * col_w)

        active = []
        for si, stage in enumerate(STAGES):
            y_start = si * strip_h
            y_end = (si + 1) * strip_h
            mean = to_grayscale(img, x_start, x_end, y_start, y_end)
            if mean < args.threshold:
                active.append(stage)

        if not active:
            continue

        if len(active) == 1:
            chosen = active[0]
        else:
            key = frozenset(active)
            ordered = sorted(active, key=lambda s: STAGE_ORDER[s])
            idx = rotation[key] % len(ordered)
            chosen = ordered[idx]
            rotation[key] += 1

        start = base + datetime.timedelta(minutes=col * args.interval)
        end = base + datetime.timedelta(minutes=(col + 1) * args.interval)
        segments.append((start.strftime("%Y-%m-%dT%H:%M:%S"),
                         end.strftime("%Y-%m-%dT%H:%M:%S"),
                         chosen.capitalize()))

    return segments


def main():
    args = parse_args()

    if args.reference_date:
        ref_date = datetime.date.fromisoformat(args.reference_date)
    else:
        ref_date = datetime.date.today()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Video: {args.video}")
    print(f"FPS: {args.fps}")
    print(f"Interval: {args.interval} min")
    print(f"Threshold: {args.threshold}")
    print(f"Sleep window: {args.start_hour:02d}:00 – {args.end_hour:02d}:00")
    print(f"Reference date: {ref_date}")
    if args.same_date:
        print(f"Same-date mode: all CSVs dated {ref_date}")
    if args.start_frame is not None:
        print(f"Start frame: {args.start_frame}")
    if args.max_frames:
        print(f"Max frames: {args.max_frames}")
    print(f"Output: {out_dir}")
    print()

    csv_index = 0
    for frame_idx, total, img in iter_frames(args.video, args.fps):
        if args.start_frame is not None and csv_index < args.start_frame:
            night_date = ref_date  # dummy, won't be used
            segments = frame_to_segments(img, frame_idx, night_date, args)
            if segments:
                csv_index += 1
            if frame_idx % 100 == 0:
                print(f"\rSkipping... frame {frame_idx}/{total}", end="", flush=True)
            continue

        if args.max_frames and csv_index >= args.max_frames:
            break

        if args.same_date:
            night_date = ref_date
        else:
            night_date = ref_date - datetime.timedelta(days=frame_idx)

        segments = frame_to_segments(img, frame_idx, night_date, args)

        if not segments:
            continue

        if args.same_date:
            filename = f"sleep_{csv_index:05d}.csv"
        else:
            filename = f"sleep_{night_date.strftime('%Y%m%d')}.csv"
        filepath = out_dir / filename

        with open(filepath, "w") as f:
            f.write("start,end,stage\n")
            for s in segments:
                f.write(f"{s[0]},{s[1]},{s[2]}\n")

        csv_index += 1

        if frame_idx % 100 == 0:
            pct = frame_idx / total * 100 if total else 0
            print(f"\rFrame {frame_idx}/{total} ({pct:.0f}%) — {filename} "
                  f"({len(segments)} segments)", end="", flush=True)

    print(f"\rDone! {csv_index} CSVs written to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
