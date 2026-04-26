import pickle
import sys
import time
from pathlib import Path

import cv2
import numpy as np

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


class _Lm:
    __slots__ = ("x", "y", "z")
    def __init__(self, lm): self.x, self.y, self.z = lm.x, lm.y, lm.z


class _HandList:
    def __init__(self, lms): self.landmark = [_Lm(l) for l in lms]


class _Result:
    def __init__(self, r):
        self.multi_hand_landmarks = (
            [_HandList(h) for h in r.hand_landmarks] if r and r.hand_landmarks else None
        )


class HandDetector:
    def __init__(self, model_path: Path, num_hands: int = 1):
        import mediapipe as mp
        from mediapipe.tasks import python as mpp
        from mediapipe.tasks.python import vision as mpv

        opts = mpv.HandLandmarkerOptions(
            base_options=mpp.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mpv.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.5,
        )
        self._det   = mpv.HandLandmarker.create_from_options(opts)
        self._t0    = time.perf_counter()
        self._mp    = mp

    def process(self, rgb: np.ndarray) -> _Result:
        img  = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        ts   = int((time.perf_counter() - self._t0) * 1000)
        return _Result(self._det.detect_for_video(img, ts))

    def close(self): self._det.close()


def extract_landmarks(result: _Result) -> np.ndarray | None:
    if not result.multi_hand_landmarks:
        return None
    hand = result.multi_hand_landmarks[0]
    return np.array([[l.x, l.y, l.z] for l in hand.landmark], dtype=np.float32).flatten()


def normalize_landmarks(raw: np.ndarray) -> np.ndarray:
    coords = raw.reshape(21, 3).copy()
    coords -= coords[0]
    scale = float(np.linalg.norm(coords[9]))
    if scale > 1e-6:
        coords /= scale
    return coords.flatten().astype(np.float32)


def draw_landmarks(frame, result: _Result) -> None:
    if not result.multi_hand_landmarks:
        return
    h, w = frame.shape[:2]
    for hand in result.multi_hand_landmarks:
        pts = [(int(l.x * w), int(l.y * h)) for l in hand.landmark]
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (0, 200, 100), 2, cv2.LINE_AA)
        tips = {0, 4, 8, 12, 16, 20}
        for i, pt in enumerate(pts):
            r = 5 if i in tips else 3
            cv2.circle(frame, pt, r, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, pt, r, (0, 160, 80), 1, cv2.LINE_AA)


class GestureClassifier:
    def __init__(self, model_path: Path, classes_path: Path, threshold: float = 0.85):
        try:
            from tensorflow import keras
        except ImportError:
            print("[ERROR] TensorFlow not found. Install: pip install tensorflow")
            sys.exit(1)

        self.model     = keras.models.load_model(model_path)
        self.threshold = threshold
        with open(classes_path, "rb") as f:
            self.classes: list[str] = pickle.load(f)

    def predict(self, raw: np.ndarray) -> tuple[str | None, float]:
        norm  = normalize_landmarks(raw).reshape(1, -1)
        probs = self.model(norm, training=False).numpy()[0]
        idx   = int(np.argmax(probs))
        conf  = float(probs[idx])
        return (self.classes[idx] if conf >= self.threshold else None, conf)


class Debouncer:
    def __init__(self, required: int = 3):
        self.required  = required
        self._pending  = None
        self._count    = 0
        self.stable: str | None = None

    def update(self, label: str | None) -> bool:
        if label != self._pending:
            self._pending, self._count = label, 1
            return False
        self._count += 1
        if self._count == self.required:
            self.stable = label
            return True
        return False
