import time
import urllib.request

import cv2
import numpy as np


def _mjpeg_frames(url: str, timeout: int = 5):
    """Read MJPEG frames from URL directly — more reliable than cv2.VideoCapture for ESP32-CAM."""
    stream = urllib.request.urlopen(url, timeout=timeout)
    buf = b""
    while True:
        buf += stream.read(4096)
        start = buf.find(b"\xff\xd8")
        end   = buf.find(b"\xff\xd9")
        if start != -1 and end != -1:
            jpg   = buf[start:end + 2]
            buf   = buf[end + 2:]
            frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                yield frame


class StreamReader:
    def __init__(self, url: str, retries: int = 5, retry_delay: float = 2.0):
        self.url         = url
        self.retries     = retries
        self.retry_delay = retry_delay
        self._gen        = None

    def _connect(self):
        for attempt in range(1, self.retries + 1):
            try:
                print(f"[Stream] Connecting to {self.url} (attempt {attempt}/{self.retries})")
                self._gen = _mjpeg_frames(self.url)
                next(self._gen)  # probe first frame
                print("[Stream] Connected.")
                return
            except Exception as e:
                print(f"[Stream] Failed: {e}")
                if attempt < self.retries:
                    time.sleep(self.retry_delay)
        raise ConnectionError(f"Cannot reach ESP32-CAM at {self.url}")

    def frames(self):
        """Yield (frame, ok) tuples. Reconnects on failure."""
        if self._gen is None:
            self._connect()
        while True:
            try:
                yield next(self._gen), True
            except StopIteration:
                break
            except Exception as e:
                print(f"[Stream] Lost connection: {e} — reconnecting...")
                try:
                    self._connect()
                except ConnectionError:
                    break
