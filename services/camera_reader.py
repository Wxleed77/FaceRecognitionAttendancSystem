"""
camera_reader.py — Persistent background camera thread
-------------------------------------------------------
Solves the remaining camera lag completely.

The problem with the old approach:
  Every time the user clicks "Start Attendance", the code calls
  cv2.VideoCapture() inside the Flask response generator. Even with
  CameraPool, the generator itself is started lazily — there's still
  a round-trip from browser click → Flask route → generator start →
  first frame. On Windows with DirectShow this is 600ms–2s.

The correct approach:
  Run ONE dedicated thread that reads frames from the camera continuously
  for the entire lifetime of the app. The camera is opened ONCE when the
  app starts, never closed until shutdown. Streams just subscribe to this
  thread's output — they get the latest frame immediately, zero lag.

Architecture:
  CameraReader (background thread, always running)
      │
      └─ writes latest frame to self._frame  (thread-safe)

  generate_frames() / generate_student_scan()
      │
      └─ reads self._frame, runs recognition, yields MJPEG bytes
         (never touches cv2.VideoCapture directly)
"""

import cv2
import threading
import time
import platform


def _best_backend():
    if platform.system() == "Windows":
        return cv2.CAP_DSHOW
    elif platform.system() == "Linux":
        return cv2.CAP_V4L2
    return cv2.CAP_ANY


class CameraReader:
    """
    Single persistent camera thread. Reads frames in a tight loop and
    exposes the latest one via get_frame(). All stream generators share
    this one reader — the camera is never opened more than once.
    """

    def __init__(self, index: int, width: int = 800, height: int = 600):
        self._index   = index
        self._width   = width
        self._height  = height
        self._cap     = None
        self._frame   = None
        self._lock    = threading.Lock()
        self._started = threading.Event()
        self._stop    = threading.Event()
        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _open(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self._index, _best_backend())
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)   # minimal buffer = low latency
        cap.set(cv2.CAP_PROP_FPS,          30)
        return cap

    def _run(self):
        """Runs forever in background. Reconnects automatically on failure."""
        print("📷 Camera reader starting...")
        self._cap = self._open()

        if not self._cap.isOpened():
            print("❌ Camera reader: device not available.")
            return

        # Drain initial stale buffer
        for _ in range(5):
            self._cap.grab()

        print("✅ Camera reader: live.")
        self._started.set()

        consecutive_failures = 0
        while not self._stop.is_set():
            ret, frame = self._cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures > 10:
                    # Try to reconnect
                    print("⚠️  Camera reader: lost feed, reconnecting...")
                    self._cap.release()
                    time.sleep(1.0)
                    self._cap = self._open()
                    consecutive_failures = 0
                time.sleep(0.05)
                continue

            consecutive_failures = 0
            with self._lock:
                self._frame = frame   # always the freshest frame

        self._cap.release()
        print("📴 Camera reader stopped.")

    def get_frame(self, timeout: float = 5.0):
        """
        Returns the latest frame as a numpy array, or None on timeout.
        Called by stream generators — never blocks more than `timeout` seconds.
        """
        self._started.wait(timeout=timeout)
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def is_ready(self) -> bool:
        return self._started.is_set()

    def shutdown(self):
        self._stop.set()
        self._thread.join(timeout=3.0)
