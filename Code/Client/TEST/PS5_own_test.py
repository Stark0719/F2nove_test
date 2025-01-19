import socket
import pygame
import math

# Server details (replace with the actual server IP and port)
SERVER_IP = "192.168.1.141"  # Replace with server IP
PORT = 5000  # This should match the port on which the server listens for commands

# Flag to track the current command state
current_command = None

def send_command(client_socket, command):
    """Send a command to the server over TCP"""
    global current_command
    try:
        if current_command != command:  # Avoid sending duplicate commands
            client_socket.sendall(command.encode('utf-8'))
            current_command = command
            print(f"Sent command: {command.strip()}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Client is running. Use the PS5 controller to control the car:")
    print("Left Stick (Vertical) - Move Forward/Backward")
    print("Right Stick (Horizontal) - Turn Left/Right")
    print("Circle Button - Quit")
    
    # Initialize pygame for controller input
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("No controller found. Please connect a PS5 controller.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Connected to {joystick.get_name()}")

    # Open the socket once, before the loop starts
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, PORT))
        print(f"Connected to server at {SERVER_IP}:{PORT}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    # Axis 1: Left Stick Vertical (Forward/Backward)
                    # Axis 2: Right Stick Horizontal (Turn Left/Right)
                    forward = joystick.get_axis(1)  # Forward/Backward motion
                    turn = joystick.get_axis(2)  # Left/Right turning motion
                    
                    # Dead zone adjustment (ignore small movements)
                    if abs(forward) < 0.1:
                        forward = 0
                    if abs(turn) < 0.1:
                        turn = 0

                    # Combine forward and turning inputs
                    max_speed = 1500
                    left_motor = int((forward - turn) * -max_speed)  # Left motor speed
                    right_motor = int((forward + turn) * -max_speed)  # Right motor speed
                    
                    # Normalize motor speeds to prevent overflow
                    max_motor_speed = max(abs(left_motor), abs(right_motor))
                    if max_motor_speed > max_speed:
                        left_motor = int(left_motor / max_motor_speed * max_speed)
                        right_motor = int(right_motor / max_motor_speed * max_speed)

                    # Send commands to the car
                    if forward != 0 or turn != 0:
                        send_command(client_socket, f"CMD_MOTOR#{left_motor}#{left_motor}#{right_motor}#{right_motor}\n")
                    else:
                        # Stop when no input
                        send_command(client_socket, "CMD_MOTOR#0#0#0#0\n")

                elif event.type == pygame.JOYBUTTONDOWN:
                    # Button 1 (Circle Button) to quit
                    if joystick.get_button(1):  # Circle Button
                        print("Quitting...")
                        running = False
                        break
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        # Close the socket and clean up
        client_socket.close()
        joystick.quit()
        pygame.quit()

if __name__ == "__main__":
    main()
