#!/usr/bin/env python3
"""Extract all screenshot attachments from an xcresult bundle."""
import subprocess, sys, json, os

RESULT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/htest.xcresult"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/attachments"

os.makedirs(OUT, exist_ok=True)

def run(path, id=None, legacy=True):
    cmd = ["xcrun", "xcresulttool", "get", "--path", path, "--format", "json"]
    if legacy: cmd.insert(3, "--legacy")
    if id: cmd.extend(["--id", id])
    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return json.loads(raw)
    except Exception as e:
        print(f"ERR: {e}", file=sys.stderr)
        return None

root = run(RESULT)
if not root:
    print("Failed to read root")
    sys.exit(1)

def find_ids(obj, prefix="", collected=None):
    if collected is None: collected = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "_value" and isinstance(v, str) and v.startswith("0~"):
                collected.append((prefix, v))
            find_ids(v, prefix + "/" + k, collected)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_ids(v, prefix + f"[{i}]", collected)
    return collected

ids = find_ids(root)
print(f"Found {len(ids)} reference IDs")

# Find attachments
attachment_refs = []
for path, ref in ids:
    if "payloadRef" in path or "attachment" in path.lower():
        attachment_refs.append((path, ref))

print(f"\nPotential attachment refs: {len(attachment_refs)}")
for path, ref in attachment_refs:
    print(f"  {path[-80:]}: {ref}")

# Try exporting each one
for i, (path, ref) in enumerate(attachment_refs):
    obj = run(RESULT, ref)
    if obj:
        name = obj.get("name", {}).get("_value", f"attachment_{i}")
        fname = obj.get("filename", {}).get("_value", f"file_{i}.png")
        data_key = obj.get("data", {}) or obj.get("payload", {})
        payload_ref = obj.get("payloadRef", {}).get("id", {}).get("_value", "")
        
        print(f"\n[{i}] name={name} file={fname} type={obj.get('_type',{}).get('_name','')}")
        
        if payload_ref:
            # Try exporting
            exp_cmd = ["xcrun", "xcresulttool", "export", "--path", RESULT,
                       "--output-path", f"{OUT}/{name}.png", "--type", "file",
                       "--id", payload_ref, "--legacy"]
            print(f"  Exporting...")
            subprocess.run(exp_cmd, stderr=subprocess.DEVNULL)

print(f"\nDone. Files in {OUT}:")
for f in os.listdir(OUT):
    print(f"  {f} ({os.path.getsize(os.path.join(OUT, f))} bytes)")
