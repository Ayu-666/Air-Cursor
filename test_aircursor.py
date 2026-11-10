import math
import time
import unittest
import numpy as np
import pyautogui

from config import (
    MOUSE_MARGIN,
    MOUSE_SMOOTHING,
    CURSOR_SENSITIVITY,
    DEAD_ZONE_PIXELS,
    PINCH_THRESHOLD,
    PINCH_RELEASE_THRESHOLD,
    CLICK_COOLDOWN,
    MAX_HANDS,
)
from modules.gesture_controller import GestureController, FingerState
from modules.mouse_controller import MouseController
from modules.drawing_canvas import DrawingCanvas
from modules.hand_tracker import HandTracker
from main import draw_hud


def create_dummy_hand_landmarks(pose="MOVE", angle_deg=0.0):
    """Generate synthetic 21 hand landmarks for testing geometry and gestures."""
    wrist = (0.50, 0.80, 0.0)
    palm_width_mcp_5 = (0.45, 0.55, 0.0)
    palm_width_mcp_17 = (0.58, 0.58, 0.0)

    # Defaults: all folded
    coords = [wrist] + [(0.50, 0.70, 0.0)] * 20
    coords[5] = palm_width_mcp_5
    coords[9] = (0.50, 0.53, 0.0)
    coords[13] = (0.54, 0.55, 0.0)
    coords[17] = palm_width_mcp_17

    # Folded PIPs and TIPs
    for base_idx in [5, 9, 13, 17]:
        coords[base_idx + 1] = (coords[base_idx][0], 0.60, 0.0)  # PIP
        coords[base_idx + 2] = (coords[base_idx][0], 0.65, 0.0)  # DIP
        coords[base_idx + 3] = (coords[base_idx][0], 0.68, 0.0)  # TIP (folded into palm)

    # Natural resting thumb (on the side of the palm)
    coords[1] = (0.46, 0.74, 0.0)
    coords[2] = (0.42, 0.68, 0.0)
    coords[3] = (0.40, 0.62, 0.0)
    coords[4] = (0.38, 0.58, 0.0)

    if pose == "MOVE":
        # Index extended, others folded
        coords[6] = (0.45, 0.40, 0.0)  # PIP
        coords[7] = (0.45, 0.30, 0.0)  # DIP
        coords[8] = (0.45, 0.20, 0.0)  # TIP (far from wrist)

    elif pose == "DRAW":
        # Index and Middle extended
        coords[6] = (0.45, 0.40, 0.0)
        coords[8] = (0.45, 0.20, 0.0)
        coords[10] = (0.50, 0.38, 0.0)
        coords[12] = (0.50, 0.18, 0.0)

    elif pose == "PAUSE":
        # All 5 extended
        coords[4] = (0.28, 0.55, 0.0)  # Thumb tip extended outwards
        coords[6] = (0.45, 0.40, 0.0)
        coords[8] = (0.45, 0.20, 0.0)
        coords[10] = (0.50, 0.38, 0.0)
        coords[12] = (0.50, 0.18, 0.0)
        coords[14] = (0.54, 0.40, 0.0)
        coords[16] = (0.54, 0.22, 0.0)
        coords[18] = (0.58, 0.42, 0.0)
        coords[20] = (0.58, 0.25, 0.0)

    elif pose == "LEFT CLICK":
        # Thumb and Index pinched together
        coords[6] = (0.45, 0.40, 0.0)
        coords[8] = (0.42, 0.50, 0.0)  # Index tip near thumb
        coords[4] = (0.42, 0.50, 0.0)  # Thumb tip at same position

    elif pose == "RIGHT CLICK":
        # Thumb and Middle pinched together, Index extended
        coords[6] = (0.45, 0.40, 0.0)
        coords[8] = (0.45, 0.20, 0.0)  # Index up
        coords[10] = (0.50, 0.40, 0.0)
        coords[12] = (0.42, 0.52, 0.0)  # Middle tip near thumb
        coords[4] = (0.42, 0.52, 0.0)   # Thumb tip

    if angle_deg != 0.0:
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        cx, cy = 0.5, 0.5
        rotated = []
        for x, y, z in coords:
            rx = cx + (x - cx) * cos_a - (y - cy) * sin_a
            ry = cy + (x - cx) * sin_a + (y - cy) * cos_a
            rotated.append((rx, ry, z))
        return rotated

    return coords


