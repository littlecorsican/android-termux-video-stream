# this one is for the newer version , as termux-camera-video is deprecated



import os
import socket
import time
import subprocess
from flask import Flask, Response

app = Flask(__name__)

# Track the output frame path securely inside Termux
TMP_DIR = "/data/data/com.termux/files/usr/tmp"
os.makedirs(TMP_DIR, exist_ok=True)
FRAME_PATH = os.path.join(TMP_DIR, "live_frame.jpg")

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip[0] if isinstance(ip, tuple) else ip

def generate_frames():
    # --- CRITICAL OPTIMIZATION ---
    # We remove the '-' pipe and write to a fast local file buffer instead.
    # We forcefully kill the resolution to ensure fast capture speeds.
    # Check your camera sizes via 'termux-camera-info' if you want to tweak this.
    cmd = ["termux-camera-photo", "-c", "0", FRAME_PATH]
    
    while True:
        try:
            # Drop old background API blocks cleanly
            subprocess.run(["pkill", "-f", "com.termux.api"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Execute the capture with a strict timeout so the loop never locks up permanently
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
            
            # Read the fresh raw data directly into the web stream chunk pipelines
            if os.path.exists(FRAME_PATH) and os.path.getsize(FRAME_PATH) > 0:
                with open(FRAME_PATH, "rb") as f:
                    frame = f.read()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            # Allow a short rest window for the hardware sensor loop
            time.sleep(0.1)
            
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            print(f"[!] Streaming Engine Error: {e}")
            break

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    PORT = 5000
    IP_ADDR = get_ip_address()
    
    print("[*] Engaging Termux Wake-Lock...")
    os.system('termux-wake-lock &')
    
    print("=" * 50)
    print(f"[*] Live Streaming URL: http://{IP_ADDR}:{PORT}/video_feed")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
    finally:
        print("[*] Releasing Termux Wake-Lock...")
        os.system('termux-wake-unlock &')
        if os.path.exists(FRAME_PATH):
            os.remove(FRAME_PATH)

