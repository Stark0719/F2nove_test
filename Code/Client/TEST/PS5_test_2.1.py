import pygame
import socket
import time
from Command import COMMAND as cmd

class PS5Controller:
    def __init__(self, server_ip, server_port):
        pygame.init()
        pygame.joystick.init()
        self.intervalChar = '#'
        self.endChar = '\n'
        self.connect_Flag = False

        # Connect to data socket (client_socket1)
        self.client_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket1.connect((server_ip, server_port))
        self.connect_Flag = True
        print(f"Connected to server at {server_ip}:{server_port}")

        # Initialize joystick
        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No joystick detected. Please connect your PS5 controller.")
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        print(f"Initialized controller: {self.joystick.get_name()}")

        # Deadzone for joystick
        self.deadzone = 0.2

        # Set car to manual mode
        self.sendData(cmd.CMD_MODE, ['one'])

    def sendData(self, command_prefix, data):
        if self.connect_Flag:
            command = command_prefix + self.intervalChar.join(map(str, data)) + self.endChar
            try:
                self.client_socket1.send(command.encode('utf-8'))
                print(f"Sent: {command}")
            except Exception as e:
                print(f"Error sending command: {e}")

    def process_inputs(self):
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                self.handle_button_down(event.button)
            elif event.type == pygame.JOYBUTTONUP:
                self.handle_button_up(event.button)
            elif event.type == pygame.JOYAXISMOTION:
                self.handle_axis_motion(event.axis, event.value)

        time.sleep(0.05)

    def handle_button_down(self, button):
        if button == 0:  # X Button (Move forward)
            self.sendData(cmd.CMD_M_MOTOR, [0, 1500, 0, 0])
        elif button == 1:  # Circle Button (Move backward)
            self.sendData(cmd.CMD_M_MOTOR, [180, 1500, 0, 0])
        elif button == 2:  # Square Button (Turn left)
            self.sendData(cmd.CMD_M_MOTOR, [-90, 1500, 0, 0])
        elif button == 3:  # Triangle Button (Turn right)
            self.sendData(cmd.CMD_M_MOTOR, [90, 1500, 0, 0])

    def handle_button_up(self, button):
        self.sendData(cmd.CMD_M_MOTOR, [0, 0, 0, 0])  # Stop

    def handle_axis_motion(self, axis, value):
        if abs(value) < self.deadzone:
            value = 0
        if axis == 1:  # Forward/Backward
            speed = int(-value * 1500)
            self.sendData(cmd.CMD_M_MOTOR, [0, speed, 0, 0])
        elif axis == 0:  # Left/Right
            turn = int(value * 1500)
            self.sendData(cmd.CMD_M_MOTOR, [turn, 1500, 0, 0])


if __name__ == "__main__":
    SERVER_IP = "192.168.1.141"
    SERVER_PORT = 8000

    controller = PS5Controller(SERVER_IP, SERVER_PORT)
    print("Listening for controller inputs...")

    try:
        while True:
            controller.process_inputs()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        pygame.quit()
        controller.client_socket1.close()
