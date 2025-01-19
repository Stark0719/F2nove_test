### Main Program (main.py)
import socket
import pygame
from video_stream import VideoStream
from ps5_controller import PS5Controller

# Server details
SERVER_IP = "192.168.1.141"
CONTROL_PORT = 5000
VIDEO_PORT = 8000

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Car Control and Video Stream")
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

def main():
    try:
        # Initialize video streaming and controller
        video_stream = VideoStream(SERVER_IP, VIDEO_PORT)
        ps5_controller = PS5Controller(SERVER_IP, CONTROL_PORT)

        running = True
        while running:
            screen.fill((0, 0, 0))  # Black background

            # Draw buttons
            start_button = pygame.draw.rect(screen, (0, 255, 0), (100, 100, 200, 50))
            stop_button = pygame.draw.rect(screen, (255, 0, 0), (100, 200, 200, 50))

            # Add text to buttons
            start_text = font.render("Stream ON", True, (0, 0, 0))
            stop_text = font.render("Stream OFF", True, (0, 0, 0))
            screen.blit(start_text, (150, 115))
            screen.blit(stop_text, (145, 215))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if start_button.collidepoint(event.pos):
                        print("Stream Video ON clicked")
                        video_stream.start()
                    elif stop_button.collidepoint(event.pos):
                        print("Stream Video OFF clicked")
                        video_stream.stop()

                # Handle PS5 controller events
                ps5_controller.handle_event(event)

            pygame.display.flip()
            clock.tick(30)

        video_stream.stop()
        ps5_controller.close()
        pygame.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()