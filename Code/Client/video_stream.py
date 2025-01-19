import socket
import cv2
import numpy as np
import struct
from PIL import Image
import io

class VideoStream:
    def __init__(self, server_ip, video_port):
        self.server_ip = server_ip
        self.video_port = video_port
        self.video_streaming = False

    def start(self):
        if not self.video_streaming:
            self.video_streaming = True
            self._stream_video()

    def stop(self):
        self.video_streaming = False

    def _is_valid_image(self, buf):
        """Validate if the received buffer is a valid JPEG image."""
        if buf[6:10] in (b'JFIF', b'Exif'):
            if not buf.rstrip(b'\0\r\n').endswith(b'\xff\xd9'):
                return False
        try:
            Image.open(io.BytesIO(buf)).verify()
            return True
        except Exception:
            return False

    def _stream_video(self):
        """Stream video from the server."""
        try:
            video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            video_socket.connect((self.server_ip, self.video_port))
            print("Connected to video stream.")

            stream_bytes = b""

            while self.video_streaming:
                # Read the 4-byte frame size
                frame_header = video_socket.recv(4)
                if len(frame_header) < 4:
                    print("Incomplete frame header. Stopping stream.")
                    break

                frame_size = struct.unpack('<L', frame_header)[0]

                # Read the frame data
                frame_data = b""
                while len(frame_data) < frame_size:
                    packet = video_socket.recv(frame_size - len(frame_data))
                    if not packet:
                        print("Incomplete frame data. Stopping stream.")
                        break
                    frame_data += packet

                if not self._is_valid_image(frame_data):
                    print("Invalid frame received.")
                    continue

                # Decode and display the frame
                frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    cv2.imshow("Raspberry Pi Video Stream", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.video_streaming = False
                        break

            video_socket.close()
            cv2.destroyAllWindows()
            print("Video stream stopped.")
        except Exception as e:
            print(f"Error in video streaming: {e}")
            cv2.destroyAllWindows()







# ### Video Stream Module (video_stream.py)
# import socket
# import cv2
# import numpy as np
# import threading

# class VideoStream:
#     def __init__(self, server_ip, video_port):
#         self.server_ip = server_ip
#         self.video_port = video_port
#         self.video_streaming = False
#         self.stream_thread = None

#     def start(self):
#         if not self.video_streaming:
#             self.video_streaming = True
#             self.stream_thread = threading.Thread(target=self._stream_video)
#             self.stream_thread.start()

#     def stop(self):
#         self.video_streaming = False
#         if self.stream_thread and self.stream_thread.is_alive():
#             self.stream_thread.join()

#     def _stream_video(self):
#         try:
#             video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             video_socket.connect((self.server_ip, self.video_port))
#             print("Connected to video stream.")

#             data = b""
#             payload_size = 4

#             while self.video_streaming:
#                 while len(data) < payload_size:
#                     packet = video_socket.recv(4 * 1024)
#                     if not packet:
#                         print("No data received. Stopping stream.")
#                         self.video_streaming = False
#                         break
#                     data += packet
#                 if len(data) < payload_size:
#                     break

#                 packed_msg_size = data[:payload_size]
#                 data = data[payload_size:]
#                 msg_size = int.from_bytes(packed_msg_size, byteorder="little")

#                 while len(data) < msg_size:
#                     packet = video_socket.recv(4 * 1024)
#                     if not packet:
#                         print("Incomplete frame received. Stopping stream.")
#                         self.video_streaming = False
#                         break
#                     data += packet
#                 if not self.video_streaming:
#                     break

#                 frame_data = data[:msg_size]
#                 data = data[msg_size:]

#                 frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
#                 if frame is not None:
#                     cv2.imshow("Raspberry Pi Video Stream", frame)
#                     if cv2.waitKey(1) & 0xFF == ord("q"):
#                         self.video_streaming = False
#                         break
#                 else:
#                     print("Error decoding frame.")
#                     self.video_streaming = False

#             video_socket.close()
#             cv2.destroyAllWindows()
#             print("Video stream stopped.")
#         except Exception as e:
#             print(f"Error in video streaming: {e}")
#             cv2.destroyAllWindows()