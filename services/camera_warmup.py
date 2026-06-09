"""
camera_warmup.py — Persistent pre-warmed camera
-------------------------------------------------
Key change from previous version: the camera is NEVER released between streams.
This eliminates the re-warmup lag on second/third stream start.
The camera stays open for the lifetime of the app process.
"""

import cv2
import threading
import time
import platform
from config import CAMERA_INDEX


def _get_backend():
    if platform.system() == "Windows":
        return cv2.CAP_DSHOW
    elif platform.system() == "Linux":
        return cv2.CAP_V4L2
    return cv2.CAP_ANY


class PersistentCamera:
    """
    Opens the camera once at app startup and keeps it open permanently.
    Multiple streams read from it sequentially (one at a time via a lock).

    The key insight: USB webcam negotiation is a one-time cost.
    Releasing and re-opening between sessions was the remaining source of lag.
    """

    def __init__(self, index: int, width: int = 800, height: int = 600):
        self._index  = index
        self._width  = width
        self._height = height
        self._cap    = None
        self._lock   = threading.Lock()
        self._ready  = threading.Event()
        self._in_use = False

        threading.Thread(target=self._init, daemon=True).start()

    def _init(self):
        backend = _get_backend()
        cap = cv2.VideoCapture(self._index, backend)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # minimize buffer latency

        if not cap.isOpened():
            print("⚠️  Camera init failed.")
            self._ready.set()
            return

        # Drain stale startup frames
        for _ in range(6):
            cap.grab()

        self._cap = cap
        self._ready.set()
        print("✅ Camera initialized and held open.")

    def acquire(self, timeout: float = 8.0) -> cv2.VideoCapture | None:
        """
        Waits for camera to be ready and not in use, then returns it.
        The caller must call release() when done.
        """
        deadline = time.time() + timeout
        self._ready.wait(timeout=timeout)

        while time.time() < deadline:
            with self._lock:
                if self._cap and self._cap.isOpened() and not self._in_use:
                    self._in_use = True
                    # Drain stale frames accumulated while idle
                    for _ in range(3):
                        self._cap.grab()
                    return self._cap
            time.sleep(0.05)

        print("⚠️  Camera acquire timed out.")
        return None

    def release(self, _cap=None):
        """
        Marks the camera as available again.
        Does NOT close it — that's the whole point.
        """
        with self._lock:
            self._in_use = False

    def shutdown(self):
        """Call only on full app exit."""
        with self._lock:
            if self._cap:
                self._cap.release()
                self._cap = None


camera_pool = PersistentCamera(index=CAMERA_INDEX)
