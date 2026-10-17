#!/usr/bin/env python3
"""
Raspberry Pi 30FPS Camera Streaming Server + L298N Motor Control REST API
+ In-Browser AI Face Detection & Korean Voice Greeting (Web Speech API)
Compatible with Python 3.4+
"""

import io
import time
import socketserver
import urllib.parse
from http import server
from threading import Condition
import picamera
from motor_controller import MotorController

PAGE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Raspberry Pi 30FPS Camera, AI Greeting & Robot</title>
<!-- Load TensorFlow.js and BlazeFace for in-browser face detection -->
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@3.20.0/dist/tf.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/blazeface@0.0.7/dist/blazeface.min.js"></script>
<style>
  body {
    background-color: #11141e;
    color: #f0f0f5;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    margin: 0;
    padding: 15px;
    box-sizing: border-box;
  }
  .container {
    background: #1c2130;
    padding: 20px;
    border-radius: 20px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.6);
    text-align: center;
    max-width: 720px;
    width: 100%;
  }
  h1 { margin: 0 0 6px 0; font-size: 22px; color: #4ade80; }
  .badge {
    background: #3b82f6;
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: bold;
    display: inline-block;
    margin-bottom: 10px;
  }

  /* Video & AI Canvas Container */
  .video-container {
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    border: 2px solid #3b82f6;
    background: #000;
    width: 100%;
    max-width: 640px;
    margin: 0 auto;
  }
  img#live-stream {
    width: 100%;
    height: auto;
    display: block;
  }
  canvas#ai-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  /* Greeting Banner */
  #greeting-banner {
    display: none;
    background: rgba(16, 185, 129, 0.9);
    color: white;
    font-size: 17px;
    font-weight: bold;
    padding: 8px 16px;
    border-radius: 10px;
    margin-top: 10px;
    animation: fadeIn 0.3s ease;
  }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }

  /* AI Greeting Toggle Bar */
  .ai-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #161a26;
    padding: 10px 16px;
    border-radius: 12px;
    margin-top: 12px;
    font-size: 14px;
  }
  .ai-btn {
    background: #10b981;
    color: white;
    border: none;
    padding: 6px 14px;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s;
  }
  .ai-btn.disabled {
    background: #4b5563;
  }

  /* Mode Tabs */
  .tabs {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-top: 14px;
  }
  .tab-btn {
    background: #2a324b;
    color: #94a3b8;
    border: 1px solid #3e4a6d;
    padding: 8px 18px;
    border-radius: 10px;
    cursor: pointer;
    font-weight: bold;
    font-size: 14px;
    transition: all 0.2s;
  }
  .tab-btn.active {
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
  }

  .panel-box {
    margin-top: 12px;
    background: #161a26;
    padding: 14px;
    border-radius: 16px;
  }

  /* Dual Vehicle Drive D-Pad */
  .d-pad {
    display: grid;
    grid-template-columns: repeat(3, 72px);
    grid-gap: 10px;
    justify-content: center;
    margin: 10px auto;
  }

  /* Individual Motor Controls Grid */
  .indiv-grid {
    display: flex;
    justify-content: space-around;
    gap: 15px;
    margin: 10px 0;
  }
  .motor-card {
    background: #212738;
    padding: 12px;
    border-radius: 14px;
    flex: 1;
    border: 1px solid #2e374d;
  }
  .motor-card h3 {
    margin: 0 0 10px 0;
    font-size: 15px;
    color: #38bdf8;
  }
  .motor-btn-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .btn {
    background: #2d3748;
    color: white;
    border: none;
    border-radius: 10px;
    height: 48px;
    font-size: 15px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.1s ease;
    user-select: none;
    -webkit-user-select: none;
    touch-action: manipulation;
  }
  .btn:active { background: #3b82f6; transform: scale(0.96); }
  .btn-pad { height: 60px; font-size: 22px; }
  .btn-stop { background: #ef4444; }
  .btn-stop:active { background: #dc2626; }

  .slider-box {
    margin: 10px 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    font-size: 14px;
  }
  input[type=range] { width: 180px; }
  .status-text { font-size: 12px; color: #94a3b8; margin-top: 8px; }
</style>
</head>
<body>
  <div class="container">
    <h1>?çì Raspberry Pi Live Camera & Motor Lab</h1>
    <div class="badge">30 FPS Live Stream + AI Face Greeting + Motor Control</div>
    
    <!-- Video and Face Tracking Overlay -->
    <div class="video-container">
      <img id="live-stream" src="stream.mjpg" alt="Live Stream" crossorigin="anonymous" />
      <canvas id="ai-canvas"></canvas>
    </div>

    <!-- Live Greeting Banner -->
    <div id="greeting-banner">?ëã [?∏ÏÇ¨] ?àÎÖï?òÏÑ∏?? Î∞òÍ∞ë?µÎãà??</div>

    <!-- AI Greeting Controls -->
    <div class="ai-bar">
      <span>?§ñ <strong>Î∏åÎùº?∞Ï? AI ?ºÍµ¥?∏Ïãù ?∏ÏÇ¨:</strong> <span id="ai-status" style="color:#10b981;">Ï§ÄÎπ?Ï§?..</span></span>
      <button class="ai-btn" id="ai-toggle-btn" onclick="toggleAIGreeting()">?åÏÑ± ?∏ÏÇ¨ ÏºúÍ∏∞ ?îä</button>
    </div>

    <!-- Mode Selector Tabs -->
    <div class="tabs">
      <button class="tab-btn active" id="tab-vehicle-btn" onclick="showTab('vehicle')">?öó ?µÌï© Ï£ºÌñâ Î™®Îìú</button>
      <button class="tab-btn" id="tab-indiv-btn" onclick="showTab('indiv')">?ôÔ∏è Í∞úÎ≥Ñ Î™®ÌÑ∞ ?úÏñ¥ Î™®Îìú</button>
    </div>

    <!-- 1. Vehicle Dual Drive Panel -->
    <div class="panel-box" id="panel-vehicle">
      <div class="d-pad">
        <div></div>
        <button class="btn btn-pad" onmousedown="sendCmd('forward')" onmouseup="sendCmd('stop')" ontouchstart="sendCmd('forward')" ontouchend="sendCmd('stop')">&#x25B2;</button>
        <div></div>
        <button class="btn btn-pad" onmousedown="sendCmd('left')" onmouseup="sendCmd('stop')" ontouchstart="sendCmd('left')" ontouchend="sendCmd('stop')">&#x25C0;</button>
        <button class="btn btn-pad btn-stop" onclick="sendCmd('stop')">&#x25A0;</button>
        <button class="btn btn-pad" onmousedown="sendCmd('right')" onmouseup="sendCmd('stop')" ontouchstart="sendCmd('right')" ontouchend="sendCmd('stop')">&#x25B6;</button>
        <div></div>
        <button class="btn btn-pad" onmousedown="sendCmd('backward')" onmouseup="sendCmd('stop')" ontouchstart="sendCmd('backward')" ontouchend="sendCmd('stop')">&#x25BC;</button>
        <div></div>
      </div>
      <div class="status-text">?§Î≥¥?? [W] ?ÑÏßÑ | [A] Ï¢åÌöå???∞Ï∏°Íµ¨Îèô) | [S] ?ÑÏßÑ | [D] ?∞Ìöå??Ï¢åÏ∏°Íµ¨Îèô) | [Space] ?ïÏ?</div>
    </div>

    <!-- 2. Individual Motor Control Panel -->
    <div class="panel-box" id="panel-indiv" style="display:none;">
      <div class="indiv-grid">
        <!-- Motor A (Left) -->
        <div class="motor-card">
          <h3>Î™®ÌÑ∞ A (?ºÏ™Ω)</h3>
          <div class="motor-btn-group">
            <button class="btn" onmousedown="sendCmd('mot_a_fwd')" onmouseup="sendCmd('mot_a_stop')" ontouchstart="sendCmd('mot_a_fwd')" ontouchend="sendCmd('mot_a_stop')">???ÑÏßÑ (FWD)</button>
            <button class="btn btn-stop" onclick="sendCmd('mot_a_stop')">???ïÏ? (STOP)</button>
            <button class="btn" onmousedown="sendCmd('mot_a_bwd')" onmouseup="sendCmd('mot_a_stop')" ontouchstart="sendCmd('mot_a_bwd')" ontouchend="sendCmd('mot_a_stop')">???ÑÏßÑ (BWD)</button>
          </div>
        </div>
        <!-- Motor B (Right) -->
        <div class="motor-card">
          <h3>Î™®ÌÑ∞ B (?§Î•∏Ï™?</h3>
          <div class="motor-btn-group">
            <button class="btn" onmousedown="sendCmd('mot_b_fwd')" onmouseup="sendCmd('mot_b_stop')" ontouchstart="sendCmd('mot_b_fwd')" ontouchend="sendCmd('mot_b_stop')">???ÑÏßÑ (FWD)</button>
            <button class="btn btn-stop" onclick="sendCmd('mot_b_stop')">???ïÏ? (STOP)</button>
            <button class="btn" onmousedown="sendCmd('mot_b_bwd')" onmouseup="sendCmd('mot_b_stop')" ontouchstart="sendCmd('mot_b_bwd')" ontouchend="sendCmd('mot_b_stop')">???ÑÏßÑ (BWD)</button>
          </div>
        </div>
      </div>
      <div class="status-text">?§Î≥¥?? [1/2/3] Î™®ÌÑ∞A ?ÑÏßÑ/?ÑÏßÑ/?ïÏ? | [4/5/6] Î™®ÌÑ∞B ?ÑÏßÑ/?ÑÏßÑ/?ïÏ?</div>
    </div>

    <!-- Speed Slider -->
    <div class="slider-box">
      <span>?çÎèÑ(Speed): <strong id="speed-val">70%</strong></span>
      <input type="range" id="speed-slider" min="30" max="100" value="70" oninput="updateSpeed(this.value)">
      <button class="btn btn-stop" style="height:32px; padding:0 12px; font-size:13px;" onclick="sendCmd('stop')">?ÑÏ≤¥ ?ïÏ?</button>
    </div>
  </div>

<script>
let currentSpeed = 70;
let currentTab = 'vehicle';
let blazefaceModel = null;
let aiEnabled = false;
let lastGreetTime = 0;
const GREET_COOLDOWN_MS = 6000;
const GREETING_MESSAGES = [
  "?àÎÖï?òÏÑ∏?? Î∞òÍ∞ë?µÎãà??",
  "Î∞òÍ∞ë?µÎãà?? ?¥ÏÑú ?§ÏÑ∏??",
  "?àÎÖï?òÏÑ∏?? Ï¢ãÏ? ?òÎ£® ?òÏÑ∏??"
];

// Initialize in-browser Face Detection model
async function initFaceDetector() {
  const statusEl = document.getElementById('ai-status');
  try {
    statusEl.innerText = "AI Î™®Îç∏ Î°úÎî© Ï§?..";
    blazefaceModel = await blazeface.load();
    statusEl.innerText = "?ÄÍ∏?Ï§?(?¥Î¶≠?òÏó¨ ÏºúÍ∏∞)";
    statusEl.style.color = "#38bdf8";
  } catch (err) {
    console.error("AI model load failed:", err);
    statusEl.innerText = "Î™®Îç∏ Î°úÎìú ?§Ìå®";
    statusEl.style.color = "#ef4444";
  }
}
window.addEventListener('load', initFaceDetector);

// Toggle AI Face Greeting & Audio permissions
function toggleAIGreeting() {
  aiEnabled = !aiEnabled;
  const btn = document.getElementById('ai-toggle-btn');
  const statusEl = document.getElementById('ai-status');

  if (aiEnabled) {
    btn.innerText = "?åÏÑ± ?∏ÏÇ¨ ?ÑÍ∏∞ ?îá";
    btn.className = "ai-btn disabled";
    statusEl.innerText = "?§ÏãúÍ∞?Í∞êÏ? Î∞??∏ÏÇ¨ ?úÏÑ± Ï§?";
    statusEl.style.color = "#10b981";
    // Test browser speech unlock
    speakText("?ºÍµ¥?∏Ïãù ?∏ÏÇ¨Í∞Ä ?úÏÑ±?îÎêò?àÏäµ?àÎã§.");
    startDetectionLoop();
  } else {
    btn.innerText = "?åÏÑ± ?∏ÏÇ¨ ÏºúÍ∏∞ ?îä";
    btn.className = "ai-btn";
    statusEl.innerText = "?ºÏãú ?ïÏ???;
    statusEl.style.color = "#94a3b8";
    const canvas = document.getElementById('ai-canvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

// Browser Web Speech API TTS
function speakText(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = 'ko-KR';
  utter.rate = 1.0;
  window.speechSynthesis.speak(utter);
}

// In-browser Detection loop
async function startDetectionLoop() {
  const img = document.getElementById('live-stream');
  const canvas = document.getElementById('ai-canvas');
  const ctx = canvas.getContext('2d');

  async function detect() {
    if (!aiEnabled || !blazefaceModel) return;

    if (img.complete && img.naturalWidth > 0) {
      canvas.width = img.clientWidth;
      canvas.height = img.clientHeight;

      try {
        const predictions = await blazefaceModel.estimateFaces(img, false);
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const scaleX = canvas.width / img.naturalWidth;
        const scaleY = canvas.height / img.naturalHeight;

        if (predictions.length > 0) {
          // Face detected!
          for (let p of predictions) {
            const start = p.topLeft;
            const end = p.bottomRight;
            const size = [end[0] - start[0], end[1] - start[1]];

            // Draw bounding box
            ctx.strokeStyle = '#10b981';
            ctx.lineWidth = 3;
            ctx.strokeRect(start[0] * scaleX, start[1] * scaleY, size[0] * scaleX, size[1] * scaleY);

            // Draw face label
            ctx.fillStyle = '#10b981';
            ctx.fillRect(start[0] * scaleX, (start[1] * scaleY) - 20, 85, 20);
            ctx.fillStyle = '#000000';
            ctx.font = 'bold 12px sans-serif';
            ctx.fillText('Face Detected', (start[0] * scaleX) + 4, (start[1] * scaleY) - 5);
          }

          // Trigger Greeting
          const now = Date.now();
          if (now - lastGreetTime >= GREET_COOLDOWN_MS) {
            lastGreetTime = now;
            const msg = GREETING_MESSAGES[Math.floor(Math.random() * GREETING_MESSAGES.length)];
            
            // Show Banner
            const banner = document.getElementById('greeting-banner');
            banner.innerText = '?ëã [?∏ÏÇ¨] ' + msg;
            banner.style.display = 'block';
            setTimeout(() => { banner.style.display = 'none'; }, 4000);

            // Audio speech via browser
            speakText(msg);
          }
        }
      } catch (e) {
        console.error("Inference err:", e);
      }
    }
    if (aiEnabled) {
      setTimeout(detect, 100); // Check 10 times per second for low CPU
    }
  }
  detect();
}

function showTab(tab) {
  currentTab = tab;
  document.getElementById('panel-vehicle').style.display = (tab === 'vehicle') ? 'block' : 'none';
  document.getElementById('panel-indiv').style.display = (tab === 'indiv') ? 'block' : 'none';
  document.getElementById('tab-vehicle-btn').className = 'tab-btn' + (tab === 'vehicle' ? ' active' : '');
  document.getElementById('tab-indiv-btn').className = 'tab-btn' + (tab === 'indiv' ? ' active' : '');
}

function updateSpeed(val) {
  currentSpeed = val;
  document.getElementById('speed-val').innerText = val + '%';
  fetch('/api/motor?action=speed&speed=' + val);
}

function sendCmd(action) {
  fetch('/api/motor?action=' + action + '&speed=' + currentSpeed);
}

// Global Keyboard controls
window.addEventListener('keydown', function(e) {
  if (e.repeat) return;
  const k = e.key.toLowerCase();
  if (k === 'w') sendCmd('forward');
  else if (k === 's') sendCmd('backward');
  else if (k === 'a') sendCmd('left');
  else if (k === 'd') sendCmd('right');
  else if (k === ' ') sendCmd('stop');
  else if (k === '1') sendCmd('mot_a_fwd');
  else if (k === '2') sendCmd('mot_a_bwd');
  else if (k === '3') sendCmd('mot_a_stop');
  else if (k === '4') sendCmd('mot_b_fwd');
  else if (k === '5') sendCmd('mot_b_bwd');
  else if (k === '6') sendCmd('mot_b_stop');
});

window.addEventListener('keyup', function(e) {
  const k = e.key.toLowerCase();
  if (['w', 's', 'a', 'd'].indexOf(k) !== -1) {
    sendCmd('stop');
  } else if (['1', '2'].indexOf(k) !== -1) {
    sendCmd('mot_a_stop');
  } else if (['4', '5'].indexOf(k) !== -1) {
    sendCmd('mot_b_stop');
  }
});
</script>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception:
                pass
        elif path == '/api/motor':
            query = urllib.parse.parse_qs(parsed.query)
            action = query.get('action', ['stop'])[0].lower()
            speed = int(query.get('speed', [70])[0])

            # Dual vehicle actions
            if action == 'forward':
                motor.forward(speed)
            elif action == 'backward':
                motor.backward(speed)
            elif action == 'left':
                motor.turn_left(speed)
            elif action == 'right':
                motor.turn_right(speed)
            elif action == 'spin_left':
                motor.spin_left(speed)
            elif action == 'spin_right':
                motor.spin_right(speed)
            elif action == 'speed':
                motor.set_speed(speed)
            elif action == 'stop':
                motor.stop()

            # Individual Motor Actions
            elif action in ('mot_a_fwd', 'motor_a_fwd'):
                motor.motor_left('forward', speed)
            elif action in ('mot_a_bwd', 'motor_a_bwd'):
                motor.motor_left('backward', speed)
            elif action in ('mot_a_stop', 'motor_a_stop'):
                motor.motor_left('stop')

            elif action in ('mot_b_fwd', 'motor_b_fwd'):
                motor.motor_right('forward', speed)
            elif action in ('mot_b_bwd', 'motor_b_bwd'):
                motor.motor_right('backward', speed)
            elif action in ('mot_b_stop', 'motor_b_stop'):
                motor.motor_right('stop')

            resp = ('{"status": "ok", "action": "%s", "speed": %d}' % (action, speed)).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', len(resp))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_error(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def main():
    global output, motor
    output = StreamingOutput()
    motor = MotorController()

    print("[Pi Camera] Initializing PiCamera (640x480 @ 30 FPS)...")
    with picamera.PiCamera(resolution='640x480', framerate=30) as camera:
        time.sleep(1)
        camera.start_recording(output, format='mjpeg')
        print("[Pi Camera] Recording started. Starting HTTP server on port 8080...")
        try:
            address = ('0.0.0.0', 8080)
            server_inst = StreamingServer(address, StreamingHandler)
            print("[Pi System] Online at http://0.0.0.0:8080/ (Camera + In-Browser AI Face Greeter + Motor Control)")
            server_inst.serve_forever()
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            camera.stop_recording()
            motor.cleanup()

if __name__ == '__main__':
    main()
