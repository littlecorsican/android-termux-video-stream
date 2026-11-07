# this one is for the newer version , as termux-camera-video is deprecated

import os
import socket
import subprocess
import time
from flask import Flask, Response

app = Flask(__name__)

def get_ip_address():
    """Dynamically get the device's local network IP address."""
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
    """
    Loops continuously taking snapshot bytes from termux-camera-photo
    and streams them sequentially to create an MJPEG video stream.
    """
    # -c 0 specifies the back camera. Use -c 1 for front camera.
    # The output is sent to stdout using the trailing hyphen '-'
    cmd = ["termux-camera-photo", "-c", "0", "-"]
    
    while True:
        try:
            # Execute the photo snapshot command and capture raw byte output
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            frame = process.stdout
            
            # Ensure we got actual picture data before serving it
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            # Tiny sleep interval to prevent CPU throttling (adjust for speed vs battery)
            time.sleep(0.05)
            
        except Exception as e:
            print(f"\n[!] Stream Error: {e}")
            break

@app.route('/video_feed')
def video_feed():
    """HTTP Stream Route providing the multipart boundary output."""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

if __name__ == '__main__':
    PORT = 5000
    IP_ADDR = get_ip_address()
    
    # Automatically engage CPU lock when starting so it runs when screen turns off
    print("[*] Engaging Termux Wake-Lock...")
    os.system('termux-wake-lock &')
    
    print("=" * 50)
    print("      TERMUX API CAMERA SERVER IS ALIVE        ")
    print("=" * 50)
    print(f"[*] Local Host IP Address: {IP_ADDR}")
    print(f"[*] Live Streaming URL   : http://{IP_ADDR}:{PORT}/video_feed")
    print("=" * 50)
    print("[ Press Ctrl+C to stop the stream server safely ]\n")
    
    try:
        # Run the server accessible to any device on the local network
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
    finally:
        # Clean up and release the CPU lock so your battery can rest
        print("[*] Releasing Termux Wake-Lock...")
        os.system('termux-wake-unlock &')
