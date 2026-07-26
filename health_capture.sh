#!/bin/bash
# Full Health App screenshot capture pipeline
# 1. Build and import data
# 2. Navigate Health app + take screenshots  
# 3. Extract PNGs from xcresult
# 4. Compile movie

set -e
PROJECT="badapple-sleep.xcodeproj"
SCHEME="badapple-sleep"
SIM="iPhone 16 Pro"
FRAMES="frames"
MOVIE="badapple_sleep.mp4"
XCRESULT="/tmp/health_capture.xcresult"

echo "=== Step 1: Build ==="
xcodebuild build-for-testing -project "$PROJECT" -scheme "$SCHEME" \
    -destination "platform=iOS Simulator,name=$SIM" 2>&1 | tail -2

echo ""
echo "=== Step 2: Import + Capture ==="
rm -rf "$XCRESULT"
xcodebuild test-without-building -project "$PROJECT" -scheme "$SCHEME" \
    -destination "platform=iOS Simulator,name=$SIM" \
    -only-testing:badapple-sleepUITests/badapple_sleepUITests/testHealthCapture \
    -resultBundlePath "$XCRESULT" 2>&1 | grep -E "(Test Case|passed|failed|error:)" || true

echo ""
echo "=== Step 3: Extract screenshots ==="
rm -rf "$FRAMES"
mkdir -p "$FRAMES"

python3 << 'PYEOF' "$XCRESULT" "$FRAMES"
import json, subprocess, os, sys

RESULT = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

def xcr(path, id=None):
    cmd = ["xcrun","xcresulttool","get","--path",path,"--legacy","--format","json"]
    if id: cmd.extend(["--id", id])
    out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    return json.loads(out)

root = xcr(RESULT)
tests_ref = root['actions']['_values'][0]['actionResult']['testsRef']['id']['_value']

plan = xcr(RESULT, tests_ref)

def find_refs(obj, path="root"):
    refs = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == '_value' and isinstance(v, str) and v.startswith('0~') and len(v) > 20:
                refs[path] = v
            refs.update(find_refs(v, f"{path}/{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            refs.update(find_refs(v, f"{path}[{i}]"))
    return refs

all_refs = find_refs(plan)
print(f"Found {len(all_refs)} nested refs")

count = 0
for path, ref in all_refs.items():
    obj = xcr(RESULT, ref)
    acts = obj.get('activitySummaries', {}).get('_values', [])
    for act in acts:
        title = act.get('title', {}).get('_value', '')
        ats = act.get('attachments', {}).get('_values', [])
        for a in ats:
            aname = a.get('name', {}).get('_value', '')
            pref = a.get('payloadRef', {}).get('id', {}).get('_value', '')
            if pref and aname:
                outfile = os.path.join(OUT, f"{aname}.png")
                exp = ["xcrun","xcresulttool","export","--path",RESULT,
                       "--output-path",outfile,"--type","file","--id",pref,"--legacy"]
                subprocess.run(exp, capture_output=True)
                if os.path.exists(outfile):
                    print(f"  {os.path.getsize(outfile):>8} bytes  {aname}.png")
                    count += 1

print(f"\nExtracted {count} screenshots to {OUT}/")
PYEOF

echo ""
echo "=== Step 4: Compile movie ==="
if ls "$FRAMES"/*.png 2>/dev/null | head -1 > /dev/null; then
    ffmpeg -y -framerate 15 -pattern_type glob -i "$FRAMES/*.png" \
        -c:v libx264 -pix_fmt yuv420p -preset medium -crf 18 "$MOVIE" 2>&1 | tail -3
    echo ""
    ls -lh "$MOVIE"
else
    echo "No frames found in $FRAMES/"
fi
