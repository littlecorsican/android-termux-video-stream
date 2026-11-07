# use mmpeg

import os
import socket
import subprocess
import time
from flask import Flask, Response

app = Flask(__name__)

# Change this to the address provided by your native camera streamer app
# This connects the python engine directly to the high-speed camera stream
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
    Uses FFmpeg to ingest the hardware-accelerated video stream,
    remuxes it cleanly in memory, and pipes it straight to the web browser
    at a flawless 30 frames per second.
    """
    # FFmpeg command to pull the stream instantly with zero caching lag
    cmd = [
        'ffmpeg',
        '-i', CAMERA_STREAM_URL,
        '-f', 'mp4',
        '-movflags', 'frag_keyframe+empty_moov+default_base_moof',
        '-an', # Remove audio to save network bandwidth
        '-vcodec', 'copy', # Directly copy the hardware bytes without re-encoding (ultra-fast!)
        '-'
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    try:
        while True:
            # Read real video stream packets chunk by chunk out of RAM memory
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
    # Serves a professional native MP4 live video feed
    return Response(generate_video_stream(), mimetype='video/mp4')

if __name__ == '__main__':
    PORT = 5000
    IP_ADDR = get_ip_address()
    
    print("[*] Engaging Termux Wake-Lock...")
    os.system('termux-wake-lock &')
    
    print("=" * 50)
    print("      REFINED HIGH-PERFORMANCE VIDEO SERVER        ")
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
