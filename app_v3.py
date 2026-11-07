# use mmjpeg



import os
import socket
import subprocess
from flask import Flask, Response

app = Flask(__name__)

# --- CONFIGURATION ---
# Change this to the exact address provided by your camera app.
# Note: For IP Webcam, adding '/video' or '/shot.jpg' provides the raw stream hook.
CAMERA_STREAM_URL = "http://127.0.0" 

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

def generate_video_stream():
    """
    Uses FFmpeg to ingest the hardware stream and convert it to a 
    standard MJPEG stream block by block in memory.
    """
    # FFmpeg parses the input stream and spits out raw MJPEG packets to stdout '-'
    cmd = [
        'ffmpeg',
        '-i', CAMERA_STREAM_URL,
        '-an',                 # Disable audio processing
        '-c:v', 'mjpeg',       # Convert stream packets cleanly to MJPEG
        '-q:v', '5',           # Video quality compression level (1-31, lower is better quality)
        '-f', 'mpjpeg',        # Enforce the motion jpeg network format container
        '-'
    ]
    
    # Spawn FFmpeg as an internal process pipeline
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    try:
        while True:
            # Read image packet chunks out of RAM memory
            data = process.stdout.read(4096)
            if not data:
                break
            yield data
    except Exception as e:
        print(f"[!] Streaming Error: {e}")
    finally:
        process.terminate()

@app.route('/video_feed')
def video_feed():
    # Return the clean, browser-native multipart mixed replace stream protocol
    return Response(
        generate_video_stream(), 
        mimetype='multipart/x-mixed-replace; boundary=--ffmpeg'
    )

if __name__ == '__main__':
    PORT = 5000
    IP_ADDR = get_ip_address()
    
    print("[*] Engaging Termux Wake-Lock...")
    os.system('termux-wake-lock &')
    
    print("=" * 50)
    print("      HIGH-PERFORMANCE BROWSER STREAM SERVER        ")
    print("=" * 50)
    print(f"[*] Local Host IP Address: {IP_ADDR}")
    print(f"[*] Live Streaming URL   : http://{IP_ADDR}:{PORT}/video_feed")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
    finally:
        os.system('termux-wake-unlock &')
