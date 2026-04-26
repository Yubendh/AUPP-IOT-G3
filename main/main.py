import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import (
    CLASSES_PATH, CONFIDENCE_THRESHOLD, DEBOUNCE_FRAMES,
    LANDMARKER_PATH, MODEL_PATH, STREAM_URL,
)
from services.gesture_service import (
    Debouncer, GestureClassifier, HandDetector,
    draw_landmarks, extract_landmarks,
)
from services.stream_reader import StreamReader

WHITE = (255, 255, 255)
GREEN = (0, 210, 80)
GREY  = (140, 140, 140)
BLACK = (0, 0, 0)


def _draw_hud(frame, gesture: str | None, confidence: float, fps: float) -> None:
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 100), BLACK, -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    if gesture:
        bar_w = int(confidence * (w - 20))
        cv2.rectangle(frame, (10, 84), (10 + bar_w, 94), GREEN, -1)
        cv2.putText(frame, gesture.replace("_", " ").upper(),
                    (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9, GREEN, 2, cv2.LINE_AA)
        cv2.putText(frame, f"{confidence * 100:.0f}%",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, WHITE, 1, cv2.LINE_AA)
    else:
        cv2.putText(frame, "no hand detected", (10, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, GREY, 1, cv2.LINE_AA)

    cv2.putText(frame, f"{fps:.0f} fps",
                (w - 80, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1, cv2.LINE_AA)
    cv2.putText(frame, "ESC: quit",
                (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, GREY, 1, cv2.LINE_AA)


def send_gesture(gesture: str) -> None:
    """TODO: send confirmed gesture to output ESP32 via HTTP."""
    print(f"[Gesture] {gesture}")


def run():
    missing = [p for p in (MODEL_PATH, CLASSES_PATH, LANDMARKER_PATH) if not p.exists()]
    if missing:
        print("[ERROR] Missing model files — copy from C:/Users/User/Documents/hybrid/model/:")
        for p in missing: print(f"  {p}")
        sys.exit(1)

    detector   = HandDetector(LANDMARKER_PATH)
    classifier = GestureClassifier(MODEL_PATH, CLASSES_PATH, CONFIDENCE_THRESHOLD)
    debouncer  = Debouncer(DEBOUNCE_FRAMES)
    reader     = StreamReader(STREAM_URL)

    prev_time = time.perf_counter()
    fps       = 0.0

    print(f"Reading stream from {STREAM_URL}")
    print("Press ESC to quit.")

    for frame, ok in reader.frames():
        if not ok:
            break

        now      = time.perf_counter()
        fps      = 0.9 * fps + 0.1 * (1.0 / max(now - prev_time, 1e-6))
        prev_time = now

        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result  = detector.process(rgb)
        draw_landmarks(frame, result)

        raw = extract_landmarks(result)
        gesture, confidence = classifier.predict(raw) if raw is not None else (None, 0.0)

        if debouncer.update(gesture) and gesture:
            send_gesture(gesture)

        _draw_hud(frame, gesture, confidence, fps)
        cv2.imshow("ESP32-CAM Gesture Recognition", frame)

        if cv2.waitKey(1) & 0xFF in (27, ord("q")):
            break

    detector.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
