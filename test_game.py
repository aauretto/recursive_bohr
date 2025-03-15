import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Draggable Ball")

# Colors
white = (255, 255, 255)
red = (255, 0, 0)

# Ball properties
ball_pos = [width // 2, height // 2]
ball_speed = [3, 3]
ball_radius = 20
dragging = False  # Track if the ball is being dragged

# Clock to control frame rate
clock = pygame.time.Clock()

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Mouse button down (start dragging)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            distance = ((mouse_x - ball_pos[0]) ** 2 + (mouse_y - ball_pos[1]) ** 2) ** 0.5
            if distance <= ball_radius:
                dragging = True

        # Mouse button up (stop dragging)
        if event.type == pygame.MOUSEBUTTONUP:
            dragging = False

        # Mouse movement (dragging)
        if event.type == pygame.MOUSEMOTION and dragging:
            ball_pos = list(event.pos)

    # Update ball position (if not dragging)
    if not dragging:
        ball_pos[0] += ball_speed[0]
        ball_pos[1] += ball_speed[1]

        # Bounce off walls
        if ball_pos[0] <= ball_radius or ball_pos[0] >= width - ball_radius:
            ball_speed[0] = -ball_speed[0]
        if ball_pos[1] <= ball_radius or ball_pos[1] >= height - ball_radius:
            ball_speed[1] = -ball_speed[1]

    # Fill the screen with white
    screen.fill(white)

    # Draw the ball
    pygame.draw.circle(screen, red, ball_pos, ball_radius)

    # Update the display
    pygame.display.flip()

    # Frame rate
    clock.tick(60)
