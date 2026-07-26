#!/usr/bin/env python3
"""Extract all PNG attachments from xcresult. Handles binary JSON."""
import subprocess, sys, json, os, struct

RESULT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/htest.xcresult"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/extracted"
os.makedirs(OUT, exist_ok=True)

def xcr(path, id=None):
    cmd = ["xcrun", "xcresulttool", "get", "--path", path, "--legacy", "--format", "json"]
    if id: cmd.extend(["--id", id])
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        # xcresulttool sometimes outputs binary JSON with leading control chars
        # Try to find the JSON start
        start = 0
        for i, b in enumerate(out):
            if b == ord('{'):
                start = i
                break
        return json.loads(out[start:])
    except Exception as e:
        return None

# Collect all IDs with their paths
all_refs = []

def collect(path_str, obj):
    if isinstance(obj, dict):
        tname = obj.get('_type', {}).get('_name', '')
        for k, v in obj.items():
            if k == '_value' and isinstance(v, str) and v.startswith('0~') and len(v) > 20:
                all_refs.append((path_str, tname, k, v))
            collect(f"{path_str}/{k}", v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            collect(f"{path_str}[{i}]", v)

root = xcr(RESULT)
if not root:
    print("Failed to read root")
    sys.exit(1)

collect("root", root)
print(f"Found {len(all_refs)} reference IDs")

# Show all refs
for path, tname, kname, ref in all_refs:
    short = path[-100:]
    print(f"  [{tname}] {short}: {ref[:40]}...")
    
print(f"\nNow looking for attachment patterns...")

# For each ref that might be an attachment tree, drill down
for path, tname, kname, ref in all_refs:
    if 'summary' in path.lower() or 'activity' in path.lower():
        obj = xcr(RESULT, ref)
        if obj:
            tn = obj.get('_type', {}).get('_name', '')
            if tn == 'ActionTestSummary':
                # Check for activitySummaries
                acts = obj.get('activitySummaries', {}).get('_values', [])
                if acts:
                    print(f"\nTest summary at {path[-60:]} has {len(acts)} activities")
                    for a in acts:
                        at = a.get('_type', {}).get('_name', '')
                        title = a.get('title', {}).get('_value', 'N/A')
                        ats = a.get('attachments', {}).get('_values', [])
                        sub = a.get('subactivities', {}).get('_values', [])
                        if ats:
                            print(f"  Activity '{title}': {len(ats)} attachments")
                            for att in ats:
                                name = att.get('name', {}).get('_value', '')
                                fname = att.get('filename', {}).get('_value', '')
                                pref = att.get('payloadRef', {}).get('id', {}).get('_value', '')
                                if pref:
                                    print(f"    Attachment: name={name} file={fname}")
                                    # Export it
                                    outfile = os.path.join(OUT, f"{name or fname}.png")
                                    exp_cmd = ["xcrun", "xcresulttool", "export", "--path", RESULT,
                                               "--output-path", outfile, "--type", "file",
                                               "--id", pref, "--legacy"]
                                    subprocess.run(exp_cmd, capture_output=True)
                                    if os.path.exists(outfile):
                                        print(f"    -> EXPORTED: {os.path.getsize(outfile)} bytes")
                                    else:
                                        print(f"    -> export failed")
                        if sub:
                            print(f"  Activity '{title}': {len(sub)} subactivities (drilling...)")
