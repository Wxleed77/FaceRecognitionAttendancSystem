"""
camera.py — Optimized recognition pipeline (InsightFace + Hungarian + dual threshold)
--------------------------------------------------------------------------------------

Key fixes in this version:
  1. InsightFace ArcFace — better embeddings, better detector, active development
  2. Dual threshold: MATCH_THRESHOLD (absolute) + CONFIDENCE_MARGIN (relative gap)
     This prevents the "only one student registered but stranger walks in" bug
  3. Hungarian assignment — still used, now on similarity scores (not distances)
  4. Persistent camera — no re-warmup between stream sessions
  5. Detection score gating — faces detected below 60% confidence are ignored
"""

import cv2
import numpy as np
import threading
import time

from scipy.optimize import linear_sum_assignment

from config import MATCH_THRESHOLD, CONFIDENCE_MARGIN, RECOGNITION_INTERVAL
from database import mark_attendance
from services.camera_warmup import camera_pool
from services.face_engine import detect_and_embed


# ── Shared state ───────────────────────────────────────────────────────────────
class State:
    def __init__(self):
        self.lock        = threading.Lock()
        self.boxes       = []
        self.active      = False
        self.last_marked = {}

state = State()


# ── Core: dual-threshold assignment ────────────────────────────────────────────
def assign_faces(face_detections: list, known_data: list) -> list[dict]:
    """
    Assigns detected faces to known identities using:
      1. Hungarian algorithm for collision-free one-to-one assignment
      2. Absolute threshold: similarity >= MATCH_THRESHOLD
      3. Margin check: winner must beat second-best by >= CONFIDENCE_MARGIN
         (this is what fixes the "only one student but stranger matches" bug)

    Args:
        face_detections: list of dicts from detect_and_embed()
                         each has "bbox", "embedding", "det_score"
        known_data:      list of (sid, name, roll_no, class_id, embedding)

    Returns:
        list of result dicts, one per face detection
    """
    n_faces = len(face_detections)
    n_known = len(known_data)
    unknown = {"matched": False, "sid": None, "name": "Unknown",
               "roll": None, "class_id": None, "sim": 0.0}

    if n_faces == 0:
        return []
    if n_known == 0:
        return [unknown.copy() for _ in face_detections]

    # ArcFace embeddings are L2-normalized, so cosine similarity = dot product
    # Shape: (n_faces, 512)
    face_embs  = np.stack([f["embedding"] for f in face_detections])
    # Shape: (n_known, 512)
    known_embs = np.stack([k[4] for k in known_data])

    # Similarity matrix: (n_faces, n_known), range ~[-1, 1] but in practice [0, 1]
    sim_matrix = face_embs @ known_embs.T   # dot product = cosine sim (normalized)

    # Hungarian works on cost (minimize), so negate similarity (maximize)
    cost_matrix = -sim_matrix
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    assignment = dict(zip(row_ind, col_ind))   # face_i → known_j

    results = []
    for i, face in enumerate(face_detections):
        if i not in assignment:
            results.append(unknown.copy())
            continue

        j          = assignment[i]
        best_sim   = float(sim_matrix[i, j])
        sid, name, roll_no, class_id, _ = known_data[j]

        # ── Check 1: absolute threshold ────────────────────────────────────
        if best_sim < MATCH_THRESHOLD:
            results.append(unknown.copy())
            continue

        # ── Check 2: confidence margin (the critical fix) ──────────────────
        # If there's more than one known identity, verify the winner is
        # clearly better than the second-best — not just barely better.
        # This prevents a stranger from matching a registered student simply
        # because they are the only option in the cost matrix.
        if n_known > 1:
            all_sims   = sim_matrix[i, :]          # similarities to all known
            sorted_sim = np.sort(all_sims)[::-1]   # descending
            second_sim = sorted_sim[1] if len(sorted_sim) > 1 else 0.0
            margin     = best_sim - second_sim
            if margin < CONFIDENCE_MARGIN:
                results.append(unknown.copy())
                continue
        else:
            # Only one registered student — apply a stricter single-identity
            # threshold to compensate for lack of margin comparison
            if best_sim < (MATCH_THRESHOLD + 0.08):
                results.append(unknown.copy())
                continue

        results.append({
            "matched":  True,
            "sid":      sid,
            "name":     name,
            "roll":     roll_no,
            "class_id": class_id,
            "sim":      best_sim,
        })

    return results


# ── Recognition worker ─────────────────────────────────────────────────────────
def _recognition_worker(frame_ref: dict, known_data: list, teacher_id: int):
    while state.active:
        frame = frame_ref.get("frame")
        if frame is None:
            time.sleep(0.04)
            continue

        detections  = detect_and_embed(frame)
        assignments = assign_faces(detections, known_data)

        boxes = []
        now   = time.time()

        for result, det in zip(assignments, detections):
            x1, y1, x2, y2 = det["bbox"]

            if result["matched"]:
                sid      = result["sid"]
                conf_pct = int(result["sim"] * 100)
                label    = f"{result['name']}  {conf_pct}%"
                color    = (50, 220, 80)

                if now - state.last_marked.get(sid, 0) > 30:
                    if mark_attendance(sid, result["name"],
                                       result["roll"], result["class_id"],
                                       teacher_id):
                        print(f"✅ Marked: {result['name']}")
                    state.last_marked[sid] = now
            else:
                label = "Unknown"
                color = (80, 80, 220)

            boxes.append((y1, x2, y2, x1, label, color, x1, y1, x2, y2))

        with state.lock:
            state.boxes = boxes

        time.sleep(0.04)


