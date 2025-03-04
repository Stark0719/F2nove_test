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
pygame.display.set_caption("Car Control + Video + Face Tracking")
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

def main():
    video_stream = VideoStream(SERVER_IP, VIDEO_PORT, 
                        haarcascade_path="haarcascade_frontalface_default.xml")
    ps5_controller = PS5Controller(SERVER_IP, CONTROL_PORT)

    # We'll add a simple face-detect toggle
    face_detect_enabled = False

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

                # Check if we clicked "Stream ON"
                if start_button_rect.collidepoint(mx, my):
                    video_stream.start()

                # Check if we clicked "Stream OFF"
                elif stop_button_rect.collidepoint(mx, my):
                    video_stream.stop()

                # Check if we clicked "Face Detect ON/OFF"
                elif face_button_rect.collidepoint(mx, my):
                    face_detect_enabled = not face_detect_enabled
                    video_stream.enable_face_tracking(face_detect_enabled)

            # PS5 Controller
            ps5_controller.handle_event(event)

        # Draw latest frame
        if video_stream.video_streaming:
            frame_bgr = video_stream.get_frame()
            if frame_bgr is not None:
                # BGR -> RGB
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

        # Face detect button
        face_color = (0, 200, 200) if face_detect_enabled else (128, 128, 128)
        face_rect  = pygame.draw.rect(screen, face_color, (270, 10, 120, 40))

        screen.blit(font.render("Stream ON", True, (0,0,0)),  (15, 15))
        screen.blit(font.render("Stream OFF", True, (0,0,0)), (145, 15))

        face_button_text = "Face ON" if face_detect_enabled else "Face OFF"
        screen.blit(font.render(face_button_text, True, (0,0,0)), (275, 15))

        # Example: If you want to show face coords
        face_x, face_y = video_stream.get_face_coords()
        if face_detect_enabled and (face_x != 0 or face_y != 0):
            coord_text = f"Face: {int(face_x)}, {int(face_y)}"
            screen.blit(font.render(coord_text, True, (255,255,255)), (400, 15))

        pygame.display.flip()
        clock.tick(30)

    video_stream.stop()
    ps5_controller.close()
    pygame.quit()

if __name__ == "__main__":
    main()
