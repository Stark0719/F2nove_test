# main.py
import pygame
import cv2
import numpy as np
from video_stream2 import VideoStream
from ps5_controller import PS5Controller

SERVER_IP = "192.168.1.141"
CONTROL_PORT = 5000
VIDEO_PORT = 8000

pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Control + Video Stream")
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

def main():
    video_stream = VideoStream(SERVER_IP, VIDEO_PORT)
    ps5_controller = PS5Controller(SERVER_IP, CONTROL_PORT)

    running = True
    while running:
        # -- 1) Process Pygame events --
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Simple clickable buttons
                mx, my = event.pos
                # Hardcode some rect positions
                start_button_rect = pygame.Rect(10, 10, 120, 40)
                stop_button_rect  = pygame.Rect(140, 10, 120, 40)
                if start_button_rect.collidepoint(mx, my):
                    print("[MAIN] Stream ON clicked.")
                    video_stream.start()
                elif stop_button_rect.collidepoint(mx, my):
                    print("[MAIN] Stream OFF clicked.")
                    video_stream.stop()

            # Pass event to PS5 controller
            ps5_controller.handle_event(event)

        # -- 2) Draw the latest video frame in the Pygame window --
        if video_stream.video_streaming:
            frame_bgr = video_stream.get_frame()
            if frame_bgr is not None:
                # Convert BGR -> RGB for Pygame
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

                # Convert the NumPy array to a Pygame surface
                frame_surface = pygame.surfarray.make_surface(
                    np.transpose(frame_rgb, (1, 0, 2))
                )
                # Optionally resize the frame if it's bigger than the window
                frame_surface = pygame.transform.scale(frame_surface, (WIDTH, HEIGHT))

                # Blit the video surface onto the screen
                screen.blit(frame_surface, (0, 0))
            else:
                # If streaming but no frame yet, fill black
                screen.fill((0, 0, 0))
        else:
            # If not streaming, just black out the screen
            screen.fill((0, 0, 0))

        # -- 3) Draw "Stream ON/OFF" buttons on top --
        start_button_rect = pygame.draw.rect(screen, (0,255,0), (10, 10, 120, 40))
        stop_button_rect  = pygame.draw.rect(screen, (255,0,0), (140, 10, 120, 40))
        screen.blit(font.render("Stream ON",  True, (0,0,0)), (15, 15))
        screen.blit(font.render("Stream OFF", True, (0,0,0)), (145, 15))

        # -- 4) Flip the display, limit to ~30 fps --
        pygame.display.flip()
        clock.tick(30)

    # On exit, stop video + close controller
    video_stream.stop()
    ps5_controller.close()
    pygame.quit()

if __name__ == "__main__":
    main()
