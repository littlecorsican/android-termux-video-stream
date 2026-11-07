import cv2
import socket
from mjpeg_streamer import MjpegServer, Stream

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

HOST = "0.0.0.0"
PORT = 8080
STREAM_NAME = "my_camera"

cap = cv2.VideoCapture(0)
stream = Stream(STREAM_NAME, size=(640, 480), quality=50, fps=30)

server = MjpegServer(HOST, PORT)
server.add_stream(stream)
server.start()

# ---- Print access info ----
ip = get_local_ip()
print("=" * 50)
print(f"📡 MJPEG stream is live!")
print(f"   Local:    http://127.0.0.1:{PORT}/{STREAM_NAME}")
print(f"   Network:  http://{ip}:{PORT}/{STREAM_NAME}")
print("=" * 50)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        stream.set_frame(frame)
finally:
    cap.release()
    server.stop()
    print("\n🛑 Stream stopped.")
