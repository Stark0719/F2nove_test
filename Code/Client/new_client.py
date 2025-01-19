import socket
import struct
import cv2
import numpy as np

# Replace with the IP address of your Raspberry Pi server
HOST = '192.168.1.141'  # Update with your Raspberry Pi's IP
PORT = 8000  # Port used by the server for video streaming (modify if different)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

while True:
    # Receive frame length
    length_data = client_socket.recv(4)
    if not length_data:
        break
    frame_length = struct.unpack('<I', length_data)[0]

    # Receive frame data
    frame_data = b''
    while len(frame_data) < frame_length:
        packet = client_socket.recv(1024)
        if not packet:
            break
        frame_data += packet

    # Decode and display the frame
    frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
    cv2.imshow('Live Stream', frame)

    # Handle user input (e.g., 'q' to quit)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

# Close connection and windows
client_socket.close()
cv2.destroyAllWindows()