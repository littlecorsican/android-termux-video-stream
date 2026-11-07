import os
import socket
import subprocess
import time
from flask import Flask, Response

app = Flask(__name__)

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

def generate_frames():
    # Enforce standard photo command streaming out to stdout '-'
    cmd = ["termux-camera-photo", "-c", "0", "-"]
    
    while True:
        try:
            # Explicitly clear out old API bindings to prevent hardware locks
            subprocess.run(["pkill", "-f", "com.termux.api"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Fetch the raw picture snapshot directly into RAM memory bytes
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=4)
            frame = result.stdout
            
            # Verify the output is a valid JPEG byte-string structure
            if frame and frame.startswith(b'\xff\xd8'):
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + 
                       frame + b'\r\n')
            
            # Minimal sleep buffer so your processor can handle the incoming cycles
            time.sleep(0.05)
            
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            print(f"[!] Frame Loop Issue: {e}")
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
    print("         PURE TERMUX NATIVE STREAM SERVER          ")
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