class TestGestureController(unittest.TestCase):
    def setUp(self):
        self.gc = GestureController()

    def test_no_hand(self):
        gesture = self.gc.detect(None)
        self.assertEqual(gesture, "NO HAND")
        self.assertIsNone(self.gc.get_finger_state())

    def test_move_gesture(self):
        lm = create_dummy_hand_landmarks("MOVE")
        gesture = self.gc.detect(lm)
        self.assertEqual(gesture, "MOVE")
        fs = self.gc.get_finger_state()
        self.assertIsNotNone(fs)
        self.assertTrue(fs.index)
        self.assertFalse(fs.middle)
        self.assertFalse(fs.ring)
        self.assertFalse(fs.pinky)
        self.assertEqual(fs.raised_count, 1)

    def test_draw_gesture(self):
        lm = create_dummy_hand_landmarks("DRAW")
        gesture = self.gc.detect(lm)
        self.assertEqual(gesture, "DRAW")
        fs = self.gc.get_finger_state()
        self.assertTrue(fs.index)
        self.assertTrue(fs.middle)
        self.assertFalse(fs.ring)
        self.assertFalse(fs.pinky)
        self.assertEqual(fs.raised_count, 2)

    def test_pause_gesture(self):
        lm = create_dummy_hand_landmarks("PAUSE")
        gesture = self.gc.detect(lm)
        self.assertEqual(gesture, "PAUSE")
        fs = self.gc.get_finger_state()
        self.assertTrue(fs.index)
        self.assertTrue(fs.middle)
        self.assertTrue(fs.ring)
        self.assertTrue(fs.pinky)
        self.assertGreaterEqual(fs.raised_count, 4)

    def test_right_click_gesture(self):
        lm = create_dummy_hand_landmarks("RIGHT CLICK")
        gesture = self.gc.detect(lm)
        self.assertEqual(gesture, "RIGHT CLICK")
        fs = self.gc.get_finger_state()
        self.assertTrue(fs.pinch_thumb_middle)
        self.assertTrue(fs.index)

    def test_pinch_hysteresis(self):
        # Initial: open pinch
        lm_move = create_dummy_hand_landmarks("MOVE")
        self.gc.detect(lm_move)
        self.assertFalse(self.gc.is_pinching_index)

        # Enter pinch
        lm_pinch = create_dummy_hand_landmarks("LEFT CLICK")
        gesture = self.gc.detect(lm_pinch)
        self.assertEqual(gesture, "LEFT CLICK")
        self.assertTrue(self.gc.is_pinching_index)

        # Move finger slightly apart: distance between enter (0.38) and release (0.48) threshold
        lm_intermediate = [list(pt) for pt in lm_pinch]
        palm_w = self.gc._distance(lm_intermediate[5], lm_intermediate[17])
        lm_intermediate[8] = (lm_intermediate[4][0] + palm_w * 0.42, lm_intermediate[4][1], 0.0)

        gesture = self.gc.detect(lm_intermediate)
        # Due to hysteresis, should STILL remain in LEFT CLICK
        self.assertTrue(self.gc.is_pinching_index)
        self.assertEqual(gesture, "LEFT CLICK")

        # Now pull finger beyond release threshold (> 0.48 * palm_w)
        lm_released = [list(pt) for pt in lm_pinch]
        lm_released[8] = (lm_released[4][0] + palm_w * 0.55, lm_released[4][1], 0.0)
        self.gc.detect(lm_released)
        self.assertFalse(self.gc.is_pinching_index)

    def test_orientation_invariance(self):
        """Test that gestures are recognized even if hand is rotated 45, 90, 180 degrees."""
        for angle in [0, 45, 90, 135, 180, 270]:
            gc = GestureController()
            lm = create_dummy_hand_landmarks("MOVE", angle_deg=angle)
            fs = gc.analyze_fingers(lm)
            self.assertTrue(fs.index, f"Index failed at angle {angle}")
            self.assertFalse(fs.middle, f"Middle failed at angle {angle}")
            self.assertFalse(fs.ring, f"Ring failed at angle {angle}")
            self.assertFalse(fs.pinky, f"Pinky failed at angle {angle}")


