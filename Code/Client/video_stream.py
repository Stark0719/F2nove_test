# video_stream.py
import socket
import cv2
import numpy as np
import struct
from PIL import Image
import io
import threading
import sys

class VideoStream:
    def __init__(self, server_ip, video_port, haarcascade_path="haarcascade_frontalface_default.xml"):
        self.server_ip = server_ip
        self.video_port = video_port

        # For controlling streaming and threading
        self.video_streaming = False
        self.thread = None
        self.lock = threading.Lock()

        # Shared frame in BGR, updated every time we decode
        self.current_frame = None

        # Face detection
        self.track_face = False  # Toggle on/off from the main script if desired
        self.face_cascade = cv2.CascadeClassifier(haarcascade_path)
        self.face_x = 0.0
        self.face_y = 0.0

    def start(self):
        """Start streaming in a background thread."""
        if self.video_streaming:
            print("[VideoStream] Already streaming.")
            return

        print("[VideoStream] Starting stream (background thread)...")
        self.video_streaming = True
        self.thread = threading.Thread(target=self._stream_video, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the video stream and wait for the thread to finish."""
        if self.video_streaming:
            print("[VideoStream] Stopping stream...")
            self.video_streaming = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)
            self.thread = None

        self.face_x = 0.0
        self.face_y = 0.0
        self.current_frame = None
        print("[VideoStream] Stream stopped.")

    def enable_face_tracking(self, enabled=True):
        """Toggle face detection on/off."""
        self.track_face = enabled

    def get_frame(self):
        """
        Return a copy of the latest frame (thread-safe).
        Return None if no frame is available.
        """
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def get_face_coords(self):
        """Returns (face_x, face_y) as last detected face center, or (0,0) if none."""
        return (self.face_x, self.face_y)

    def _stream_video(self):
        try:
            video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            video_socket.connect((self.server_ip, self.video_port))
            print("[VideoStream] Connected to video stream.")

            while self.video_streaming:
                # Read the 4-byte frame size
                header = video_socket.recv(4)
                if len(header) < 4:
                    print("[VideoStream] Incomplete frame header, stopping...")
                    break

                frame_size = struct.unpack('<L', header)[0]
                if frame_size <= 0:
                    print("[VideoStream] Invalid frame size, stopping...")
                    break

                # Read entire frame
                frame_data = b""
                while len(frame_data) < frame_size:
                    packet = video_socket.recv(frame_size - len(frame_data))
                    if not packet:
                        print("[VideoStream] Incomplete frame data, stopping...")
                        break
                    frame_data += packet

                # Validate / decode
                if not self._is_valid_jpeg(frame_data):
                    print("[VideoStream] Invalid frame, skipping...")
                    continue

                frame_bgr = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                if frame_bgr is not None:
                    # Optionally detect faces
                    if self.track_face:
                        frame_bgr = self._detect_and_draw_face(frame_bgr)

                    # Update shared frame
                    with self.lock:
                        self.current_frame = frame_bgr
                else:
                    print("[VideoStream] Failed to decode frame.")

            video_socket.close()
            print("[VideoStream] Socket closed.")
        except Exception as e:
            print(f"[VideoStream] Error: {e}")
        finally:
            self.video_streaming = False
            with self.lock:
                self.current_frame = None
            print("[VideoStream] _stream_video thread exited.")

    def _detect_and_draw_face(self, img_bgr):
        """
        Detect faces in BGR image, draw a circle around the first face,
        and update self.face_x, self.face_y as the face center.
        """
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) > 0:
            # For simplicity, take the first face
            (x, y, w, h) = faces[0]
            self.face_x = x + w/2.0
            self.face_y = y + h/2.0
            # Draw a circle around the face
            center = (int(self.face_x), int(self.face_y))
            radius = int((w+h)/4)
            cv2.circle(img_bgr, center, radius, (0, 255, 0), 2)
        else:
            # No face detected
            self.face_x = 0.0
            self.face_y = 0.0

        return img_bgr

    def _is_valid_jpeg(self, buf):
        """Quick check if buf is a valid JPEG."""
        if len(buf) < 4:
            return False
        # Check for standard JPEG header
        if buf[6:10] in (b'JFIF', b'Exif'):
            if not buf.rstrip(b'\0\r\n').endswith(b'\xff\xd9'):
                return False
        # Attempt reading with PIL
        try:
            Image.open(io.BytesIO(buf)).verify()
            return True
        except:
            return False
