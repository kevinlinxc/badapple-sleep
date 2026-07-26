#!/bin/bash
# Full pipeline: build, capture screenshots on simulator, compile movie
set -e

PROJECT="badapple-sleep.xcodeproj"
SCHEME="badapple-sleep"
BUNDLE="Kevin-Lin.badapple-sleep"
SIM="iPhone 16 Pro"
FRAMES_DIR="frames"
MOVIE="badapple_sleep.mp4"

echo "=== Build ==="
xcodebuild -project "$PROJECT" -scheme "$SCHEME" \
    -destination "platform=iOS Simulator,name=$SIM" build 2>&1 | tail -1

APP=$(find ~/Library/Developer/Xcode/DerivedData -name "badapple-sleep.app" -not -path "*Index*" | head -1)
echo "App: $APP"

echo "=== Boot simulator ==="
xcrun simctl boot "$SIM" 2>/dev/null || true
sleep 2
xcrun simctl install booted "$APP" 2>/dev/null || true

echo "=== Capture ==="
xcrun simctl launch --console-pty booted "$BUNDLE" -- --auto-capture &
PID=$!
echo "PID: $PID"

# Wait for app to finish (max 40 min)
for i in $(seq 1 480); do
    sleep 5
    PID_CHECKED=$(xcrun simctl spawn booted launchctl list 2>/dev/null | grep "$BUNDLE" | grep -v grep | wc -l)
    if [ "$PID_CHECKED" -eq 0 ]; then break; fi
    echo -n "."
done
echo ""

echo "=== Extract frames ==="
SIM_UDID=$(xcrun simctl list devices booted | grep -oE '[A-F0-9-]{36}' | head -1)
APP_DATA=$(xcrun simctl get_app_container "$SIM_UDID" "$BUNDLE" data)
FRAMES_SRC="$APP_DATA/Documents/sleep_frames"

if [ ! -d "$FRAMES_SRC" ]; then
    echo "ERROR: No frames found"
    exit 1
fi

COUNT=$(ls "$FRAMES_SRC"/frame_*.png 2>/dev/null | wc -l | tr -d ' ')
echo "Found $COUNT frames"

rm -rf "$FRAMES_DIR"
mkdir -p "$FRAMES_DIR"
cp "$FRAMES_SRC"/frame_*.png "$FRAMES_DIR/"

echo "=== Compile ==="
ffmpeg -y -framerate 15 -pattern_type glob -i "$FRAMES_DIR/frame_*.png" \
    -c:v libx264 -pix_fmt yuv420p -preset medium -crf 18 "$MOVIE" 2>&1 | tail -3

echo ""
echo "=== Done ==="
ls -lh "$MOVIE"
echo "Frames: $COUNT"
