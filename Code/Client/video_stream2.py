# video_stream.py
import socket
import cv2
import numpy as np
import struct
from PIL import Image
import io
import threading

class VideoStream:
    def __init__(self, server_ip, video_port):
        self.server_ip = server_ip
        self.video_port = video_port
        self.video_streaming = False
        self.thread = None
        
        # We store the latest decoded frame in memory.
        # We'll lock access so we don't read while we're writing.
        self.current_frame = None
        self.lock = threading.Lock()

    def start(self):
        """Start streaming in a background thread."""
        if self.video_streaming:
            print("[VideoStream] Already streaming.")
            return

        print("[VideoStream] Starting stream in background...")
        self.video_streaming = True
        self.thread = threading.Thread(target=self._stream_video, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the video stream and wait for the thread to exit."""
        if self.video_streaming:
            print("[VideoStream] Stopping stream...")
            self.video_streaming = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)
            self.thread = None
            self.current_frame = None
        else:
            print("[VideoStream] Stream not running. Nothing to stop.")

    def get_frame(self):
        """
        Return a copy of the latest frame (thread-safe).
        Return None if no frame is available.
        """
        with self.lock:
            if self.current_frame is not None:
                # Make a copy so we don't hand out the same buffer
                return self.current_frame.copy()
            else:
                return None

    def _is_valid_image(self, buf):
        """Validate if the buffer is a valid JPEG image."""
        if len(buf) < 4:
            return False
        # Quick checks for JPEG signature
        if buf[6:10] in (b'JFIF', b'Exif'):
            # Check if it ends with 0xFFD9
            if not buf.rstrip(b'\0\r\n').endswith(b'\xff\xd9'):
                return False
        # Try opening with PIL
        try:
            Image.open(io.BytesIO(buf)).verify()
            return True
        except Exception:
            return False

    def _stream_video(self):
        """Background method: connect to server, read frames, decode to self.current_frame."""
        try:
            video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            video_socket.connect((self.server_ip, self.video_port))
            print("[VideoStream] Connected to video stream.")

            while self.video_streaming:
                # Read the 4-byte frame size
                frame_header = video_socket.recv(4)
                if len(frame_header) < 4:
                    print("[VideoStream] Incomplete frame header. Stopping.")
                    break

                frame_size = struct.unpack('<L', frame_header)[0]
                if frame_size <= 0:
                    print("[VideoStream] Invalid frame size. Stopping.")
                    break

                # Read the entire frame
                frame_data = b""
                while len(frame_data) < frame_size:
                    packet = video_socket.recv(frame_size - len(frame_data))
                    if not packet:
                        print("[VideoStream] Incomplete frame data. Stopping.")
                        break
                    frame_data += packet

                if not self._is_valid_image(frame_data):
                    print("[VideoStream] Invalid frame. Skipping.")
                    continue

                # Decode using OpenCV (BGR format)
                frame_bgr = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                if frame_bgr is not None:
                    # Update the shared frame
                    with self.lock:
                        self.current_frame = frame_bgr
                else:
                    print("[VideoStream] Failed to decode frame.")

            video_socket.close()
            print("[VideoStream] Video socket closed.")
        except Exception as e:
            print(f"[VideoStream] Error in streaming thread: {e}")
        finally:
            self.video_streaming = False
            with self.lock:
                self.current_frame = None
            print("[VideoStream] _stream_video thread exit.")
