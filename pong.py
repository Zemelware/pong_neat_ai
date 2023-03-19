import pygame
import random

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

BACKGROUND = BLACK

# Set the width and height of the screen [width, height]
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 500
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

FPS = 60

BALL_RADIUS = 10
BALL_LOWER_SPEED_RANGE = 4
BALL_UPPER_SPEED_RANGE = 7
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
PADDLE_SPEED = 8

# Set the title of the window
pygame.display.set_caption("Pong")


class Ball:
    def __init__(self, x, y, radius, lower_speed_range, upper_speed_range):
        self.x = x
        self.y = y
        self.radius = radius
        self.lower_speed_range = lower_speed_range
        self.upper_speed_range = upper_speed_range
        self.speed = random.randint(lower_speed_range, upper_speed_range)
        self.x_direction = random.choice([1, -1])
        self.y_direction = random.choice([1, -1])
        self.x_velocity = self.speed * self.x_direction
        self.y_velocity = self.speed * self.y_direction

    def update(self):
        self.x += self.x_velocity
        self.y += self.y_velocity

        # Check for collision with top and bottom walls
        if self.y - self.radius <= 0 or self.y + self.radius >= SCREEN_HEIGHT:
            self.y_velocity *= -1

    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.speed = random.randint(
            self.lower_speed_range, self.upper_speed_range)
        self.x_direction = random.choice([1, -1])
        self.y_direction = random.choice([1, -1])
        self.x_velocity = self.speed * self.x_direction
        self.y_velocity = self.speed * self.y_direction


class Paddle:
    def __init__(self, x, y, width, height, speed, up_key, down_key, score=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.up_key = up_key
        self.down_key = down_key
        self.score = score

    def update(self, keys):
        # Move the paddle based on the key pressed
        if keys[self.up_key]:
            self.y -= self.speed
        if keys[self.down_key]:
            self.y += self.speed

        # Make sure the paddle doesn't go off the screen
        if self.y < 0:
            self.y = 0
        elif self.y + self.height > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.height


def update_game_objects(keys, ball, paddle1, paddle2):
    paddle1.update(keys)
    paddle2.update(keys)

    ball.update()

    # Check for collision with paddles
    if (ball.x - ball.radius <= paddle1.x + paddle1.width and
            paddle1.y <= ball.y <= paddle1.y + paddle1.height):
        ball.x_direction = 1
        ball.x_velocity = ball.speed * ball.x_direction

    if (ball.x + ball.radius >= paddle2.x and
            paddle2.y <= ball.y <= paddle2.y + paddle2.height):
        ball.x_direction = -1
        ball.x_velocity = ball.speed * ball.x_direction

    # Increase the score if a player scores
    if ball.x - ball.radius <= 0:
        ball.reset()
        paddle2.score += 1
    elif ball.x + ball.radius >= SCREEN_WIDTH:
        ball.reset()
        paddle1.score += 1


def draw_game_objects(screen, font, ball, paddle1, paddle2):
    # Clear the screen
    screen.fill(BACKGROUND)

    # Draw the ball and paddles
    pygame.draw.rect(
        screen, WHITE, [paddle1.x, paddle1.y, paddle1.width, paddle1.height])
    pygame.draw.rect(
        screen, WHITE, [paddle2.x, paddle2.y, paddle2.width, paddle2.height])
    pygame.draw.circle(screen, WHITE, [ball.x, ball.y], ball.radius)

    # Draw a dotted line down the middle
    for i in range(0, SCREEN_HEIGHT, 35):
        pygame.draw.rect(screen, WHITE, [SCREEN_WIDTH // 2 - 2, i, 4, 20])

    # Draw the scores
    score_y_offset = 15
    score_centre_offset = 30
    paddle1_score_text = font.render(str(paddle1.score), True, WHITE)
    paddle2_score_text = font.render(str(paddle2.score), True, WHITE)
    screen.blit(paddle1_score_text, (SCREEN_WIDTH // 2 -
                paddle1_score_text.get_width() - score_centre_offset, score_y_offset))
    screen.blit(paddle2_score_text, (SCREEN_WIDTH //
                2 + score_centre_offset, score_y_offset))

    pygame.display.update()


def play_game():
    pygame.init()

    font = pygame.font.Font(None, 70)

    ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_RADIUS,
                BALL_LOWER_SPEED_RANGE, BALL_UPPER_SPEED_RANGE)

    paddle_x_offset = 20
    paddle1 = Paddle(paddle_x_offset, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH,
                     PADDLE_HEIGHT, PADDLE_SPEED, pygame.K_w, pygame.K_s)
    paddle2 = Paddle(SCREEN_WIDTH - PADDLE_WIDTH - paddle_x_offset, SCREEN_HEIGHT // 2 -
                     PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED, pygame.K_UP, pygame.K_DOWN)

    clock = pygame.time.Clock()

    # Main game loop
    while True:

        # Get quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break

        # Get pressed keys (returns the state of all keys)
        keys = pygame.key.get_pressed()

        update_game_objects(keys, ball, paddle1, paddle2)

        draw_game_objects(screen, font, ball, paddle1, paddle2)

        # Limit to 60 FPS
        clock.tick(FPS)

    pygame.quit()


if __name__ == '__main__':
    play_game()
