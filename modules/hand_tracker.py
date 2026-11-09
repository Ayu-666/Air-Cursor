import cv2
import mediapipe as mp


class HandTracker:
    """MediaPipe Hands wrapper. Landmark coordinates are normalized 0..1."""

    def __init__(self, max_hands=1, detection_confidence=0.65, tracking_confidence=0.6):
        self.mp_hands = mp.solutions.hands
        self.drawer = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            model_complexity=1,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        landmarks = None
        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            self.drawer.draw_landmarks(
                frame, hand, self.mp_hands.HAND_CONNECTIONS
            )
            landmarks = [
                (point.x, point.y, point.z)
                for point in hand.landmark
            ]

        return frame, landmarks

    def close(self):
        self.hands.close()
