import os
import socket
import subprocess
import time
from flask import Flask, Response

app = Flask(__name__)

# --- STORAGE CONFIGURATION ---
# We write to a dedicated live buffer file inside Termux's local storage path
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
    return ip

def generate_frames():
    # Points cleanly to the exact file path instead of the invalid '-' pipe
    cmd = ["termux-camera-photo", "-c", "0", FRAME_PATH]
    
    while True:
        try:
            # 1. Clear out stuck API instances so the camera hardware stays completely loose
            subprocess.run(["pkill", "-f", "com.termux.api"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 2. Capture a fresh snapshot onto the disk buffer
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
            
            # 3. Read the image data out immediately if it exists and has content
            if os.path.exists(FRAME_PATH) and os.path.getsize(FRAME_PATH) > 0:
                with open(FRAME_PATH, "rb") as f:
                    frame = f.read()
                
                # Standard HTTP multipart frame boundaries so the browser catches it instantly
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + 
                       frame + b'\r\n')
            
            # Short delay interval to let your phone's processor catch up
            time.sleep(0.1)
            
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            print(f"[!] Frame Engine Error: {e}")
            break

@app.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

if __name__ == '__main__':
    PORT = 5000
    IP_ADDR = get_ip_address()
    
    print("[*] Engaging Termux Wake-Lock...")
    os.system('termux-wake-lock &')
    
    print("=" * 50)
    print("         PURE TERMUX LOCAL-BUFFER SERVER           ")
    print("=" * 50)
    print(f"[*] Local Host IP Address: {IP_ADDR}")
    print(f"[*] Live Streaming URL   : http://{IP_ADDR}:{PORT}/video_feed")
    print("=" * 50)
    print("[ Press Ctrl+C to stop the stream server safely ]\n")
    
    try:
        # threaded=True gives Flask the ability to serve the layout even while waiting on hardware
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
    finally:
        print("[*] Releasing Termux Wake-Lock...")
        os.system('termux-wake-unlock &')
        if os.path.exists(FRAME_PATH):
            os.remove(FRAME_PATH)
