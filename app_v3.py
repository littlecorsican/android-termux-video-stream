import os
import socket
import subprocess
import time
import threading
from flask import Flask, Response

app = Flask(__name__)

# System paths
TMP_DIR = "/data/data/com.termux/files/usr/tmp"
os.makedirs(TMP_DIR, exist_ok=True)
FRAME_PATH = os.path.join(TMP_DIR, "live_frame.jpg")

# Global variables to store the image buffer in RAM memory
latest_frame = b''
frame_lock = threading.Lock()

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

def camera_capture_thread():
    """
    Runs completely independently in the background.
    Continuously snapshots the camera hardware and updates the RAM memory buffer.
    """
    global latest_frame
    cmd = ["termux-camera-photo", "-c", "0", FRAME_PATH]
    
    print("[*] Background Camera Thread Started.")
    while True:
        try:
            # Force close old API holds
            subprocess.run(["pkill", "-f", "com.termux.api"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Capture snapshot to file
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=4)
            
            # If the image was successfully captured, read it straight into RAM
            if os.path.exists(FRAME_PATH) and os.path.getsize(FRAME_PATH) > 0:
                with open(FRAME_PATH, "rb") as f:
                    data = f.read()
                
                # Safely update the global frame pointer using a thread lock
                with frame_lock:
                    latest_frame = data
            
            # Tiny sleep to allow thread context switching
            time.sleep(0.01)
            
        except Exception as e:
            print(f"\n[!] Camera Thread Warning: {e}")
            time.sleep(1)

def generate_frames():
    """Serves the latest frame stored in RAM instantly to the web browser."""
    global latest_frame
    while True:
        with frame_lock:
            # Copy the current frame data out of the lock block quickly
            frame = latest_frame
        
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + 
                   frame + b'\r\n')
        
        # Target ~10 frame checks per second for the browser delivery loop
        time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    PORT = 5000
    IP_ADDR = get_ip_address()
    
    print("[*] Engaging Termux Wake-Lock...")
    os.system('termux-wake-lock &')
    
    # --- LAUNCH CAMERA ON A INDEPENDENT WORKER THREAD ---
    cam_thread = threading.Thread(target=camera_capture_thread, daemon=True)
    cam_thread.start()
    
    print("=" * 50)
    print("       THREAD-DECOUPLED NATIVE STREAM SERVER       ")
    print("=" * 50)
    print(f"[*] Local Host IP Address: {IP_ADDR}")
    print(f"[*] Live Streaming URL   : http://{IP_ADDR}:{PORT}/video_feed")
    print("=" * 50)
    print("[ Press Ctrl+C to stop the stream server safely ]\n")
    
    try:
        # Run Flask server normally
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
    finally:
        os.system('termux-wake-unlock &')
        if os.path.exists(FRAME_PATH):
            os.remove(FRAME_PATH)
