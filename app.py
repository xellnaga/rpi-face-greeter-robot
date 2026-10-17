import os
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import time
import random
import threading
import urllib.request
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config
from detector import FaceDetector
from voice import VoiceEngine

def draw_korean_text(img_bgr, text, pos, font_size=20, color_bgr=(255, 255, 255)):
    """
    Renders clean Korean text onto an OpenCV BGR image using PIL and Malgun Gothic.
    """
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    
    color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])
    draw.text(pos, text, font=font, fill=color_rgb)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

class MotorClient:
    """
    Asynchronous client to send motor commands to Raspberry Pi REST API without blocking video display.
    """
    def __init__(self, base_url: str):
        self.api_url = base_url.replace("/stream.mjpg", "") + "/api/motor"
        self.current_speed = 70

    def send_cmd(self, action: str, speed: int = None):
        spd = self.current_speed if speed is None else speed
        url = f"{self.api_url}?action={action}&speed={spd}"
        def _request():
            try:
                urllib.request.urlopen(url, timeout=0.8)
            except Exception:
                pass
        threading.Thread(target=_request, daemon=True).start()

class StreamReceiver:
    """
    Background worker thread that continually fetches the latest frame from the network stream.
    Eliminates internal OpenCV buffer latency and guarantees real-time 30 FPS display.
    """
    def __init__(self, stream_url: str):
        self.stream_url = stream_url
        self.cap = None
        self.current_frame = None
        self.running = True
        self.lock = threading.Lock()
        self.connected = False
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _connect(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.stream_url)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.connected = self.cap.isOpened()

    def _update_loop(self):
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                self.connected = False
                self._connect()
                if not self.connected:
                    time.sleep(1.0)
                    continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.connected = False
                time.sleep(0.3)
                self._connect()
                continue

            self.connected = True
            with self.lock:
                self.current_frame = frame
            time.sleep(0.005)

    def get_frame(self):
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def is_connected(self):
        return self.connected

    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()

