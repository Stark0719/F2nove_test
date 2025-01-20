# main.py
import pygame
import cv2
import numpy as np
from video_stream import VideoStream
from ps5_controller import PS5Controller

SERVER_IP = "192.168.1.141"
CONTROL_PORT = 5000
VIDEO_PORT = 8000

pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Control + Client-based Face Tracking")
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

def main():
    video_stream = VideoStream(SERVER_IP, VIDEO_PORT, 
                            haarcascade_path="haarcascade_frontalface_default.xml")
    ps5_controller = PS5Controller(SERVER_IP, CONTROL_PORT)

    # Flag for face detection
    face_detect_enabled = False

    # We'll keep track of servo angles in the client
    pan_angle = 90
    tilt_angle = 90
    # Gains: how quickly to rotate per pixel offset
    k_pan = 0.02
    k_tilt = 0.02

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                start_button_rect = pygame.Rect(10, 10, 120, 40)
                stop_button_rect  = pygame.Rect(140, 10, 120, 40)
                face_button_rect  = pygame.Rect(270, 10, 120, 40)

                if start_button_rect.collidepoint(mx, my):
                    video_stream.start()
                elif stop_button_rect.collidepoint(mx, my):
                    video_stream.stop()
                elif face_button_rect.collidepoint(mx, my):
                    face_detect_enabled = not face_detect_enabled
                    video_stream.enable_face_tracking(face_detect_enabled)

            # Also handle PS5 controller events (for manual override if needed)
            ps5_controller.handle_event(event)

        # Display the latest frame
        if video_stream.video_streaming:
            frame_bgr = video_stream.get_frame()
            if frame_bgr is not None:
                # Convert BGR -> RGB for Pygame
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frame_surface = pygame.surfarray.make_surface(
                    np.transpose(frame_rgb, (1, 0, 2))
                )
                frame_surface = pygame.transform.scale(frame_surface, (WIDTH, HEIGHT))
                screen.blit(frame_surface, (0, 0))
            else:
                screen.fill((0, 0, 0))
        else:
            screen.fill((0, 0, 0))

        # Draw buttons
        start_rect = pygame.draw.rect(screen, (0,255,0), (10, 10, 120, 40))
        stop_rect  = pygame.draw.rect(screen, (255,0,0), (140, 10, 120, 40))

        # Face toggle button
        face_color = (0,200,200) if face_detect_enabled else (128,128,128)
        face_rect  = pygame.draw.rect(screen, face_color, (270, 10, 120, 40))

        screen.blit(font.render("Stream ON", True, (0,0,0)),  (15, 15))
        screen.blit(font.render("Stream OFF", True, (0,0,0)), (145, 15))

        face_text = "Face ON" if face_detect_enabled else "Face OFF"
        screen.blit(font.render(face_text, True, (0,0,0)), (275, 15))

        # If face detection is enabled, we get face coords from video_stream
        # We'll move servos automatically to center the face
        if face_detect_enabled:
            face_x, face_y = video_stream.get_face_coords()
            if face_x != 0 or face_y != 0:
                # Draw coords on screen
                coord_text = f"Face: {int(face_x)}, {int(face_y)}"
                screen.blit(font.render(coord_text, True, (255,255,255)), (400, 15))

                # Calculate offset from center of the image
                center_x = WIDTH / 2
                center_y = HEIGHT / 2
                offset_x = face_x - center_x
                offset_y = face_y - center_y

                # Adjust servo angles
                # Pan servo: if offset_x > 0, face is right => reduce pan_angle
                pan_angle -= (offset_x * k_pan)
                # Tilt servo: if offset_y > 0, face is below => increase tilt_angle
                tilt_angle += (offset_y * k_tilt)

                # Clamp angles to [0..180]
                pan_angle  = max(0, min(180, pan_angle))
                tilt_angle = max(0, min(180, tilt_angle))

                # Send new servo angles to Pi
                ps5_controller.send_command(f"CMD_SERVO#0#{int(pan_angle)}\n")
                ps5_controller.send_command(f"CMD_SERVO#1#{int(tilt_angle)}\n")

        pygame.display.flip()
        clock.tick(30)

    # On exit, stop streaming, close controller, quit pygame
    video_stream.stop()
    ps5_controller.close()
    pygame.quit()

if __name__ == "__main__":
    main()
