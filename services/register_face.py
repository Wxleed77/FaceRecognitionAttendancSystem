"""
register_face.py — InsightFace-based registration stream
---------------------------------------------------------
Uses the same face_engine as recognition so embeddings are in the same
embedding space — critical for consistency.

Uses the persistent camera pool to avoid conflicts.
Photo count raised to 7 with guidance hints to encourage angle diversity.
"""

import cv2
import numpy as np
import time
from config import CAMERA_INDEX, REGISTER_PHOTO_COUNT
from services.face_engine import detect_and_embed
from services.camera_warmup import camera_pool

# Hint sequence shown at each capture to encourage pose diversity
CAPTURE_HINTS = [
    "Look straight at camera",
    "Turn slightly LEFT",
    "Turn slightly RIGHT",
    "Tilt head slightly UP",
    "Tilt head slightly DOWN",
    "Straight again (different expression)",
    "Straight — final capture",
]


class RegState:
    def __init__(self):
        self.embeddings = []
        self.status     = "ready"
        self.message    = ""
        self.active     = False

reg_state = RegState()


def reset_reg():
    reg_state.embeddings = []
    reg_state.status     = "ready"
    reg_state.message    = ""
    reg_state.active     = True


def get_final_embedding():
    if len(reg_state.embeddings) < REGISTER_PHOTO_COUNT:
        return None
    # Average normalized embeddings, then re-normalize
    avg = np.mean(reg_state.embeddings, axis=0)
    norm = np.linalg.norm(avg)
    return avg / norm if norm > 1e-9 else avg


_latest_frame = {"frame": None}
_cap = None


def generate_registration_stream():
    global _cap
    reset_reg()
    _cap = camera_pool.acquire(timeout=10)
    
    if _cap is None:
        print("❌ Failed to acquire camera for registration")
        return

    # Drain startup frames
    for _ in range(5):
        _cap.grab()

    try:
        while reg_state.active:
            ret, frame = _cap.read()
            if not ret:
                print("⚠️  Failed to read frame from camera")
                break

            _latest_frame["frame"] = frame.copy()

            n      = len(reg_state.embeddings)
            status = reg_state.status
            hint   = CAPTURE_HINTS[min(n, len(CAPTURE_HINTS) - 1)]
            color  = (80, 200, 120) if status == "done" else (200, 160, 40)

            cv2.rectangle(frame, (0, 0), (frame.shape[1], 44), (12, 12, 18), -1)
            cv2.putText(frame, f"  {n}/{REGISTER_PHOTO_COUNT}  |  {hint}",
                        (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2)

            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + buf.tobytes() + b'\r\n')

            if status == "done":
                time.sleep(1.5)
                break
    finally:
        reg_state.active = False
        if _cap:
            camera_pool.release()
            _cap = None


def trigger_capture():
    try:
        frame = _latest_frame.get("frame")
        if frame is None:
            return False, "Camera not ready — waiting for first frame."
        
        # Ensure frame is a proper numpy array
        if not isinstance(frame, np.ndarray) or frame.size == 0:
            print(f"⚠️  Invalid frame: type={type(frame)}, shape={frame.shape if hasattr(frame, 'shape') else 'N/A'}")
            return False, "Camera stream error — retry."
        
        if reg_state.status == "done":
            return True, "Already complete."
        
        print(f"🔍 Attempting capture {len(reg_state.embeddings) + 1}/{REGISTER_PHOTO_COUNT}...")
        print(f"   Frame shape: {frame.shape}, dtype: {frame.dtype}")
        
        detections = detect_and_embed(frame)
        print(f"   Found {len(detections)} face(s)")
        
        if not detections:
            return False, "No face detected — position your face clearly."

        # Use the highest-confidence detection
        best = max(detections, key=lambda d: d["det_score"])
        emb  = best["embedding"]
        
        print(f"   Using face with confidence {best['det_score']:.2%}")

        reg_state.embeddings.append(emb)
        n = len(reg_state.embeddings)
        
        print(f"   ✅ Captured {n}/{REGISTER_PHOTO_COUNT}")

        if n >= REGISTER_PHOTO_COUNT:
            reg_state.status  = "done"
            reg_state.message = f"All {REGISTER_PHOTO_COUNT} captures complete!"
        else:
            hint = CAPTURE_HINTS[min(n, len(CAPTURE_HINTS) - 1)]
            reg_state.status  = "capturing"
            reg_state.message = f"Good! Now: {hint}"

        return True, reg_state.message
    
    except Exception as e:
        print(f"❌ Capture error: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error: {str(e)}"
