import cv2
import pyautogui

from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, MIRROR_CAMERA
from modules.hand_tracker import HandTracker
from modules.gesture_controller import GestureController
from modules.mouse_controller import MouseController
from modules.drawing_canvas import DrawingCanvas


def main():
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    if not camera.isOpened():
        raise RuntimeError(
            "Could not open webcam. Check CAMERA_INDEX in config.py "
            "and close other apps that may be using the camera."
        )

    tracker = HandTracker()
    gestures = GestureController()
    mouse = MouseController()
    canvas = DrawingCanvas()

    print("\nAIR CURSOR RUNNING")
    print("Index finger only: move cursor")
    print("Thumb + index pinch: left click")
    print("Thumb + middle pinch: right click")
    print("Index + middle fingers up: draw on the Pygame canvas")
    print("Press Q or ESC in the webcam window to quit.")
    print("Press C in the drawing canvas to clear it.\n")

    current_gesture = "NO HAND"

    try:
        while canvas.running:
            ok, frame = camera.read()
            if not ok:
                print("Webcam frame could not be read.")
                break

            if MIRROR_CAMERA:
                frame = cv2.flip(frame, 1)

            frame, landmarks = tracker.process(frame)
            current_gesture = gestures.detect(landmarks)

            if landmarks:
                if current_gesture == "DRAW":
                    canvas.draw_from_normalized(
                        landmarks[8][0], landmarks[8][1]
                    )
                else:
                    canvas.stop_stroke()
                    mouse.handle(current_gesture, landmarks)
            else:
                canvas.stop_stroke()

            # Minimal webcam HUD.
            cv2.putText(
                frame, f"GESTURE: {current_gesture}",
                (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (40, 210, 120), 2, cv2.LINE_AA
            )
            cv2.putText(
                frame, "Q / ESC: quit",
                (20, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (230, 230, 230), 1, cv2.LINE_AA
            )

            cv2.imshow("Air Cursor — Hand Tracking", frame)
            canvas.process_events()
            canvas.render(current_gesture)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break

    except pyautogui.FailSafeException:
        print("PyAutoGUI safety stop triggered.")
    finally:
        camera.release()
        tracker.close()
        canvas.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
