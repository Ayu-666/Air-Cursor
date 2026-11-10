# Air Cursor v1.1 — High-Performance Virtual Mouse & Smart Hand Tracking

A webcam-based hand tracking mouse and air-drawing application for Windows with low-latency EMA smoothing, resizable floating windows, and smart live diagnostics.

## Features in v1.1

- **Ultra-Responsive Cursor Movement**:
  - Velocity-adaptive Exponential Moving Average (EMA) smoothing eliminates cursor lag during sweeps while staying stable when aiming.
  - Configurable dead zone (`DEAD_ZONE_PIXELS`) eliminates micro-tremors and finger flutter.
  - Full desktop reachability (`CURSOR_SENSITIVITY` and `MOUSE_MARGIN`) reaches all corners of multi-monitor or ultra-wide screens.
- **Reliable Pinch Clicks**:
  - Hysteresis thresholds (`PINCH_THRESHOLD` / `PINCH_RELEASE_THRESHOLD`) prevent click chatter.
  - Debounced click dispatching prevents accidental double-clicks.
- **Resizable Floating Preview**:
  - OpenCV preview is fully resizable (`cv2.WINDOW_NORMAL`), starting as a compact, unobtrusive floating window (`PREVIEW_WIDTH` x `PREVIEW_HEIGHT`).
  - Preview window resizing does not affect hand tracking or screen mapping.
- **Practical Drawing Mode**:
  - Drawing canvas is independent of mouse mode: toggle it on/off at any time with `D`.
  - Closing the canvas window returns control to desktop mouse mode without quitting the application.
  - Resizable canvas (`pygame.RESIZABLE`) with full brush color and size controls.
- **Smart Diagnostics Mode (`H` / `TAB`)**:
  - Live FPS, rolling average FPS (30-frame window), and tracking latency in milliseconds.
  - Multi-hand tracking status and handedness (Left/Right) identification.
  - Orientation-invariant finger extension analysis for Thumb, Index, Middle, Ring, and Pinky.
  - Real-time pinch distance metrics.

## Requirements
- Windows 10/11
- Python 3.10, 3.11, or 3.12
- A working webcam

## Setup & Running (PowerShell)

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Or directly via python.exe:

```powershell
.venv\Scripts\python.exe main.py
```

## Gestures

| Gesture | Action |
|---|---|
| Index finger up, others folded | Move Windows cursor |
| Thumb + index pinch | Left click |
| Thumb + middle pinch (index raised) | Right click |
| Index + middle fingers raised | Draw on canvas (when active) |
| Open hand (4+ fingers raised) | Pause cursor |

## Keyboard Controls

### Webcam Window
- `D`: Toggle Drawing Canvas ON/OFF
- `H` or `TAB`: Toggle Smart Diagnostics HUD overlay
- `C`: Clear drawing canvas
- `Q` or `ESC`: Quit Air Cursor

### Drawing Canvas Window
- `1`: Dark brush
- `2`: Blue brush
- `3`: Red brush
- `4`: Green brush
- `+` / `=`: Increase brush size
- `-`: Decrease brush size
- `C`: Clear canvas
- `D` or `X` button: Close canvas window (returns to mouse mode)

## Configuration (`config.py`)

All key parameters are exposed with sensible defaults:

```python
# Floating preview window size
PREVIEW_WIDTH = 540
PREVIEW_HEIGHT = 304

# Mouse control and precision
MOUSE_MARGIN = 0.10             # Edge margin for comfortable corner access
MOUSE_SMOOTHING = 0.32          # EMA smoothing factor
CURSOR_SENSITIVITY = 1.25       # Sensitivity multiplier
DEAD_ZONE_PIXELS = 3.5          # Suppresses micro-jitter when holding still

# Gesture thresholds
PINCH_THRESHOLD = 0.38          # Enter pinch threshold
PINCH_RELEASE_THRESHOLD = 0.48  # Exit pinch hysteresis threshold
CLICK_COOLDOWN = 0.35           # Minimum seconds between clicks

# Drawing and diagnostics toggles
DRAWING_MODE_ENABLED = False    # Whether canvas opens on startup
SHOW_DIAGNOSTICS = False        # Whether diagnostics HUD starts visible
MAX_HANDS = 2                   # Max hands tracked
```
