import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load local .env file if present (git-ignored for security)
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# Raspberry Pi Camera Stream URL (configured via .env or environment variable)
RPI_HOST = os.environ.get("RPI_HOST", "raspberrypi.local")
STREAM_URL = os.environ.get("RPI_STREAM_URL", f"http://{RPI_HOST}:8080/stream.mjpg")

# Deep Learning Model Path
MODEL_PATH = str(BASE_DIR / "models" / "blaze_face_short_range.tflite")

# Face Detection Settings
CONFIDENCE_THRESHOLD = 0.30  # Minimum confidence score (0.0 ~ 1.0)
SHOW_LANDMARKS = True        # Render facial landmark points (eyes, nose, mouth)

# Greeting Settings
VOICE_ENABLED = True
GREETING_COOLDOWN_SEC = 5.0  # Seconds to wait before greeting again
GREETING_MESSAGES = [
    "안녕하세요! 반갑습니다.",
    "반갑습니다! 어서 오세요.",
    "안녕하세요! 좋은 하루 되세요."
]

# UI & Display Settings
WINDOW_TITLE = "Raspberry Pi 30FPS AI Face Greeter"
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 600
SNAPSHOT_DIR = str(BASE_DIR / "snapshots")
