#!/usr/bin/env python3
"""Run XCUITest with progress logging and screenshot extraction."""
import subprocess, sys, os, time, glob

PROJECT = "badapple-sleep.xcodeproj"
SCHEME = "badapple-sleep"
SIM = "iPhone 16 Pro"

def run(cmd, timeout=120):
    print(f"[runner] Running: {' '.join(cmd[:4])}...")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    start = time.time()
    output = []
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            output.append(line)
            # Show progress-relevant lines
            if any(w in line for w in ["Test Case", "passed", "failed", "STEP", "DUMP", "Total", "Screenshot", "TIMEOUT", "error:"]):
                print(f"[runner] {line}")
        elif time.time() - start > timeout and proc.poll() is None:
            proc.kill()
            print("[runner] TIMEOUT - killed")
            break
    proc.wait()
    return proc.returncode, output

# Step 1: Build for testing (only if needed)
print("[runner] Building for testing...")
ret, out = run([
    "xcodebuild", "build-for-testing",
    "-project", PROJECT, "-scheme", SCHEME,
    "-destination", f"platform=iOS Simulator,name={SIM}"
], timeout=120)
if ret != 0:
    print("[runner] Build FAILED")
    sys.exit(1)
print("[runner] Build OK")

# Step 2: Run just the dump test
print("\n[runner] Running testHealthAppDump...")
ret, out = run([
    "xcodebuild", "test-without-building",
    "-project", PROJECT, "-scheme", SCHEME,
    "-destination", f"platform=iOS Simulator,name={SIM}",
    "-only-testing", "badapple-sleepUITests/badapple_sleepUITests/testHealthAppDump"
], timeout=60)

print(f"\n[runner] Test completed with code {ret}")
print(f"[runner] Output lines: {len(out)}")

# Show all test output
print("\n=== TEST OUTPUT ===")
for line in out:
    if not line.startswith(" ") or "STEP" in line or "DUMP" in line:
        print(line)
