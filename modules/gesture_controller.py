import math
from config import PINCH_THRESHOLD


class GestureController:
    """Classifies a few deliberately simple, easy-to-learn hand poses."""

    @staticmethod
    def _distance(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def detect(self, lm):
        if not lm:
            return "NO HAND"

        # Landmark indices: thumb tip 4, index tip 8, middle tip 12,
        # ring tip 16, pinky tip 20; finger PIP joints 6, 10, 14, 18.
        wrist = lm[0]
        palm_width = max(self._distance(lm[5], lm[17]), 0.001)

        index_up = lm[8][1] < lm[6][1]
        middle_up = lm[12][1] < lm[10][1]
        ring_up = lm[16][1] < lm[14][1]
        pinky_up = lm[20][1] < lm[18][1]

        thumb_index = self._distance(lm[4], lm[8]) / palm_width
        thumb_middle = self._distance(lm[4], lm[12]) / palm_width

        # Pinches take priority over finger poses.
        if thumb_index < PINCH_THRESHOLD:
            return "LEFT CLICK"
        if thumb_middle < PINCH_THRESHOLD and index_up:
            return "RIGHT CLICK"

        # Two raised fingers = draw. One raised index = move cursor.
        if index_up and middle_up and not ring_up and not pinky_up:
            return "DRAW"
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "MOVE"

        if index_up and middle_up and ring_up and pinky_up:
            return "PAUSE"

        return "IDLE"
