# Air Cursor v1.0

A webcam-based hand tracking mouse and air-drawing prototype for Windows.

## Requirements
- Windows 10/11
- Python 3.10 or 3.11 (recommended: Python 3.11)
- A working webcam

## Setup (PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

If PowerShell blocks environment activation, use:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

## Gestures

| Gesture | Action |
|---|---|
| Index finger up, other fingers folded | Move Windows cursor |
| Thumb + index pinch | Left click |
| Thumb + middle pinch (index raised) | Right click |
| Index + middle raised, ring + pinky folded | Draw on canvas |
| Open hand | Pause / idle |

## Canvas controls
- `C`: clear
- `1`: dark brush
- `2`: blue brush
- `3`: red brush
- `4`: green brush
- `+` / `-`: brush size
- Close the canvas window to quit

## Webcam controls
- `Q` or `Esc`: quit (focus the webcam preview window first)

## Safety and troubleshooting
- Start with the cursor away from important buttons and documents.
- Keep your hand visible and use slow movements at first.
- Move the mouse to the top-left corner to trigger PyAutoGUI's failsafe.
- If the webcam does not open, change `CAMERA_INDEX` in `config.py` from `0` to `1`.
- If tracking is jittery, improve lighting and adjust `MOUSE_SMOOTHING` in `config.py`.
- This is a first prototype. Gesture thresholds and cursor calibration may need tuning for your webcam and hand.

## Notes
The app uses MediaPipe's legacy `solutions.hands` API, pinned to MediaPipe 0.10.21 for compatibility.
