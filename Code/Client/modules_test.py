import socket
import pygame

# Server details
SERVER_IP = "192.168.1.141"
PORT = 5000

current_command = None

# Initialize servo angles
servo_0_angle = 90  # Default angle for servo 0
servo_1_angle = 90  # Default angle for servo 1
angle_step = 10  # Amount to adjust the angle per button press
min_angle = 0  # Minimum angle
max_angle = 180  # Maximum angle

def send_command(client_socket, command):
    """Send a command to the server."""
    global current_command
    try:
        if current_command != command:
            client_socket.sendall(command.encode("utf-8"))
            current_command = command
            print(f"Sent command: {command.strip()}")
    except Exception as e:
        print(f"Error: {e}")

def handle_button_input(joystick, client_socket):
    """Handle button input for servo control."""
    global servo_0_angle, servo_1_angle

    # Cross Button (Button 0) - Increment servo_0 angle
    if joystick.get_button(0):  # Cross Button
        servo_0_angle = min(servo_0_angle + angle_step, max_angle)
        send_command(client_socket, f"CMD_SERVO#0#{servo_0_angle}\n")

    # Circle Button (Button 1) - Decrement servo_0 angle
    if joystick.get_button(1):  # Circle Button
        servo_0_angle = max(servo_0_angle - angle_step, min_angle)
        send_command(client_socket, f"CMD_SERVO#0#{servo_0_angle}\n")

    # Square Button (Button 2) - Decrement servo_1 angle
    if joystick.get_button(2):  # Square Button
        servo_1_angle = max(servo_1_angle - angle_step, min_angle)
        send_command(client_socket, f"CMD_SERVO#1#{servo_1_angle}\n")

    # Triangle Button (Button 3) - Increment servo_1 angle
    if joystick.get_button(3):  # Triangle Button
        servo_1_angle = min(servo_1_angle + angle_step, max_angle)
        send_command(client_socket, f"CMD_SERVO#1#{servo_1_angle}\n")

def main():
    print("Client is running. Use the PS5 controller to control the car:")
    print("Left Stick: Move Forward/Backward")
    print("Right Stick: Turn Left/Right")
    print("Cross: Increment Servo 0")
    print("Circle: Decrement Servo 0")
    print("Square: Decrement Servo 1")
    print("Triangle: Increment Servo 1")
    print("Share Button: Quit")

    # Initialize pygame for controller input
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No controller found. Please connect a PS5 controller.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Connected to {joystick.get_name()}")

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
                    # Handle car movement with joysticks
                    forward_backward = joystick.get_axis(1)
                    left_right = joystick.get_axis(2)

                    if abs(forward_backward) < 0.1:
                        forward_backward = 0
                    if abs(left_right) < 0.1:
                        left_right = 0

                    forward_speed = int(forward_backward * -1500)
                    turn_speed = int(left_right * 1500)

                    if forward_speed != 0 or turn_speed != 0:
                        left_motor = forward_speed + turn_speed
                        right_motor = forward_speed - turn_speed
                        send_command(client_socket, f"CMD_MOTOR#{left_motor}#{left_motor}#{right_motor}#{right_motor}\n")
                    else:
                        send_command(client_socket, "CMD_MOTOR#0#0#0#0\n")

                elif event.type == pygame.JOYBUTTONDOWN:
                    # Handle servo control with buttons
                    handle_button_input(joystick, client_socket)

                    # Quit on Share Button (Optional: Replace 8 with the actual index for Share Button)
                    if joystick.get_button(8):  # Share Button
                        print("Quitting...")
                        running = False
                        break
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        client_socket.close()
        pygame.quit()

if __name__ == "__main__":
    main()
