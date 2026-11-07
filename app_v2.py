# this one is for the newer version , as termux-camera-video is deprecated


import os
import socket
import time
import subprocess
from flask import Flask, Response

app = Flask(__name__)

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
    # Use -c 0 for back camera, -c 1 for front camera.
    # The trailing hyphen '-' tells newer versions to attempt output piping,
    # but we will enforce a strict execution timeout to prevent hanging.
    cmd = ["termux-camera-photo", "-c", "0", "-"]
    
    while True:
        try:
            # Clean up the background api service before each shot to prevent deadlocks
            subprocess.run(["pkill", "-f", "com.termux.api"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Execute the photo snapshot directly into memory bytes
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=4)
            frame = result.stdout
            
            # Valid JPEGs start with these specific hex bytes (0xff 0xd8)
            if frame and frame.startswith(b'\xff\xd8'):
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            # Small cooldown so your phone's camera sensor doesn't overheat
            time.sleep(0.1)
            
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            print(f"[!] Stream loop error: {e}")
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
    print("      TERMUX API CAMERA SERVER IS LIVE        ")
    print("=" * 50)
    print(f"[*] Local Host IP Address: {IP_ADDR}")
    print(f"[*] Live Streaming URL   : http://{IP_ADDR}:{PORT}/video_feed")
    print("=" * 50)
    print("[ Press Ctrl+C to stop the stream server safely ]\n")
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
    finally:
        print("[*] Releasing Termux Wake-Lock...")
        os.system('termux-wake-unlock &')
