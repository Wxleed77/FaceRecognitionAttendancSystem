import cv2
import os
from database import connect_db
from config import CAMERA_INDEX

def register_student(student_name, roll_no, department):
    path = f"dataset/{roll_no}"
    os.makedirs(path, exist_ok=True)

    # Save to DB
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO students (name,roll_no,department,image_path) VALUES (?,?,?,?)",
            (student_name, roll_no, department, path))
        conn.commit()
        print(f"✅ Student {student_name} registered in DB.")
    except Exception as e:
        print(f"⚠️  DB warning: {e}")
    finally:
        conn.close()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    count = 0
    print("📸 Press S to save image | Q to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.putText(frame, f"Saved: {count} | S=save Q=quit",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.imshow("Register Face", frame)
        key = cv2.waitKey(1)
        if key == ord('s'):
            img_path = f"{path}/{count}.jpg"
            cv2.imwrite(img_path, frame)
            print(f"  Saved {img_path}")
            count += 1
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"✅ {count} images saved for {student_name}.")
