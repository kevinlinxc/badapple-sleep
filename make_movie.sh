#!/bin/bash
# Compile sleep frames into an animated video
# Usage: ./make_movie.sh [fps] [output]
set -e

FPS="${1:-30}"
OUTPUT="${2:-badapple_sleep.mp4}"
FRAMES_DIR="frames"

if [ ! -d "$FRAMES_DIR" ]; then
    echo "Error: $FRAMES_DIR/ not found. Run render_frames.py first."
    exit 1
fi

FRAME_COUNT=$(ls "$FRAMES_DIR"/frame_*.png 2>/dev/null | wc -l | tr -d ' ')
echo "Compiling $FRAME_COUNT frames at ${FPS}fps → $OUTPUT"

ffmpeg -y \
    -framerate "$FPS" \
    -pattern_type glob -i "$FRAMES_DIR/frame_*.png" \
    -c:v libx264 \
    -pix_fmt yuv420p \
    -preset medium \
    -crf 18 \
    "$OUTPUT"

echo "Done: $OUTPUT"
