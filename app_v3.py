import os
import socket
import subprocess
from flask import Flask, Response

app = Flask(__name__)

# Dedicated buffer path inside Termux local memory space
TMP_DIR = "/data/data/com.termux/files/usr/tmp"
os.makedirs(TMP_DIR, exist_ok=True)
FRAME_PATH = os.path.join(TMP_DIR, "live_frame.jpg")

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@app.route('/video_feed')
def video_feed():
    """
    Triggers the camera hardware ONLY when the browser requests the page.
    This guarantees the endpoint registers and never crashes the loop.
    """
    try:
        # 1. Clean out any stuck background links cleanly
        subprocess.run(["pkill", "-f", "com.termux.api"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. Take a fresh snapshot onto the disk buffer
        # -c 0 is the back camera. If it hangs, change to -c 1 for front camera.
        subprocess.run(["termux-camera-photo", "-c", "0", FRAME_PATH], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        
        # 3. If the frame exists, read and serve it immediately as a standard JPEG image
        if os.path.exists(FRAME_PATH) and os.path.getsize(FRAME_PATH) > 0:
            with open(FRAME_PATH, "rb") as f:
                frame_data = f.read()
            return Response(frame_data, mimetype='image/jpeg')
            
    except Exception as e:
        return f"Camera capture error: {e}", 500
        
    return "Failed to fetch image data from camera sensor.", 500

if __name__ == '__main__':
    PORT = 5000
    IP_ADDR = get_ip_address()
    
    print("=" * 50)
    print("      MINIMAL ON-DEMAND CAMERA SERVER          ")
    print("=" * 50)
    print(f"[*] Access URL: http://{IP_ADDR}:{PORT}/video_feed")
    print("=" * 50)
    
    # use_reloader=False blocks Flask from starting double sub-threads inside Termux
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
