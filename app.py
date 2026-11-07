import socket
import subprocess
import time
from flask import Flask, Response

app = Flask(__name__)

def get_ip_address():
    """Dynamically get the device's local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable, this just establishes an interface connection
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def generate_frames():
    """
    Spawns termux-camera-video to dump stream bytes to stdout.
    Reads chunks and wraps them in an HTTP MJPEG boundary packet stream.
    """
    # -d 0 specifies the back camera. Use -d 1 for front camera.
    # The trailing hyphen '-' tells Termux to pipe raw video to stdout.
    cmd = ["termux-camera-video", "-d", "0", "-"]
    
    # Spawn the process
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    try:
        while True:
            # Read chunks of the video stream data
            # Adjust the buffer size depending on network performance and resolution
            chunk = process.stdout.read(4096)
            if not chunk:
                break
                
            # Yield the chunk directly into the multipart HTTP frame chunking pipeline
            yield chunk
    except Exception as e:
        print(f"\n[!] Stream Error: {e}")
    finally:
        process.terminate()

@app.route('/video_feed')
def video_feed():
    """HTTP Stream Route providing the multipart boundary output."""
    return Response(
        generate_frames(),
        mimetype='video/x-motion-jpeg'
    )

if __name__ == '__main__':
    PORT = 5000
    IP_ADDR = get_ip_address()
    
    print("=" * 50)
    print("      TERMUX API CAMERA SERVER IS ALIVE        ")
    print("=" * 50)
    print(f"[*] Local Host IP Address: {IP_ADDR}")
    print(f"[*] Live Streaming URL   : http://{IP_ADDR}:{PORT}/video_feed")
    print("=" * 50)
    print("[ Press Ctrl+C to stop the stream server safely ]\n")
    
    # Run the server accessible to any device on the local network
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
