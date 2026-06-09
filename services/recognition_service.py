"""
Recognition architecture (non-freezing):
  - Main thread  → camera capture + display (always smooth)
  - Worker thread → face recognition every N frames (heavy work off main thread)
  - Shared state  → thread-safe result passed back to display
"""
import cv2
import numpy as np
import face_recognition
import threading
import time
from config import CAMERA_INDEX, MATCH_TOLERANCE
from database import load_all_embeddings, mark_attendance


# ── Shared state between threads ───────────────────────────────────────────────
class RecognitionState:
    def __init__(self):
        self.lock       = threading.Lock()
        self.label      = "Initializing..."
        self.color      = (200, 200, 200)
        self.face_box   = None          # (top, right, bottom, left) in full-res coords
        self.running    = True
        self.last_marked = {}           # roll_no → timestamp, prevents spam


state = RecognitionState()


def cosine_distance(a, b):
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)


def recognition_worker(frame_queue, known_data):
    """Runs in background thread. Reads frames, does recognition, updates state."""
    while state.running:
        if frame_queue:
            frame = frame_queue[-1]   # always use the latest frame
            frame_queue.clear()
        else:
            time.sleep(0.05)
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Use HOG model (fast CPU); use 'cnn' only with GPU
        face_locs = face_recognition.face_locations(rgb, model="hog")

        if not face_locs:
            with state.lock:
                state.label    = "No face detected"
                state.color    = (100, 100, 100)
                state.face_box = None
            continue

        encodings = face_recognition.face_encodings(rgb, face_locs)

        best_name    = "Unknown"
        best_roll    = None
        best_dist    = 1.0
        best_box     = face_locs[0]

        for enc, loc in zip(encodings, face_locs):
            for (name, roll_no, known_enc) in known_data:
                dist = cosine_distance(enc, known_enc)
                if dist < best_dist:
                    best_dist  = dist
                    best_name  = name
                    best_roll  = roll_no
                    best_box   = loc

        if best_dist <= MATCH_TOLERANCE and best_roll:
            label = f"{best_name}  ({1 - best_dist:.0%})"
            color = (50, 220, 50)

            # Throttle: mark attendance max once per 30 seconds per person
            now = time.time()
            last = state.last_marked.get(best_roll, 0)
            if now - last > 30:
                marked = mark_attendance(best_name, best_roll)
                if marked:
                    print(f"✅ Attendance marked: {best_name}")
                state.last_marked[best_roll] = now
        else:
            label = "Unknown"
            color = (50, 50, 220)

        # Scale box back to full frame (we passed the full frame here)
        top, right, bottom, left = best_box
        with state.lock:
            state.label    = label
            state.color    = color
            state.face_box = (top, right, bottom, left)


def recognize_faces():
    known_data = load_all_embeddings()
    if not known_data:
        print("❌ No students registered. Run register.py first.")
        return

    print(f"✅ Loaded {len(known_data)} student(s) from database.")
    print("🎥 Recognition started. Press Q to quit.\n")

    frame_queue = []
    worker = threading.Thread(
        target=recognition_worker,
        args=(frame_queue, known_data),
        daemon=True
    )
    worker.start()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    frame_num = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (800, 600))
        frame_num += 1

        # Feed worker every 5th frame (recognition cadence)
        if frame_num % 5 == 0:
            frame_queue.append(frame.copy())

        # Draw latest recognition result (never blocks)
        with state.lock:
            label    = state.label
            color    = state.color
            face_box = state.face_box

        if face_box:
            top, right, bottom, left = face_box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            # Label bar below box
            cv2.rectangle(frame, (left, bottom), (right, bottom + 32), color, -1)
            cv2.putText(frame, label, (left + 6, bottom + 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (10, 10, 10), 2)

        # Top status bar
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 44), (15, 15, 15), -1)
        cv2.putText(frame, "AI Attendance  |  Q = quit",
                    (14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (160, 160, 160), 1)

        cv2.imshow("AI Attendance System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    state.running = False
    cap.release()
    cv2.destroyAllWindows()
    print("📴 Recognition stopped.")