class FaceGreeterApp:
    def __init__(self):
        print("=" * 60)
        print(" Raspberry Pi 30FPS AI Face Greeter & Robot Controller")
        print("=" * 60)
        print(f"Connecting to Raspberry Pi stream: {config.STREAM_URL}")
        
        os.makedirs(config.SNAPSHOT_DIR, exist_ok=True)

        self.stream = StreamReceiver(config.STREAM_URL)
        print("Initializing MediaPipe BlazeFace DL Model...")
        self.detector = FaceDetector(config.MODEL_PATH, config.CONFIDENCE_THRESHOLD)
        print("Initializing Windows SAPI Korean Voice Engine...")
        self.voice = VoiceEngine(config.VOICE_ENABLED)
        self.motor = MotorClient(config.STREAM_URL)

        self.last_greeting_time = 0.0
        self.banner_text = ""
        self.banner_expire_time = 0.0
        self.show_hud = True
        
        # Motor status display
        self.mot_a_status = "STOP"
        self.mot_b_status = "STOP"

        # FPS calculation
        self.prev_time = time.time()
        self.fps = 0.0
        self.frame_count = 0

    def trigger_greeting(self, custom_msg=None):
        msg = custom_msg or random.choice(config.GREETING_MESSAGES)
        self.last_greeting_time = time.time()
        self.banner_text = msg
        self.banner_expire_time = time.time() + 4.0
        print(f"[*] [인사 발화] \"{msg}\"")
        self.voice.speak(msg)

    def draw_hud(self, frame, faces):
        h, w, _ = frame.shape
        now = time.time()

        if not self.show_hud:
            return frame

        # Semi-transparent top bar & bottom bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 46), (20, 20, 30), -1)
        cv2.rectangle(overlay, (0, h - 34), (w, h), (20, 20, 30), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Top Bar Info
        status_text = "CONNECTED" if self.stream.is_connected() else "CONNECTING..."
        status_color = (0, 255, 120) if self.stream.is_connected() else (0, 140, 255)
        
        cv2.putText(frame, f"STATUS: {status_text}", (15, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, status_color, 2, cv2.LINE_AA)
        
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (210, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)
        
        face_info = f"FACES: {len(faces)}"
        face_color = (0, 255, 255) if faces else (180, 180, 180)
        cv2.putText(frame, face_info, (320, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, face_color, 2, cv2.LINE_AA)

        # Motor Dual Status
        motor_summary = f"MOT_A:{self.mot_a_status} | MOT_B:{self.mot_b_status} ({self.motor.current_speed}%)"
        cv2.putText(frame, motor_summary, (430, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 200), 2, cv2.LINE_AA)

        # Bottom Bar: Shortcuts & Motor driving guide
        shortcuts = "[W/A/S/D] 주행 | [1/2/3] 모터A (전/후/정) | [4/5/6] 모터B (전/후/정) | [Space] 정지"
        frame = draw_korean_text(frame, shortcuts, (15, h - 26), font_size=15, color_bgr=(220, 220, 220))

        # Draw Greeting Banner when active
        if now < self.banner_expire_time:
            bw_h = 46
            bw_y = 56
            b_overlay = frame.copy()
            cv2.rectangle(b_overlay, (20, bw_y), (w - 20, bw_y + bw_h), (0, 160, 50), -1)
            cv2.addWeighted(b_overlay, 0.85, frame, 0.15, 0, frame)
            cv2.rectangle(frame, (20, bw_y), (w - 20, bw_y + bw_h), (255, 255, 255), 2)
            
            banner_msg = f"[GREETING] {self.banner_text}"
            frame = draw_korean_text(frame, banner_msg, (35, bw_y + 10), font_size=20, color_bgr=(255, 255, 255))

        return frame

    def draw_faces(self, frame, faces):
        for f in faces:
            x, y, w, h = f['bbox']
            conf = f['confidence']

            color = (0, 255, 128)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            label = f"Face: {int(conf * 100)}%"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            lbl_w, lbl_h = label_size
            cv2.rectangle(frame, (x, max(0, y - lbl_h - 10)), (x + lbl_w + 10, y), color, -1)
            cv2.putText(frame, label, (x + 5, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

            if config.SHOW_LANDMARKS and 'keypoints' in f:
                for kp in f['keypoints']:
                    cv2.circle(frame, kp, 3, (0, 255, 255), -1, cv2.LINE_AA)

        return frame

    def save_snapshot(self, frame):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(config.SNAPSHOT_DIR, f"snapshot_{ts}.jpg")
        cv2.imwrite(filename, frame)
        print(f"[+] Snapshot saved to: {filename}")

    def run(self):
        cv2.namedWindow(config.WINDOW_TITLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(config.WINDOW_TITLE, config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)

        print("[*] Application started. Use W/A/S/D or 1~6 to drive motors, Q to quit.")

        while True:
            frame = self.stream.get_frame()
            now = time.time()

            # Calculate FPS
            self.frame_count += 1
            if now - self.prev_time >= 1.0:
                self.fps = self.frame_count / (now - self.prev_time)
                self.frame_count = 0
                self.prev_time = now

            if frame is None:
                waiting_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(waiting_frame, "Connecting to Raspberry Pi Camera Stream...",
                            (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 180, 255), 2)
                cv2.imshow(config.WINDOW_TITLE, waiting_frame)
                key = cv2.waitKey(100) & 0xFF
                if key in (27, ord('q'), ord('Q')):
                    break
                continue

            # Run Deep Learning Face Detection
            faces = self.detector.detect(frame)

            # Face Greeting Trigger
            if faces:
                best_conf = max(f['confidence'] for f in faces)
                time_since_greet = now - self.last_greeting_time
                if time_since_greet >= config.GREETING_COOLDOWN_SEC:
                    print(f"[*] Face verified (Score: {best_conf:.2f}). Triggering greeting!")
                    self.trigger_greeting()

            # Render Visual Elements
            frame = self.draw_faces(frame, faces)
            frame = self.draw_hud(frame, faces)

            cv2.imshow(config.WINDOW_TITLE, frame)

            # Key handling (Camera & Motor Controls)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q'), ord('Q')):
                self.motor.send_cmd('stop')
                break

            # 1. Dual Vehicle Drive Mode
            elif key in (ord('w'), ord('W')):
                self.mot_a_status = "FWD"
                self.mot_b_status = "FWD"
                self.motor.send_cmd('forward')
            elif key in (ord('s'), ord('S')):
                self.mot_a_status = "BWD"
                self.mot_b_status = "BWD"
                self.motor.send_cmd('backward')
            elif key in (ord('a'), ord('A')):
                self.mot_a_status = "STOP"
                self.mot_b_status = "FWD"
                self.motor.send_cmd('left')
            elif key in (ord('d'), ord('D')):
                self.mot_a_status = "FWD"
                self.mot_b_status = "STOP"
                self.motor.send_cmd('right')
            elif key == ord(' '):
                self.mot_a_status = "STOP"
                self.mot_b_status = "STOP"
                self.motor.send_cmd('stop')

            # 2. Individual Motor Controls (모터 A / 모터 B 개별 제어)
            elif key == ord('1'):
                self.mot_a_status = "FWD"
                self.motor.send_cmd('mot_a_fwd')
            elif key == ord('2'):
                self.mot_a_status = "BWD"
                self.motor.send_cmd('mot_a_bwd')
            elif key == ord('3'):
                self.mot_a_status = "STOP"
                self.motor.send_cmd('mot_a_stop')
            elif key == ord('4'):
                self.mot_b_status = "FWD"
                self.motor.send_cmd('mot_b_fwd')
            elif key == ord('5'):
                self.mot_b_status = "BWD"
                self.motor.send_cmd('mot_b_bwd')
            elif key == ord('6'):
                self.mot_b_status = "STOP"
                self.motor.send_cmd('mot_b_stop')

            # Speed Adjustments
            elif key in (ord('+'), ord('=')):
                self.motor.current_speed = min(100, self.motor.current_speed + 10)
                self.motor.send_cmd('speed', self.motor.current_speed)
            elif key in (ord('-'), ord('_')):
                self.motor.current_speed = max(30, self.motor.current_speed - 10)
                self.motor.send_cmd('speed', self.motor.current_speed)

            # Snapshots & HUD
            elif key in (ord('p'), ord('P')):
                self.save_snapshot(frame)
            elif key in (ord('g'), ord('G')):
                self.trigger_greeting(custom_msg="안녕하세요! 반갑습니다.")
            elif key in (ord('h'), ord('H')):
                self.show_hud = not self.show_hud

        # Clean shutdown
        print("Shutting down...")
        self.motor.send_cmd('stop')
        self.stream.stop()
        self.voice.stop()
        cv2.destroyAllWindows()
        print("Done.")

if __name__ == "__main__":
    app = FaceGreeterApp()
    app.run()
