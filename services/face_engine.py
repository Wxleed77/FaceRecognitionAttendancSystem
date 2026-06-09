"""
face_engine.py — InsightFace ArcFace wrapper
---------------------------------------------
Singleton that loads the ArcFace model once and exposes:
  - detect_and_embed(frame)  → list of (bbox, embedding, det_score)
  - embed_frame(frame)       → same, alias

Why InsightFace / ArcFace over face_recognition (dlib)?
  - ArcFace uses additive angular margin loss — embeddings are more
    discriminative and better separated in embedding space
  - Built-in face detector (RetinaFace) is significantly more accurate
    than dlib's HOG detector, especially for non-frontal angles
  - Actively maintained, ONNX-based (no platform-specific build issues)
  - det_score gives us a face detection confidence we can threshold on,
    preventing low-confidence ghost detections from entering recognition
"""

import cv2
import numpy as np
import threading

_engine_lock    = threading.Lock()
_engine         = None
_engine_ready   = threading.Event()


def _load_engine():
    global _engine
    try:
        import insightface
        from insightface.app import FaceAnalysis
        app = FaceAnalysis(
            name="buffalo_sc",       # lightweight: detector + ArcFace recognizer
            providers=["CPUExecutionProvider"]
        )
        # det_size: larger = more accurate but slower on CPU
        # 320x320 is the sweet spot for real-time on CPU
        app.prepare(ctx_id=0, det_size=(320, 320))
        with _engine_lock:
            _engine = app
        _engine_ready.set()
        print("✅ InsightFace ArcFace engine loaded.")
    except Exception as e:
        print(f"❌ InsightFace load failed: {e}")
        _engine_ready.set()   # unblock waiters even on failure


def get_engine():
    """Returns the engine, loading it if needed. Blocks until ready."""
    _engine_ready.wait(timeout=30)
    return _engine


def detect_and_embed(frame: np.ndarray, min_det_score: float = 0.6):
    """
    Detect all faces in frame and return their embeddings.

    Args:
        frame:         BGR numpy array
        min_det_score: discard detections below this confidence
                       (prevents blurry/partial faces from entering recognition)

    Returns:
        list of dicts:
        {
            "bbox":      (x1, y1, x2, y2),
            "embedding": np.ndarray shape (512,),  normalized ArcFace embedding
            "det_score": float  (detection confidence, 0-1)
        }
    """
    engine = get_engine()
    if engine is None:
        return []

    rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces  = engine.get(rgb)
    result = []

    for face in faces:
        score = float(face.det_score)
        if score < min_det_score:
            continue   # skip blurry / partial detections

        bbox = tuple(int(v) for v in face.bbox)   # (x1, y1, x2, y2)
        emb  = face.normed_embedding               # already L2-normalized

        result.append({
            "bbox":      bbox,
            "embedding": emb,
            "det_score": score,
        })

    return result


# ── Load engine in background immediately on import ────────────────────────────
threading.Thread(target=_load_engine, daemon=True).start()
