import cv2
import numpy as np
from config import CAMERA_INDEX, REGISTER_PHOTO_COUNT
from database import save_student
from services.face_engine import detect_and_embed


def register_student(name, roll_no, department):
    """
    Register a student using InsightFace ArcFace embeddings (512-dim).
    Same embedding model as recognition to ensure compatibility.
    """
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("❌ Camera failed to open")
        return False
    
    embeddings = []
    needed = REGISTER_PHOTO_COUNT
    print(f"\n📸 Registering: {name}  |  SPACE=capture  Q=cancel\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️  Failed to read frame, retrying...")
            continue

        display = frame.copy()
        cv2.rectangle(display, (0,0), (display.shape[1], 50), (12,12,18), -1)
        cv2.putText(display,
            f"Captured {len(embeddings)}/{needed}  |  SPACE = capture  |  Q = cancel",
            (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 200, 120), 2)

        cv2.imshow("Register Student", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("❌ Registration cancelled")
            cap.release()
            cv2.destroyAllWindows()
            return False

        if key == ord(' '):
            print(f"🔍 Processing face {len(embeddings)+1}/{needed}...")
            try:
                detections = detect_and_embed(frame, min_det_score=0.5)
                print(f"   Found {len(detections)} face(s)")
                
                if not detections:
                    print("   ⚠️  No face detected, try again.")
                    continue
                
                # Use the highest confidence detection
                best = max(detections, key=lambda d: d["det_score"])
                embeddings.append(best["embedding"])
                conf_pct = int(best['det_score']*100)
                print(f"   ✅ Captured {len(embeddings)}/{needed} (confidence: {conf_pct}%)")
                
                if len(embeddings) >= needed:
                    print("✅ All photos captured!")
                    break
            except Exception as e:
                print(f"   ❌ Error during capture: {e}")
                continue

    cap.release()
    cv2.destroyAllWindows()
    
    if not embeddings:
        print("❌ No embeddings captured")
        return False

    print(f"📊 Creating average embedding from {len(embeddings)} photos...")
    avg = np.mean(embeddings, axis=0)
    ok = save_student(name, roll_no, department, avg)
    print(f"{'✅ Registered: ' + name if ok else '⚠️  Roll no already exists.'}")
    return ok
