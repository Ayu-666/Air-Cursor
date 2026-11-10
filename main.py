from collections import deque
import time
from typing import List, Dict, Any, Optional
import cv2
import pyautogui

from config import (
    CAMERA_INDEX,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
    MIRROR_CAMERA,
    PREVIEW_WIDTH,
    PREVIEW_HEIGHT,
    MAX_HANDS,
    SHOW_DIAGNOSTICS,
    DRAWING_MODE_ENABLED,
)
from modules.hand_tracker import HandTracker
from modules.gesture_controller import GestureController
from modules.mouse_controller import MouseController
from modules.drawing_canvas import DrawingCanvas


def draw_hud(
    frame: cv2.typing.MatLike,
    current_gesture: str,
    detected_hands: List[Dict[str, Any]],
    finger_state,
    fps: float,
    avg_fps: float,
    latency_ms: float,
    show_diagnostics: bool,
    drawing_active: bool,
):
    """Render a lightweight, non-intrusive status HUD and diagnostics overlay."""
    h, w, _ = frame.shape
    num_hands = len(detected_hands)
    tracking_active = num_hands > 0

    # Color scheme (BGR)
    gesture_colors = {
        "MOVE": (255, 200, 0),       # Cyan-yellow
        "LEFT CLICK": (0, 220, 255),   # Yellow/Orange
        "RIGHT CLICK": (0, 140, 255),  # Orange
        "DRAW": (0, 255, 120),         # Vibrant green
        "PAUSE": (200, 200, 200),      # Silver
        "IDLE": (160, 160, 160),       # Gray
        "NO HAND": (100, 100, 100),    # Dim Gray
    }
    gesture_color = gesture_colors.get(current_gesture, (220, 220, 220))

    # Top Status Bar
    cv2.rectangle(frame, (10, 10), (min(w - 10, 520), 80), (20, 20, 20), cv2.FILLED)
    cv2.rectangle(frame, (10, 10), (min(w - 10, 520), 80), (60, 60, 60), 1)

    cv2.putText(
        frame,
        f"GESTURE: {current_gesture}",
        (20, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        gesture_color,
        2,
        cv2.LINE_AA,
    )

    track_str = f"Tracking: {'ACTIVE' if tracking_active else 'SEARCHING'} ({num_hands}/{MAX_HANDS} hands)"
    track_color = (0, 230, 100) if tracking_active else (120, 120, 220)
    cv2.putText(
        frame,
        track_str,
        (20, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        track_color,
        1,
        cv2.LINE_AA,
    )

    # Bottom shortcut bar
    draw_badge = "[ON]" if drawing_active else "[OFF]"
    diag_badge = "[ON]" if show_diagnostics else "[OFF]"
    shortcut_text = f"D: Draw {draw_badge}  |  H: Diag {diag_badge}  |  Q/ESC: Quit"
    cv2.putText(
        frame,
        shortcut_text,
        (15, h - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (230, 230, 230),
        1,
        cv2.LINE_AA,
    )

    # Optional Diagnostics Panel
    if show_diagnostics:
        panel_x1, panel_y1 = 10, 92
        panel_x2, panel_y2 = min(w - 10, 460), 285

        # Translucent dark panel background
        overlay = frame.copy()
        cv2.rectangle(overlay, (panel_x1, panel_y1), (panel_x2, panel_y2), (15, 15, 18), cv2.FILLED)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        cv2.rectangle(frame, (panel_x1, panel_y1), (panel_x2, panel_y2), (80, 80, 80), 1)

        cv2.putText(
            frame,
            "--- SMART TRACKING DIAGNOSTICS ---",
            (panel_x1 + 12, panel_y1 + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (0, 215, 255),
            1,
            cv2.LINE_AA,
        )

        # Performance row
        perf_line = f"FPS: {fps:4.1f} | Rolling Avg: {avg_fps:4.1f} | Latency: {latency_ms:4.1f} ms"
        cv2.putText(
            frame,
            perf_line,
            (panel_x1 + 12, panel_y1 + 46),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.46,
            (210, 210, 210),
            1,
            cv2.LINE_AA,
        )

        # Hand detection row
        hand_labels = []
        for h_info in detected_hands:
            hand_labels.append(f"{h_info['handedness']} ({int(h_info['score'] * 100)}%)")
        hands_desc = ", ".join(hand_labels) if hand_labels else "None"
        cv2.putText(
            frame,
            f"Hands: {num_hands}/{MAX_HANDS} detected [{hands_desc}]",
            (panel_x1 + 12, panel_y1 + 72),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.46,
            (210, 210, 210),
            1,
            cv2.LINE_AA,
        )

        # Finger states
        if finger_state:
            def f_status(name, val):
                return f"{name}:{'UP' if val else 'DN'}"

            finger_line = (
                f"Fingers ({finger_state.raised_count}/5): "
                f"{f_status('T', finger_state.thumb)} "
                f"{f_status('I', finger_state.index)} "
                f"{f_status('M', finger_state.middle)} "
                f"{f_status('R', finger_state.ring)} "
                f"{f_status('P', finger_state.pinky)}"
            )
            cv2.putText(
                frame,
                finger_line,
                (panel_x1 + 12, panel_y1 + 98),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.46,
                (140, 255, 140),
                1,
                cv2.LINE_AA,
            )

            pinch_line = (
                f"Pinch: Index {finger_state.pinch_distance_index:.2f} "
                f"({'PINCH' if finger_state.pinch_thumb_index else 'OPEN'}) | "
                f"Mid {finger_state.pinch_distance_middle:.2f} "
                f"({'PINCH' if finger_state.pinch_thumb_middle else 'OPEN'})"
            )
            cv2.putText(
                frame,
                pinch_line,
                (panel_x1 + 12, panel_y1 + 124),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.46,
                (255, 210, 120),
                1,
                cv2.LINE_AA,
            )

            mode_str = f"Desktop Mode: {'DRAWING CANVAS' if drawing_active else 'WINDOWS MOUSE'}"
            cv2.putText(
                frame,
                mode_str,
                (panel_x1 + 12, panel_y1 + 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.46,
                (200, 200, 255),
                1,
                cv2.LINE_AA,
            )
        else:
            cv2.putText(
                frame,
                "No hand in view for finger diagnostics.",
                (panel_x1 + 12, panel_y1 + 98),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.46,
                (160, 160, 160),
                1,
                cv2.LINE_AA,
            )


def main():
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    if not camera.isOpened():
        raise RuntimeError(
            "Could not open webcam. Check CAMERA_INDEX in config.py "
            "and close other apps that may be using the camera."
        )

    tracker = HandTracker()
    gestures = GestureController()
    mouse = MouseController()
    canvas = DrawingCanvas()

    # Window setup: Resizable floating preview window
    window_title = "Air Cursor — Hand Tracking"
    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_title, PREVIEW_WIDTH, PREVIEW_HEIGHT)

    print("\n" + "=" * 50)
    print("           AIR CURSOR v1.1 RUNNING")
    print("=" * 50)
    print("GESTURES:")
    print("  - Index finger only      : Move Windows cursor")
    print("  - Thumb + index pinch    : Left click")
    print("  - Thumb + middle pinch   : Right click")
    print("  - Index + middle raised  : Draw on canvas")
    print("  - Open palm              : Pause cursor")
    print("\nCONTROLS:")
    print("  - D                      : Toggle drawing canvas ON/OFF")
    print("  - H / TAB                : Toggle live diagnostics HUD")
    print("  - C                      : Clear drawing canvas")
    print("  - Q / ESC                : Quit Air Cursor")
    print("=" * 50 + "\n")

    current_gesture = "NO HAND"
    show_diagnostics = SHOW_DIAGNOSTICS

    # Performance monitoring
    fps_history = deque(maxlen=30)
    last_frame_time = time.perf_counter()
    current_fps = 0.0

    running = True

    try:
        while running:
            # Calculate FPS
            now = time.perf_counter()
            delta = now - last_frame_time
            last_frame_time = now
            if delta > 0:
                current_fps = 1.0 / delta
                fps_history.append(current_fps)
            avg_fps = sum(fps_history) / len(fps_history) if fps_history else 0.0

            ok, frame = camera.read()
            if not ok:
                print("Webcam frame could not be read.")
                break

            if MIRROR_CAMERA:
                frame = cv2.flip(frame, 1)

            # Process frame through HandTracker
            frame, primary_landmarks = tracker.process(frame)
            detected_hands = tracker.get_hands_info()

            # Primary hand handedness for gesture analysis
            primary_handedness = (
                detected_hands[0]["handedness"] if detected_hands else "Unknown"
            )

            # Detect gesture
            current_gesture = gestures.detect(primary_landmarks, primary_handedness)
            finger_state = gestures.get_finger_state()

            # Handle actions
            if primary_landmarks:
                if canvas.is_active and current_gesture == "DRAW":
                    canvas.draw_from_normalized(
                        primary_landmarks[8][0], primary_landmarks[8][1]
                    )
                else:
                    canvas.stop_stroke()
                    # Normal desktop mouse movement
                    mouse.handle(current_gesture, primary_landmarks)
            else:
                canvas.stop_stroke()

            # Render HUD and diagnostics onto frame
            draw_hud(
                frame=frame,
                current_gesture=current_gesture,
                detected_hands=detected_hands,
                finger_state=finger_state,
                fps=current_fps,
                avg_fps=avg_fps,
                latency_ms=tracker.latency_ms,
                show_diagnostics=show_diagnostics,
                drawing_active=canvas.is_active,
            )

            cv2.imshow(window_title, frame)

            # Pygame canvas event handling and render (non-blocking)
            if canvas.is_active:
                canvas.process_events()
                canvas.render(current_gesture)

            # Check if preview window was closed
            try:
                if cv2.getWindowProperty(window_title, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except Exception:
                pass

            # Keyboard shortcuts
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                running = False
            elif key in (ord("d"), ord("D")):
                canvas.toggle()
            elif key in (ord("h"), ord("H"), 9):  # 9 is TAB
                show_diagnostics = not show_diagnostics
            elif key in (ord("c"), ord("C")):
                if canvas.is_active:
                    canvas.clear()

    except pyautogui.FailSafeException:
        print("PyAutoGUI safety stop triggered.")
    finally:
        camera.release()
        tracker.close()
        canvas.close()
        cv2.destroyAllWindows()
        print("Air Cursor stopped cleanly.")


if __name__ == "__main__":
    main()
