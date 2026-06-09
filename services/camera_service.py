import cv2
from config import CAMERA_INDEX

def test_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    print("📷 Camera test | Q to quit")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Camera not accessible.")
            break
        cv2.imshow("Camera Test", frame)
        if cv2.waitKey(1) == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