class TestMouseController(unittest.TestCase):
    def setUp(self):
        pyautogui.FAILSAFE = False
        self.mc = MouseController()

    def tearDown(self):
        pyautogui.FAILSAFE = True

    def test_screen_corner_reachability(self):
        """Verify that mapping allows reaching every edge and corner of the screen."""
        pyautogui.FAILSAFE = False
        try:
            # Top-left corner
            for _ in range(15):
                self.mc.move_from_normalized(0.02, 0.02)
            self.assertAlmostEqual(self.mc.last_x, 0.0, delta=5)
            self.assertAlmostEqual(self.mc.last_y, 0.0, delta=5)

            # Bottom-right corner
            for _ in range(15):  # allow EMA to settle
                self.mc.move_from_normalized(0.98, 0.98)
            self.assertAlmostEqual(self.mc.last_x, self.mc.screen_w - 1, delta=5)
            self.assertAlmostEqual(self.mc.last_y, self.mc.screen_h - 1, delta=5)
        finally:
            pyautogui.FAILSAFE = True

    def test_click_cooldown(self):
        """Verify that rapid clicks within CLICK_COOLDOWN are throttled."""
        call_count = 0
        original_click = pyautogui.click

        def mock_click(*args, **kwargs):
            nonlocal call_count
            call_count += 1

        pyautogui.click = mock_click
        try:
            self.mc.click("left")
            self.assertEqual(call_count, 1)

            # Attempt immediate second click (within cooldown)
            self.mc.click("left")
            self.assertEqual(call_count, 1)

            # Wait past cooldown
            time.sleep(self.mc.cooldown + 0.05)
            self.mc.click("left")
            self.assertEqual(call_count, 2)
        finally:
            pyautogui.click = original_click


class TestHandTracker(unittest.TestCase):
    def test_hand_tracker_process(self):
        tracker = HandTracker(max_hands=2)
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_out, landmarks = tracker.process(blank_frame)

        self.assertIsNone(landmarks)
        self.assertEqual(len(tracker.get_hands_info()), 0)
        self.assertGreater(tracker.latency_ms, 0.0)
        tracker.close()


class TestDrawingCanvas(unittest.TestCase):
    def test_lifecycle_and_non_fatal_close(self):
        canvas = DrawingCanvas(enabled_at_start=False)
        self.assertFalse(canvas.is_active)

        # Toggle activate
        canvas.toggle()
        self.assertTrue(canvas.is_active)
        self.assertIsNotNone(canvas.screen)

        # Stroke drawing
        canvas.draw_from_normalized(0.5, 0.5)
        canvas.draw_from_normalized(0.6, 0.6)
        self.assertIsNotNone(canvas.previous_point)
        canvas.stop_stroke()
        self.assertIsNone(canvas.previous_point)

        # Clear
        canvas.clear()

        # Deactivate / close
        canvas.deactivate()
        self.assertFalse(canvas.is_active)

        # Toggle back on
        canvas.toggle()
        self.assertTrue(canvas.is_active)
        canvas.close()


class TestHUDAndDiagnostics(unittest.TestCase):
    def test_render_hud(self):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        fs = FingerState(
            thumb=False,
            index=True,
            middle=False,
            ring=False,
            pinky=False,
            pinch_thumb_index=False,
            pinch_thumb_middle=False,
            pinch_distance_index=0.8,
            pinch_distance_middle=0.9,
            raised_count=1,
            handedness="Right",
        )
        detected_hands = [{"handedness": "Right", "score": 0.99}]

        # Test with diagnostics OFF
        draw_hud(
            frame=frame,
            current_gesture="MOVE",
            detected_hands=detected_hands,
            finger_state=fs,
            fps=30.0,
            avg_fps=29.8,
            latency_ms=12.5,
            show_diagnostics=False,
            drawing_active=False,
        )

        # Test with diagnostics ON
        draw_hud(
            frame=frame,
            current_gesture="MOVE",
            detected_hands=detected_hands,
            finger_state=fs,
            fps=30.0,
            avg_fps=29.8,
            latency_ms=12.5,
            show_diagnostics=True,
            drawing_active=True,
        )
        self.assertEqual(frame.shape, (720, 1280, 3))


if __name__ == "__main__":
    unittest.main()
