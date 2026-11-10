from dataclasses import dataclass
from typing import List, Optional, Tuple
import math
import time

from config import (
    PINCH_THRESHOLD,
    PINCH_RELEASE_THRESHOLD,
    GESTURE_COOLDOWN,
)


@dataclass
class FingerState:
    """Detailed state of each finger on a detected hand."""
    thumb: bool
    index: bool
    middle: bool
    ring: bool
    pinky: bool
    pinch_thumb_index: bool
    pinch_thumb_middle: bool
    pinch_distance_index: float
    pinch_distance_middle: float
    raised_count: int
    handedness: str = "Unknown"


class GestureController:
    """Classifies hand poses and finger states with orientation-invariant geometry,

    hysteresis-based pinch detection, and rapid responsive transitions.
    """

    def __init__(
        self,
        pinch_threshold: float = PINCH_THRESHOLD,
        pinch_release_threshold: float = PINCH_RELEASE_THRESHOLD,
        gesture_cooldown: float = GESTURE_COOLDOWN,
    ):
        self.pinch_threshold = pinch_threshold
        self.pinch_release_threshold = pinch_release_threshold
        self.gesture_cooldown = gesture_cooldown

        self.is_pinching_index = False
        self.is_pinching_middle = False

        self.last_gesture = "NO HAND"
        self.last_transition_time = 0.0

        self.last_finger_state: Optional[FingerState] = None

    @staticmethod
    def _distance(a: Tuple[float, float, ...], b: Tuple[float, float, ...]) -> float:
        """Euclidean 2D distance between two landmarks."""
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def analyze_fingers(
        self, lm: Optional[List[Tuple[float, float, float]]], handedness: str = "Unknown"
    ) -> Optional[FingerState]:
        """Compute individual finger extensions and pinches using orientation-invariant geometry."""
        if not lm or len(lm) < 21:
            self.is_pinching_index = False
            self.is_pinching_middle = False
            self.last_finger_state = None
            return None

        # Landmarks:
        # Wrist: 0
        # Thumb:  1=CMC, 2=MCP,  3=IP,   4=TIP
        # Index:  5=MCP, 6=PIP,  7=DIP,  8=TIP
        # Middle: 9=MCP, 10=PIP, 11=DIP, 12=TIP
        # Ring:  13=MCP, 14=PIP, 15=DIP, 16=TIP
        # Pinky: 17=MCP, 18=PIP, 19=DIP, 20=TIP
        wrist = lm[0]
        palm_width = max(self._distance(lm[5], lm[17]), 0.001)

        # 1. Four fingers (Index, Middle, Ring, Pinky)
        # Orientation-independent check:
        # When extended, tip is noticeably farther from the wrist and MCP than the PIP joint.
        index_up = (
            self._distance(lm[8], wrist) > self._distance(lm[6], wrist) * 1.05
            and self._distance(lm[8], lm[5]) > self._distance(lm[6], lm[5]) * 1.10
        )
        middle_up = (
            self._distance(lm[12], wrist) > self._distance(lm[10], wrist) * 1.05
            and self._distance(lm[12], lm[9]) > self._distance(lm[10], lm[9]) * 1.10
        )
        ring_up = (
            self._distance(lm[16], wrist) > self._distance(lm[14], wrist) * 1.05
            and self._distance(lm[16], lm[13]) > self._distance(lm[14], lm[13]) * 1.10
        )
        pinky_up = (
            self._distance(lm[20], wrist) > self._distance(lm[18], wrist) * 1.05
            and self._distance(lm[20], lm[17]) > self._distance(lm[18], lm[17]) * 1.10
        )

        # 2. Thumb check:
        # Thumb curls across the palm towards pinky base (17).
        # When extended outward, thumb tip is far from pinky base and MCP joint.
        thumb_up = (
            self._distance(lm[4], lm[17]) > self._distance(lm[3], lm[17]) * 1.12
            and self._distance(lm[4], lm[2]) > self._distance(lm[3], lm[2]) * 1.05
        )

        # 3. Pinch distances relative to palm width
        dist_thumb_index = self._distance(lm[4], lm[8]) / palm_width
        dist_thumb_middle = self._distance(lm[4], lm[12]) / palm_width

        # Hysteresis for index pinch
        if self.is_pinching_index:
            if dist_thumb_index > self.pinch_release_threshold:
                self.is_pinching_index = False
        else:
            if dist_thumb_index < self.pinch_threshold:
                self.is_pinching_index = True

        # Hysteresis for middle pinch
        if self.is_pinching_middle:
            if dist_thumb_middle > self.pinch_release_threshold:
                self.is_pinching_middle = False
        else:
            if dist_thumb_middle < self.pinch_threshold:
                self.is_pinching_middle = True

        raised_count = sum([thumb_up, index_up, middle_up, ring_up, pinky_up])

        state = FingerState(
            thumb=thumb_up,
            index=index_up,
            middle=middle_up,
            ring=ring_up,
            pinky=pinky_up,
            pinch_thumb_index=self.is_pinching_index,
            pinch_thumb_middle=self.is_pinching_middle,
            pinch_distance_index=dist_thumb_index,
            pinch_distance_middle=dist_thumb_middle,
            raised_count=raised_count,
            handedness=handedness,
        )

        self.last_finger_state = state
        return state

    def detect(
        self, lm: Optional[List[Tuple[float, float, float]]], handedness: str = "Unknown"
    ) -> str:
        """Classify hand pose into a high-level gesture name."""
        if not lm:
            self.last_finger_state = None
            self.is_pinching_index = False
            self.is_pinching_middle = False
            self.last_gesture = "NO HAND"
            return "NO HAND"

        state = self.analyze_fingers(lm, handedness)
        if not state:
            self.last_gesture = "NO HAND"
            return "NO HAND"

        # Raw gesture classification according to priority:
        # 1. Pinches take priority over finger poses.
        if state.pinch_thumb_index:
            gesture = "LEFT CLICK"
        elif state.pinch_thumb_middle and state.index:
            gesture = "RIGHT CLICK"
        # 2. Finger poses
        elif state.index and state.middle and not state.ring and not state.pinky:
            gesture = "DRAW"
        elif state.index and not state.middle and not state.ring and not state.pinky:
            gesture = "MOVE"
        elif state.index and state.middle and state.ring and state.pinky:
            gesture = "PAUSE"
        else:
            gesture = "IDLE"

        now = time.monotonic()
        if gesture != self.last_gesture:
            self.last_transition_time = now

        self.last_gesture = gesture
        return gesture

    def get_finger_state(self) -> Optional[FingerState]:
        """Access the latest computed finger state."""
        return self.last_finger_state
