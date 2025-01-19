import socket
import pygame
import threading

class PS5Controller:
    def __init__(self, server_ip, control_port, stop_event):
        self.server_ip = server_ip
        self.control_port = control_port
        self.stop_event = stop_event
        self.current_command = None
        self.client_socket = self._connect()
        self.joystick = self._initialize_joystick()
        self.servo_0_angle = 90  # Default servo 0 angle
        self.servo_1_angle = 90  # Default servo 1 angle
        self.angle_step = 5  # Angle adjustment step
        self.min_angle = 0
        self.max_angle = 180

    def _connect(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_ip, self.control_port))
            print(f"Connected to server at {self.server_ip}:{self.control_port}")
            return client_socket
        except Exception as e:
            print(f"Connection failed: {e}")
            return None

    def _initialize_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("No controller found. Please connect a PS5 controller.")
            return None

        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Connected to {joystick.get_name()}")
        return joystick

    def send_command(self, command):
        try:
            if self.current_command != command:
                self.client_socket.sendall(command.encode("utf-8"))
                self.current_command = command
                print(f"Sent command: {command.strip()}")
        except Exception as e:
            print(f"Error: {e}")

    def handle_event(self, event):
        if event.type == pygame.JOYAXISMOTION:
            forward_backward = self.joystick.get_axis(1)
            left_right = self.joystick.get_axis(2)

            if abs(forward_backward) < 0.1:
                forward_backward = 0
            if abs(left_right) < 0.1:
                left_right = 0

            forward_speed = int(forward_backward * -1500)
            turn_speed = int(left_right * 1500)

            if forward_speed != 0 or turn_speed != 0:
                left_motor = forward_speed + turn_speed
                right_motor = forward_speed - turn_speed
                self.send_command(f"CMD_MOTOR#{left_motor}#{left_motor}#{right_motor}#{right_motor}\n")
            else:
                self.send_command("CMD_MOTOR#0#0#0#0\n")

        elif event.type == pygame.JOYBUTTONDOWN:
            if self.joystick.get_button(8):  # Example button for quitting
                print("Quitting...")
                self.stop_event.set()

            # Map buttons to servos
            if self.joystick.get_button(0):  # Cross button
                self.servo_0_angle = max(self.servo_0_angle - self.angle_step, self.min_angle)
                self.send_command(f"CMD_SERVO#0#{self.servo_0_angle}\n")
            elif self.joystick.get_button(2):  # Circle button
                self.servo_0_angle = min(self.servo_0_angle + self.angle_step, self.max_angle)
                self.send_command(f"CMD_SERVO#0#{self.servo_0_angle}\n")
            elif self.joystick.get_button(3):  # Triangle button
                self.servo_1_angle = min(self.servo_1_angle + self.angle_step, self.max_angle)
                self.send_command(f"CMD_SERVO#1#{self.servo_1_angle}\n")
            elif self.joystick.get_button(1):  # Square button
                self.servo_1_angle = max(self.servo_1_angle - self.angle_step, self.min_angle)
                self.send_command(f"CMD_SERVO#1#{self.servo_1_angle}\n")

    def run(self):
        if not self.joystick:
            print("Joystick not initialized. Exiting PS5 controller thread.")
            return

        try:
            while not self.stop_event.is_set():
                for event in pygame.event.get():
                    self.handle_event(event)
        except Exception as e:
            print(f"Error in PS5 controller thread: {e}")
        finally:
            self.close()

    def close(self):
        if self.client_socket:
            self.client_socket.close()
        print("Controller connection closed.")
