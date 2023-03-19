import os
import random

import neat
import pygame

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
    def __init__(self, x, y, width, height, speed, up_key, down_key, genome, neural_network, score=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.up_key = up_key
        self.down_key = down_key
        self.score = score
        self.genome = genome
        self.neural_network = neural_network

    def update(self, keys, ball, other_paddle):
        # Move the paddle based on the key pressed
        # if keys[self.up_key]:
        #     self.y -= self.speed
        # if keys[self.down_key]:
        #     self.y += self.speed

        # Move the paddle based on the neural network
        # The paddle will be able to see its y position and its distance from the ball
        outputs = self.neural_network.activate(
            (self.y, abs(self.y - ball.y), abs(self.x - ball.x)))
        decision = outputs.index(max(outputs))

        # If decision is 0, do nothing
        # Move the paddle up or down depending on the output
        if decision == 1:
            # AI moves up
            self.y -= self.speed
        elif decision == 2:
            # AI moves down
            self.y += self.speed

        # Make sure the paddle doesn't go off the screen
        if self.y < 0:
            self.y = 0
        elif self.y + self.height > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.height


def update_game_objects(keys, ball, paddle1, paddle2):
    paddle1.update(keys, ball, paddle2)
    paddle2.update(keys, ball, paddle1)

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

    # Increase the score if a player scores. Return True breaks the loop in main() to start a new generation.
    if ball.x - ball.radius <= 0:
        ball.reset()
        paddle2.score += 1
        paddle2.genome.fitness += 2
        paddle1.genome.fitness -= 1

        return True
    elif ball.x + ball.radius >= SCREEN_WIDTH:
        ball.reset()
        paddle1.score += 1
        paddle1.genome.fitness += 2
        paddle2.genome.fitness -= 1

        return True


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


def main_game_loop(genomes, config):

    genomes[0][1].fitness = 0
    genomes[1][1].fitness = 0

    pygame.init()

    font = pygame.font.Font(None, 70)

    ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_RADIUS,
                BALL_LOWER_SPEED_RANGE, BALL_UPPER_SPEED_RANGE)

    paddle_x_offset = 20
    paddle1 = Paddle(paddle_x_offset, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH,
                     PADDLE_HEIGHT, PADDLE_SPEED, pygame.K_w, pygame.K_s,
                     genomes[0][1], neat.nn.FeedForwardNetwork.create(genomes[0][1], config))
    paddle2 = Paddle(SCREEN_WIDTH - PADDLE_WIDTH - paddle_x_offset, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH,
                     PADDLE_HEIGHT, PADDLE_SPEED, pygame.K_UP, pygame.K_DOWN,
                     genomes[1][1], neat.nn.FeedForwardNetwork.create(genomes[1][1], config))

    clock = pygame.time.Clock()

    # Main game loop
    run = True
    while run:

        # Get quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # Get pressed keys (returns the state of all keys)
        keys = pygame.key.get_pressed()

        if update_game_objects(keys, ball, paddle1, paddle2):
            run = False

        draw_game_objects(screen, font, ball, paddle1, paddle2)

        # Limit to 60 FPS
        clock.tick(FPS)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    pop = neat.Population(config)

    pop.add_reporter(neat.StdOutReporter(True))
    pop.add_reporter(neat.StatisticsReporter())

    winner = pop.run(main_game_loop, 200)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    run(config_path)
