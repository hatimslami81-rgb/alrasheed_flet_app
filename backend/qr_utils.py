import os
import qrcode
from PIL import Image
import cv2

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
QR_DIR = os.path.join(ASSETS_DIR, "qr")
os.makedirs(QR_DIR, exist_ok=True)

def generate_qr_png(text: str, file_name: str) -> str:
    path = os.path.join(QR_DIR, file_name)
    img = qrcode.make(text)
    img.save(path)
    return path

def decode_qr_from_image(path: str) -> str | None:
    img = cv2.imread(path)
    if img is None:
        return None
    det = cv2.QRCodeDetector()
    data, points, _ = det.detectAndDecode(img)
    return data if data else None

def decode_qr_from_camera(camera_index: int = 0) -> str | None:
    """يفتح الكاميرا ويقرأ QR. اضغط ESC للإلغاء."""
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None
    det = cv2.QRCodeDetector()
    token = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            data, pts, _ = det.detectAndDecode(frame)
            if pts is not None and len(pts) > 0:
                import numpy as np
                pts = np.array(pts).astype(int).reshape(-1, 2)
                for i in range(len(pts)):
                    p1 = tuple(pts[i]); p2 = tuple(pts[(i+1) % len(pts)])
                    cv2.line(frame, p1, p2, (0, 255, 0), 2)
            if data:
                token = data
                cv2.putText(frame, "QR detected!", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                cv2.imshow("QR Scanner - press any key", frame)
                cv2.waitKey(600)
                break
            cv2.imshow("QR Scanner - press ESC to cancel", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
    return token