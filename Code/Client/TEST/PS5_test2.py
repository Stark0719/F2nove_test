import socket
from pynput import keyboard
import time

# Server details (replace with the actual server IP and port)
SERVER_IP = "192.168.1.141"  # Replace with server IP
PORT = 5000  # This should match the port on which the server listens for commands

def send_command(client_socket, command):
    """Send a command to the server over TCP"""
    try:
        client_socket.sendall(command.encode('utf-8'))
        print(f"Sent command: {command}")
    except Exception as e:
        print(f"Error: {e}")

def on_press(key, client_socket):
    """Handle key press events."""
    try:
        if key.char == 'w':  # Move Forward
            send_command(client_socket, "CMD_MOTOR#1500#1500#1500#1500\n")
        elif key.char == 's':  # Move Backward
            send_command(client_socket, "CMD_MOTOR#-1500#-1500#-1500#-1500\n")
        elif key.char == 'a':  # Turn Left
            send_command(client_socket, "CMD_MOTOR#-1500#0#0#-1500\n")
        elif key.char == 'd':  # Turn Right
            send_command(client_socket, "CMD_MOTOR#-50#-50#50#50\n")
        elif key.char == 'q':  # Quit
            send_command(client_socket, "CMD_MODE#1#0#0#0\n")  # Stop/Idle Mode
            print("Quitting...")
            return False  # Stop the listener
    except AttributeError:
        pass  # Handle special keys (if any)

def main():
    print("Client is running. Press keys to control the car:")
    print("W - Move Forward")
    print("S - Move Backward")
    print("A - Turn Left")
    print("D - Turn Right")
    print("Q - Quit")
    
    # Open the socket once, before the loop starts
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, PORT))
        print(f"Connected to server at {SERVER_IP}:{PORT}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    # Use a keyboard listener to detect key presses
    with keyboard.Listener(
        on_press=lambda key: on_press(key, client_socket)
    ) as listener:
        listener.join()
    
    # Close the socket when done
    client_socket.close()

if __name__ == "__main__":
    main()
