# badapple-sleep

## Critical rules
- **Screenshots MUST be from Apple Health app** — the whole point of this project is to visualize Bad Apple through actual Health sleep data. Never use Python/Pillow renders, SwiftUI chart views, or any other fake rendering. Always use XCUITest to navigate the real Health app and capture `XCUIScreen.main.screenshot()`.
- Health app bundle ID: `com.apple.Health`
- The XCUITest flow: import data via our app → open Health → navigate to sleep stage chart → screenshot → swipe → repeat

## Plan

### Phase 1: Import one night, take one screenshot
- Generate a single CSV from Bad Apple frame 2000 (to verify we're not just lucky with frame 0)
- CSV uses "last night" timestamps (same-date mode: all data on a single date)
- Import via `Import All Sleep` button
- Open Health → Browse → Sleep → scroll to stage chart → screenshot
- Verify screenshot has colored sleep stage bars (awake = orange/red pixels)

### Phase 2: One night at a time loop
- Never import more than one CSV at once (avoids slow simulator)
- Each CSV uses "last night" timestamps (same-date)
- Loop: import one CSV → Health screenshot → delete all data → next CSV
- All screenshots saved to `frames/` folder
- After all screenshots captured, compile with ffmpeg → `badapple_sleep.mp4`

### Phase 3: Scale to all frames
- 3,197 frames at 15fps, each as a separate CSV
- Run the capture loop for all frames
- Compile full animation

## Files
- `generate_badapple_sleep.py` — converts Bad Apple video frames to sleep CSVs
- `badapple-sleep/` — iOS app (SwiftUI + HealthKit)
- `badapple-sleepUITests/` — XCUITest for Health app screenshot capture
- `frames/` — extracted Health app screenshots (not committed)
- `badapple_sleep.mp4` — compiled animation (not committed)
