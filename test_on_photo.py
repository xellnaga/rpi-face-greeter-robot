import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import os
import time
import cv2
import config
from detector import FaceDetector
from voice import VoiceEngine
from app import draw_korean_text

def test_pipeline():
    img_path = r"C:\Users\woong\.gemini\antigravity\scratch\rpi_face_greeter\sample_face.jpg"
    out_path = r"C:\Users\woong\.gemini\antigravity\scratch\rpi_face_greeter\sample_face_result.jpg"

    print("=" * 60)
    print(" [TEST] Human Face Photo Detection & Greeting Test")
    print("=" * 60)
    
    if not os.path.exists(img_path):
        print(f"[-] Image not found: {img_path}")
        return

    frame = cv2.imread(img_path)
    h, w, _ = frame.shape
    print(f"[+] Loaded test photo: {w}x{h}")

    print("[*] Initializing MediaPipe Face Detector...")
    detector = FaceDetector(config.MODEL_PATH, config.CONFIDENCE_THRESHOLD)

    print("[*] Running Face Detection...")
    t0 = time.time()
    faces = detector.detect(frame)
    dt = time.time() - t0
    print(f"[+] Detection completed in {dt*1000:.2f} ms")
    print(f"[+] Detected faces count: {len(faces)}")

    if not faces:
        print("[-] No face detected in sample photo.")
        return

    for i, f in enumerate(faces):
        bbox = f['bbox']
        conf = f['confidence']
        print(f"    - Face #{i+1}: BBox={bbox}, Confidence={conf*100:.1f}%")

    # Render detection visual elements
    for f in faces:
        x, y, bw, bh = f['bbox']
        conf = f['confidence']
        color = (0, 255, 128)
        cv2.rectangle(frame, (x, y), (x + bw, y + bh), color, 3)

        label = f"Face: {int(conf * 100)}%"
        cv2.rectangle(frame, (x, max(0, y - 28)), (x + 130, y), color, -1)
        cv2.putText(frame, label, (x + 5, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)

        if 'keypoints' in f:
            for kp in f['keypoints']:
                cv2.circle(frame, kp, 4, (0, 255, 255), -1, cv2.LINE_AA)

    # Render Greeting Banner
    greeting_msg = "[GREETING] 안녕하세요! 반갑습니다."
    cv2.rectangle(frame, (20, 20), (w - 20, 70), (0, 160, 50), -1)
    cv2.rectangle(frame, (20, 20), (w - 20, 70), (255, 255, 255), 2)
    frame = draw_korean_text(frame, greeting_msg, (35, 30), font_size=24, color_bgr=(255, 255, 255))

    # Save output image
    cv2.imwrite(out_path, frame)
    print(f"[+] Processed result saved to: {out_path}")

    # Voice TTS Test
    print("[*] Triggering Korean Voice TTS Greeting...")
    voice = VoiceEngine(enabled=True)
    voice.speak("안녕하세요! 사람 얼굴이 정상적으로 감지되었습니다. 반갑습니다.")
    time.sleep(3.5)
    voice.stop()
    print("[+] Test completed successfully!")

if __name__ == "__main__":
    test_pipeline()
