# Air Cursor configuration

# Camera settings
CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
MIRROR_CAMERA = True  # Mirror preview horizontally (recommended for natural control)

# Floating preview window size (resizable by user at runtime)
PREVIEW_WIDTH = 540
PREVIEW_HEIGHT = 304

# Hand tracking settings
MAX_HANDS = 2
DETECTION_CONFIDENCE = 0.65
TRACKING_CONFIDENCE = 0.60

# Mouse control and precision settings
MOUSE_MARGIN = 0.10             # Edge dead space to allow reaching screen borders comfortably
MOUSE_SMOOTHING = 0.32          # EMA smoothing factor (0.0 = frozen, 1.0 = raw/no smoothing)
CURSOR_SENSITIVITY = 1.25       # Sensitivity multiplier (> 1.0 reaches desktop corners with ease)
DEAD_ZONE_PIXELS = 3.5          # Suppresses micro-jitters when hand is hovering/still

# Gesture and click settings
PINCH_THRESHOLD = 0.38          # Relative to palm width (enter pinch)
PINCH_RELEASE_THRESHOLD = 0.48  # Hysteresis threshold to exit pinch (prevents click chatter)
CLICK_COOLDOWN = 0.35           # Minimum seconds between clicks
GESTURE_COOLDOWN = 0.05         # Minimum seconds before switching between conflicting gestures

# Drawing canvas settings
DRAWING_MODE_ENABLED = False    # Set True to open drawing canvas at startup, or toggle anytime with 'D'
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
CANVAS_RESIZABLE = True
CANVAS_TITLE = "Air Cursor — Drawing Canvas"

# Diagnostics settings
SHOW_DIAGNOSTICS = False        # Toggle diagnostics overlay anytime with 'H' or 'TAB'
