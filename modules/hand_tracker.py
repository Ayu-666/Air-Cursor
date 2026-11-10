import time
from typing import List, Dict, Any, Optional, Tuple
import cv2
import mediapipe as mp

from config import (
    MAX_HANDS,
    DETECTION_CONFIDENCE,
    TRACKING_CONFIDENCE,
    MIRROR_CAMERA,
)


class HandTracker:
    """MediaPipe Hands wrapper supporting multi-hand tracking, handedness extraction,

    and latency diagnostics. Landmark coordinates are normalized 0..1.
    """

    def __init__(
        self,
        max_hands: int = MAX_HANDS,
        detection_confidence: float = DETECTION_CONFIDENCE,
        tracking_confidence: float = TRACKING_CONFIDENCE,
    ):
        self.max_hands = max_hands
        self.mp_hands = mp.solutions.hands
        self.drawer = mp.solutions.drawing_utils
        self.drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            model_complexity=1,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

        self.detected_hands: List[Dict[str, Any]] = []
        self.latency_ms: float = 0.0

    def process(self, frame: cv2.typing.MatLike) -> Tuple[cv2.typing.MatLike, Optional[List[Tuple[float, float, float]]]]:
        """Process a frame, render landmarks, and record tracking metadata.

        Returns:
            (annotated_frame, primary_hand_landmarks)
        """
        start_time = time.perf_counter()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)
        self.latency_ms = (time.perf_counter() - start_time) * 1000.0

        self.detected_hands = []
        primary_landmarks = None

        if result.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
                # Draw landmarks skeleton on frame
                self.drawer.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=self.drawer.DrawingSpec(
                        color=(0, 220, 255), thickness=2, circle_radius=3
                    ),
                    connection_drawing_spec=self.drawer.DrawingSpec(
                        color=(50, 180, 50), thickness=2
                    ),
                )

                # Extract normalized 3D coordinates
                landmarks = [(p.x, p.y, p.z) for p in hand_landmarks.landmark]

                # Determine handedness label
                handedness = "Unknown"
                score = 0.0
                if result.multi_handedness and idx < len(result.multi_handedness):
                    classification = result.multi_handedness[idx].classification[0]
                    label = classification.label  # "Left" or "Right"
                    score = classification.score

                    # When the camera image is horizontally mirrored, MediaPipe's
                    # perception of Left/Right is inverted relative to physical hands.
                    if MIRROR_CAMERA:
                        handedness = "Right" if label == "Left" else "Left"
                    else:
                        handedness = label

                hand_info = {
                    "index": idx,
                    "landmarks": landmarks,
                    "handedness": handedness,
                    "score": score,
                }
                self.detected_hands.append(hand_info)

            # Primary hand is the first detected hand
            primary_landmarks = self.detected_hands[0]["landmarks"]

        return frame, primary_landmarks

    def get_hands_info(self) -> List[Dict[str, Any]]:
        """Return structured information for all currently detected hands."""
        return self.detected_hands

    def close(self):
        self.hands.close()
