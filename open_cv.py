import cv2
from mjpeg_streamer import MjpegServer, Stream

# 1. Open the camera (index 0 usually works)
cap = cv2.VideoCapture(0)

# 2. Configure the stream (size, quality, fps)
stream = Stream("my_camera", size=(640, 480), quality=50, fps=30)

# 3. Start the HTTP server on port 8080
server = MjpegServer("0.0.0.0", 8080) # Use 0.0.0.0 for network access
server.add_stream(stream)
server.start()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    # 4. Feed frames to the stream
    stream.set_frame(frame)
    # (Optional) display locally
    # cv2.imshow(stream.name, frame)
    # if cv2.waitKey(1) == ord("q"): break

# Cleanup
cap.release()
cv2.destroyAllWindows()
server.stop()
