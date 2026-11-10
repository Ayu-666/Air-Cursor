import time
import math
import pyautogui

from config import (
    MOUSE_MARGIN,
    MOUSE_SMOOTHING,
    CURSOR_SENSITIVITY,
    DEAD_ZONE_PIXELS,
    CLICK_COOLDOWN,
)


class MouseController:
    """Controls the Windows cursor with Exponential Moving Average (EMA) smoothing,

    velocity-adaptive responsiveness, dead-zone filtering, and boundary scaling.
    """

    def __init__(
        self,
        smoothing: float = MOUSE_SMOOTHING,
        sensitivity: float = CURSOR_SENSITIVITY,
        dead_zone: float = DEAD_ZONE_PIXELS,
        margin: float = MOUSE_MARGIN,
        cooldown: float = CLICK_COOLDOWN,
    ):
        self.screen_w, self.screen_h = pyautogui.size()
        self.smoothing = smoothing
        self.sensitivity = sensitivity
        self.dead_zone = dead_zone
        self.margin = margin
        self.cooldown = cooldown

        self.last_x = float(self.screen_w / 2)
        self.last_y = float(self.screen_h / 2)
        self.last_click = 0.0
        self.last_gesture = None

        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = True

    def move_from_normalized(self, x: float, y: float):
        """Map normalized camera coordinates (0..1) to desktop coordinates with

        margin compensation, sensitivity scaling, dead-zone filtering, and EMA smoothing.
        """
        # Map usable camera region to [0, 1]
        usable = max(1.0 - (2.0 * self.margin), 0.01)
        norm_x = (x - self.margin) / usable
        norm_y = (y - self.margin) / usable

        # Apply sensitivity scaling centered around 0.5
        norm_x = (norm_x - 0.5) * self.sensitivity + 0.5
        norm_y = (norm_y - 0.5) * self.sensitivity + 0.5

        # Clamp strictly within screen bounds
        norm_x = min(max(norm_x, 0.0), 1.0)
        norm_y = min(max(norm_y, 0.0), 1.0)

        target_x = norm_x * (self.screen_w - 1)
        target_y = norm_y * (self.screen_h - 1)

        # Distance to target
        dx = target_x - self.last_x
        dy = target_y - self.last_y
        dist = math.hypot(dx, dy)

        # Dead zone: eliminate micro-movements/finger tremors when stationary
        if dist < self.dead_zone:
            return

        # Velocity-adaptive EMA smoothing:
        # Fine movements remain ultra-smooth; rapid sweeps track instantly without lag
        speed_factor = min(1.0, max(0.0, (dist - 12.0) / 100.0))
        effective_alpha = self.smoothing + (0.80 - self.smoothing) * speed_factor

        self.last_x += dx * effective_alpha
        self.last_y += dy * effective_alpha

        # Send movement to Windows OS
        pyautogui.moveTo(int(self.last_x), int(self.last_y), _pause=False)

    def click(self, button: str = "left"):
        """Trigger mouse click with cooldown."""
        now = time.monotonic()
        if now - self.last_click >= self.cooldown:
            pyautogui.click(button=button, _pause=False)
            self.last_click = now

    def handle(self, gesture: str, landmarks):
        """Process incoming gesture and dispatch cursor movement or clicks."""
        if gesture == "MOVE" and landmarks:
            # Index tip is landmark 8
            self.move_from_normalized(landmarks[8][0], landmarks[8][1])

        # Click on rising-edge transition into pinch
        if gesture in ("LEFT CLICK", "RIGHT CLICK") and gesture != self.last_gesture:
            self.click("left" if gesture == "LEFT CLICK" else "right")

        self.last_gesture = gesture