# ── Overlay drawing ────────────────────────────────────────────────────────────
def _draw_overlays(frame: np.ndarray) -> np.ndarray:
    with state.lock:
        boxes = list(state.boxes)

    for box in boxes:
        _, _, _, _, label, color, x1, y1, x2, y2 = box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.60, 2)
        cv2.rectangle(frame, (x1, y2), (x1 + tw + 12, y2 + th + 10), color, -1)
        cv2.putText(frame, label, (x1 + 6, y2 + th + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.60, (10, 10, 10), 2)

    cv2.rectangle(frame, (0, 0), (frame.shape[1], 36), (10, 14, 20), -1)
    cv2.putText(frame,
                f"ATTENDAI  |  {len(boxes)} face(s)",
                (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (80, 200, 120), 1)
    return frame


# ── Public: attendance stream ──────────────────────────────────────────────────
def generate_frames(known_data: list, teacher_id: int):
    if not known_data:
        blank = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(blank, "No students registered in this class.",
                    (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (80, 80, 220), 2)
        _, buf = cv2.imencode('.jpg', blank)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
               + buf.tobytes() + b'\r\n')
        return

    cap = camera_pool.acquire(timeout=8.0)
    if not cap:
        print("❌ Camera unavailable.")
        return

    print(f"✅ Attendance stream — {len(known_data)} student(s) loaded.")

    state.active = True
    state.boxes  = []
    frame_ref    = {"frame": None}

    worker = threading.Thread(
        target=_recognition_worker,
        args=(frame_ref, known_data, teacher_id),
        daemon=True
    )
    worker.start()

    frame_count = 0
    try:
        while state.active:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count % RECOGNITION_INTERVAL == 0:
                frame_ref["frame"] = frame.copy()
            frame = _draw_overlays(frame)
            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 78])
            if not ok:
                continue
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + buf.tobytes() + b'\r\n')
    finally:
        state.active      = False
        state.boxes       = []
        frame_ref["frame"] = None
        camera_pool.release()
        print("📴 Attendance stream stopped.")


# ── Public: student self-scan ──────────────────────────────────────────────────
def generate_student_scan(student_embedding: np.ndarray, on_match):
    cap = camera_pool.acquire(timeout=8.0)
    if not cap:
        return

    matched     = False
    scan_active = {"v": True}
    frame_ref   = {"frame": None}
    result_ref  = {"label": "Scanning...", "color": (200, 160, 40),
                   "bbox": None}
    r_lock      = threading.Lock()

    # Wrap single embedding in known_data format for reuse of assign_faces
    known_data = [(-1, "Student", "—", -1, student_embedding)]

    def _worker():
        nonlocal matched
        while scan_active["v"]:
            frame = frame_ref.get("frame")
            if frame is None:
                time.sleep(0.04)
                continue

            detections = detect_and_embed(frame)
            if not detections:
                with r_lock:
                    result_ref.update({"label": "No face detected",
                                       "color": (100, 100, 100), "bbox": None})
                time.sleep(0.04)
                continue

            assignments = assign_faces(detections, known_data)
            # Take first matched result (self-scan = single person)
            best = next((a for a in assignments if a["matched"]), None)
            det  = detections[assignments.index(best)] if best else detections[0]

            x1, y1, x2, y2 = det["bbox"]
            if best:
                conf = int(best["sim"] * 100)
                with r_lock:
                    result_ref.update({"label":  f"Verified ✓  {conf}%",
                                       "color":  (50, 220, 80),
                                       "bbox":   (x1, y1, x2, y2)})
                if not matched:
                    matched = True
                    scan_active["v"] = False
                    on_match()
            else:
                with r_lock:
                    result_ref.update({"label": "Not matched",
                                       "color": (80, 80, 220),
                                       "bbox":  (x1, y1, x2, y2)})
            time.sleep(0.04)

    wt = threading.Thread(target=_worker, daemon=True)
    wt.start()

    frame_count = 0
    try:
        while scan_active["v"] or not matched:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count % 4 == 0:
                frame_ref["frame"] = frame.copy()

            with r_lock:
                label = result_ref["label"]
                color = result_ref["color"]
                bbox  = result_ref["bbox"]

            if bbox:
                x1, y1, x2, y2 = bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
                cv2.rectangle(frame, (x1, y2),
                              (x1 + tw + 12, y2 + th + 10), color, -1)
                cv2.putText(frame, label, (x1 + 6, y2 + th + 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (10, 10, 10), 2)

            cv2.rectangle(frame, (0, 0), (frame.shape[1], 36), (10, 14, 20), -1)
            cv2.putText(frame, "ATTENDAI  |  Face Verification",
                        (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (80, 200, 120), 1)

            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 78])
            if not ok:
                continue
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + buf.tobytes() + b'\r\n')

            if matched:
                time.sleep(2.0)
                break
    finally:
        scan_active["v"] = False
        camera_pool.release()
        print("📴 Student scan stopped.")
