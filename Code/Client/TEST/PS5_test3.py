import pygame
import socket
from Command import COMMAND as cmd


class PS5Controller:
    def __init__(self, server_ip, server_port):
        # Initialize Pygame and Joystick
        pygame.init()
        pygame.joystick.init()

        # Initialize the server connection
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.server_port))
        print(f"Connected to server at {self.server_ip}:{self.server_port}")

        # Initialize the first joystick (PS5 controller)
        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No joystick detected. Please connect your PS5 controller.")
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        print(f"Initialized controller: {self.joystick.get_name()}")

        # Deadzone for joystick axes
        self.deadzone = 0.2

    def send_command(self, command):
        """
        Send a command to the server.
        """
        try:
            self.client_socket.sendall(command.encode('utf-8'))
            print(f"Sent: {command.strip()}")
        except Exception as e:
            print(f"Error sending command: {e}")

    def process_inputs(self):
        """
        Process PS5 controller inputs and send corresponding commands to the server.
        """
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                self.handle_button_down(event.button)
            elif event.type == pygame.JOYBUTTONUP:
                self.handle_button_up(event.button)
            elif event.type == pygame.JOYAXISMOTION:
                self.handle_axis_motion(event.axis, event.value)

    def handle_button_down(self, button):
        """
        Handle button presses.
        """
        if button == 0:  # X Button
            self.send_command(f"{cmd.CMD_MOTOR}#1500#1500#1500#1500\n")
        elif button == 1:  # Circle Button
            self.send_command(f"{cmd.CMD_MOTOR}#-1500#-1500#-1500#-1500\n")
        elif button == 2:  # Square Button
            self.send_command(f"{cmd.CMD_MOTOR}#-1500#1500#1500#-1500\n")  # Turn Left
        elif button == 3:  # Triangle Button
            self.send_command(f"{cmd.CMD_MOTOR}#1500#-1500#-1500#1500\n")  # Turn Right

    def handle_button_up(self, button):
        """
        Stop movement when the button is released.
        """
        if button in [0, 1, 2, 3]:  # Stop movement on button release
            self.send_command(f"{cmd.CMD_MOTOR}#0#0#0#0\n")

    def handle_axis_motion(self, axis, value):
        """
        Handle joystick axis movement.
        """
        # Apply deadzone
        if abs(value) < self.deadzone:
            value = 0

        # Left stick for forward/backward (axis 1: vertical)
        if axis == 1:  # Left stick vertical
            speed = int(-value * 1500)  # Map axis value to motor speed
            self.send_command(f"{cmd.CMD_MOTOR}#{speed}#{speed}#{speed}#{speed}\n")

        # Right stick for left/right (axis 0: horizontal)
        elif axis == 0:  # Left stick horizontal (turning)
            turn = int(value * 1500)
            self.send_command(f"{cmd.CMD_MOTOR}#{1500 - turn}#{1500 + turn}#{1500 - turn}#{1500 + turn}\n")


if __name__ == "__main__":
    # Define server IP and port (replace with your server details)
    SERVER_IP = "192.168.1.140"  # Replace with your Freenove car's IP address
    SERVER_PORT = 8000         # Replace with the port used by your server

    # Initialize the PS5 controller
    try:
        controller = PS5Controller(SERVER_IP, SERVER_PORT)
    except RuntimeError as e:
        print(e)
        pygame.quit()
        exit(1)

    print("Listening for controller inputs...")
    try:
        while True:
            controller.process_inputs()
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pygame.quit()
        controller.client_socket.close()
