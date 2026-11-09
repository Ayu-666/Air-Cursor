import time
import pyautogui
from config import MOUSE_MARGIN, MOUSE_SMOOTHING, CLICK_COOLDOWN


class MouseController:
    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()
        self.last_x = self.screen_w / 2
        self.last_y = self.screen_h / 2
        self.last_click = 0.0
        self.last_gesture = None
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = True

    def move_from_normalized(self, x, y):
        # Ignore the outer camera margin and map the remaining area to the screen.
        usable = 1.0 - (2 * MOUSE_MARGIN)
        x = min(max((x - MOUSE_MARGIN) / usable, 0.0), 1.0)
        y = min(max((y - MOUSE_MARGIN) / usable, 0.0), 1.0)

        target_x = x * self.screen_w
        target_y = y * self.screen_h

        alpha = MOUSE_SMOOTHING
        self.last_x += (target_x - self.last_x) * alpha
        self.last_y += (target_y - self.last_y) * alpha

        pyautogui.moveTo(int(self.last_x), int(self.last_y), _pause=False)

    def click(self, button="left"):
        now = time.monotonic()
        if now - self.last_click >= CLICK_COOLDOWN:
            pyautogui.click(button=button)
            self.last_click = now

    def handle(self, gesture, landmarks):
        if gesture == "MOVE" and landmarks:
            self.move_from_normalized(landmarks[8][0], landmarks[8][1])

        # Click only on the transition into a pinch, not every video frame.
        if gesture in ("LEFT CLICK", "RIGHT CLICK") and gesture != self.last_gesture:
            self.click("left" if gesture == "LEFT CLICK" else "right")

        self.last_gesture = gesture
