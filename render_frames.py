#!/usr/bin/env python3
"""Render sleep CSV data as PNG bar chart frames matching Health app style.

Usage:
    source .venv/bin/activate
    python render_frames.py [--width 585] [--height 1266]
"""

import argparse
import glob
import os
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STAGE_COLORS = {
    "awake": (255, 159, 10),
    "rem": (100, 210, 255),
    "core": (58, 130, 246),
    "deep": (94, 92, 230),
}

SLEEP_START_HOUR = 21
SLEEP_END_HOUR = 7
BG = (28, 28, 30)
CARD_BG = (44, 44, 46)
TEXT_PRIMARY = (255, 255, 255)
TEXT_SECONDARY = (174, 174, 178)
GRID_LINE = (58, 58, 60)


def parse_args():
    p = argparse.ArgumentParser(description="Render sleep CSVs as Health-app frames")
    p.add_argument("--csv-dir", default="badapple-sleep", help="Directory with sleep_*.csv files")
    p.add_argument("--output", default="frames", help="Output directory for PNG frames")
    p.add_argument("--width", type=int, default=585, help="Frame width")
    p.add_argument("--height", type=int, default=1266, help="Frame height")
    p.add_argument("--bar-h", type=int, default=22, help="Height of each stage bar")
    p.add_argument("--bar-gap", type=int, default=10, help="Gap between stage bars")
    return p.parse_args()


def load_csv(path):
    segments = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("start"):
                continue
            parts = line.split(",")
            if len(parts) != 3:
                continue
            start_str, end_str, stage = parts
            start_hour = int(start_str[11:13])
            start_min = int(start_str[14:16])
            end_hour = int(end_str[11:13])
            end_min = int(end_str[14:16])
            segments.append((start_hour, start_min, end_hour, end_min, stage.lower()))
    return segments


def time_to_x(hour, minute, x0, chart_w):
    total = ((hour - SLEEP_START_HOUR) % 24) * 60 + minute
    duration = ((SLEEP_END_HOUR - SLEEP_START_HOUR) % 24) * 60
    return x0 + int(total / duration * chart_w)


def rounded_rect(draw, bbox, radius, fill):
    x1, y1, x2, y2 = bbox
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill)


def draw_frame(segments, date_str, w, h, bar_h, bar_gap):
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    try:
        sf_pro_bold = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay-Bold.otf", 30)
        sf_pro_reg = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay-Regular.otf", 22)
        sf_pro_sm = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay-Regular.otf", 13)
        sf_pro_xs = ImageFont.truetype("/System/Library/Fonts/SFNSDisplay-Regular.otf", 11)
    except OSError:
        try:
            sf_pro_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
            sf_pro_reg = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
            sf_pro_sm = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
            sf_pro_xs = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
        except OSError:
            sf_pro_bold = sf_pro_reg = sf_pro_sm = sf_pro_xs = ImageFont.load_default()

    margin = 20
    label_w = 48
    x0 = margin + label_w + 8
    chart_w = w - x0 - margin - 8
    stage_names = ["Awake", "REM", "Core", "Deep"]

    try:
        d = datetime.strptime(date_str, "%Y%m%d")
        date_display = d.strftime("%b %d, %Y")
    except ValueError:
        date_display = date_str

    # Card background
    card_margin = 12
    card_top = 60
    total_bar_h = len(stage_names) * (bar_h + bar_gap)
    chart_top = card_top + 60
    content_bottom = chart_top + total_bar_h + 30 + 20

    draw.rounded_rectangle(
        [card_margin, card_top, w - card_margin, content_bottom],
        radius=14, fill=CARD_BG
    )

    # Title: "Sleep"
    draw.text((x0, card_top + 16), "Sleep", fill=TEXT_PRIMARY, font=sf_pro_bold)

    # Date
    draw.text((x0, card_top + 50), date_display, fill=TEXT_SECONDARY, font=sf_pro_reg)

    # Stage labels (aligned vertically with bar centers)
    for i, name in enumerate(stage_names):
        yc = chart_top + i * (bar_h + bar_gap) + bar_h // 2
        color = STAGE_COLORS.get(name.lower(), TEXT_SECONDARY)
        bbox = draw.textbbox((0, 0), name, font=sf_pro_sm)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((x0 - label_w + 4, yc - th // 2), name, fill=color, font=sf_pro_sm)

    # Draw bars
    for si, stage_name in enumerate(stage_names):
        y = chart_top + si * (bar_h + bar_gap)
        for seg in segments:
            sh, sm, eh, em, stage = seg
            if stage != stage_name.lower():
                continue
            x1 = time_to_x(sh, sm, x0, chart_w)
            x2 = time_to_x(eh, em, x0, chart_w)
            if x2 <= x1:
                continue
            color = STAGE_COLORS.get(stage, (128, 128, 128))
            rounded_rect(draw, (x1, y, x2, y + bar_h), bar_h // 2, color)

    # Hour grid lines + labels
    sleep_hours = ((SLEEP_END_HOUR - SLEEP_START_HOUR) % 24)
    hour_label_y = chart_top + total_bar_h + 8
    line_top = chart_top - 2
    line_bot = chart_top + total_bar_h + 2

    for h_off in range(sleep_hours + 1):
        x = x0 + int(h_off / sleep_hours * chart_w)
        draw.line([(x, line_top), (x, line_bot)], fill=GRID_LINE, width=1)

        hour = (SLEEP_START_HOUR + h_off) % 24
        suffix = "AM" if hour < 12 else "PM"
        disp_h = hour if hour <= 12 else hour - 12
        if disp_h == 0:
            disp_h = 12
        label = f"{disp_h}{suffix}"
        bbox = draw.textbbox((0, 0), label, font=sf_pro_xs)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw // 2, hour_label_y), label, fill=TEXT_SECONDARY, font=sf_pro_xs)

    return img


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)

    csv_pattern = os.path.join(args.csv_dir, "sleep_*.csv")
    csv_files = sorted(glob.glob(csv_pattern))

    if not csv_files:
        print(f"No CSV files found matching {csv_pattern}")
        return

    print(f"Rendering {len(csv_files)} frames to {args.output}/")
    print(f"Size: {args.width}x{args.height}")

    for i, csv_path in enumerate(csv_files):
        filename = os.path.basename(csv_path)
        match = re.match(r"sleep_(\d{8})\.csv", filename)
        date_str = match.group(1) if match else filename

        segments = load_csv(csv_path)
        if not segments:
            continue

        img = draw_frame(segments, date_str, args.width, args.height,
                         args.bar_h, args.bar_gap)

        out_path = os.path.join(args.output, f"frame_{i:05d}.png")
        img.save(out_path)

        if i % 200 == 0:
            print(f"\rFrame {i}/{len(csv_files)}", end="", flush=True)

    print(f"\rDone! {len(csv_files)} frames in {args.output}/")


if __name__ == "__main__":
    main()
