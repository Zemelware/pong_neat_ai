import os
import pickle
import random

import neat
import pygame

TRAINING_AI = False

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (235, 10, 10)

BACKGROUND = BLACK

# Set the width and height of the screen [width, height]
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 500
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

FPS = 60

BALL_RADIUS = 10
BALL_LOWER_SPEED_RANGE = 6
BALL_UPPER_SPEED_RANGE = 9
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
PADDLE_SPEED = 8

# Set the title of the window
pygame.display.set_caption("Pong")


class Ball:
    RADIUS = BALL_RADIUS
    LOWER_SPEED_RANGE = BALL_LOWER_SPEED_RANGE
    UPPER_SPEED_RANGE = BALL_UPPER_SPEED_RANGE

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.randint(
            self.LOWER_SPEED_RANGE, self.UPPER_SPEED_RANGE)
        self.x_direction = random.choice([1, -1])
        self.y_direction = random.choice([0.5, -0.5])
        self.x_velocity = self.speed * self.x_direction
        self.y_velocity = self.speed * self.y_direction

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, [self.x, self.y], self.RADIUS)

    def update(self):
        self.x += self.x_velocity
        self.y += self.y_velocity

        # Check for collision with top and bottom walls
        if self.y - self.RADIUS <= 0 or self.y + self.RADIUS >= SCREEN_HEIGHT:
            self.y_velocity *= -1

    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.speed = random.randint(
            self.LOWER_SPEED_RANGE, self.UPPER_SPEED_RANGE)
        self.x_direction = random.choice([1, -1])
        self.y_direction = random.choice([1, -1])
        self.x_velocity = self.speed * self.x_direction
        self.y_velocity = self.speed * self.y_direction


class Paddle:
    WIDTH = PADDLE_WIDTH
    HEIGHT = PADDLE_HEIGHT
    SPEED = PADDLE_SPEED

    def __init__(self, x, y, up_key, down_key, genome, neural_network, score=0, enable_ai=False):
        self.x = x
        self.y = y
        self.up_key = up_key
        self.down_key = down_key
        self.genome = genome
        self.neural_network = neural_network
        self.score = score
        self.enable_ai = enable_ai

        self.num_hits = 0

    def draw(self, screen):
        pygame.draw.rect(
            screen, WHITE, [self.x, self.y, self.WIDTH, self.HEIGHT])

    def update(self, keys, ball):
        if self.enable_ai:
            # Move the paddle based on the neural network
            # The paddle will be able to see its y position, the ball's y position, and the x distance between the ball and the paddle
            outputs = self.neural_network.activate(
                (self.y, ball.y, abs(self.x - ball.x)))
            decision = outputs.index(max(outputs))

            # Move the paddle up or down depending on the output
            if decision == 0:
                # Discourage the AI from doing nothing
                self.genome.fitness -= 0.01
            elif decision == 1:
                # AI moves up
                self.y -= self.SPEED
            elif decision == 2:
                # AI moves down
                self.y += self.SPEED
        else:
            # Move the paddle based on the key pressed
            if keys[self.up_key]:
                self.y -= self.SPEED
            if keys[self.down_key]:
                self.y += self.SPEED

        # Make sure the paddle doesn't go off the screen
        if self.y < 0:
            self.y = 0
        elif self.y + self.HEIGHT > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.HEIGHT


def update_game_objects(keys, ball, paddle1, paddle2):
    paddle1.update(keys, ball)
    paddle2.update(keys, ball)

    ball.update()

    # Check for collision with paddles
    if (ball.x - ball.RADIUS <= paddle1.x + paddle1.WIDTH and
            paddle1.y <= ball.y <= paddle1.y + paddle1.HEIGHT):
        ball.x_direction = 1
        ball.x_velocity = ball.speed * ball.x_direction
        paddle1.num_hits += 1
        if TRAINING_AI:
            paddle1.genome.fitness += 1

    if (ball.x + ball.RADIUS >= paddle2.x and
            paddle2.y <= ball.y <= paddle2.y + paddle2.HEIGHT):
        ball.x_direction = -1
        ball.x_velocity = ball.speed * ball.x_direction
        paddle2.num_hits += 1
        if TRAINING_AI:
            paddle2.genome.fitness += 1

    # If the paddles have hit the ball 50 times, it's sufficient to end the round (during training)
    if paddle1.num_hits >= 50:
        return True

    # Increase the score if a player scores. Return True breaks the loop in main() to start a new generation.
    if ball.x - ball.RADIUS <= 0:
        ball.reset()
        paddle2.score += 1
        return True
    elif ball.x + ball.RADIUS >= SCREEN_WIDTH:
        ball.reset()
        paddle1.score += 1
        return True


def draw_game_objects(screen, ball, paddle1, paddle2):
    # Clear the screen
    screen.fill(BACKGROUND)

    # Draw the ball and paddles
    paddle1.draw(screen)
    paddle2.draw(screen)
    ball.draw(screen)

    # Draw a dotted line down the middle
    for i in range(0, SCREEN_HEIGHT, 35):
        pygame.draw.rect(screen, WHITE, [SCREEN_WIDTH // 2 - 2, i, 4, 20])

    font = pygame.font.Font(None, 70)

    text_y_offset = 15
    if TRAINING_AI:
        # Draw the total number of hits in the game between both paddles
        total_hits_text = font.render(
            str(paddle1.num_hits + paddle2.num_hits), True, RED)
        screen.blit(total_hits_text, (SCREEN_WIDTH // 2 -
                    total_hits_text.get_width() // 2, text_y_offset))
    else:
        # Draw the scores
        score_centre_offset = 30
        paddle1_score_text = font.render(str(paddle1.score), True, WHITE)
        paddle2_score_text = font.render(str(paddle2.score), True, WHITE)
        screen.blit(paddle1_score_text, (SCREEN_WIDTH // 2 -
                    paddle1_score_text.get_width() - score_centre_offset, text_y_offset))
        screen.blit(paddle2_score_text, (SCREEN_WIDTH //
                    2 + score_centre_offset, text_y_offset))

    pygame.display.update()


def game_loop(genome1, genome2, config):
    pygame.init()

    ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    if not TRAINING_AI:
        try:
            # Load the AI model if it exists
            with open("best_model.pickle", "rb") as f:
                model = pickle.load(f)
                paddle2_neural_net = neat.nn.FeedForwardNetwork.create(
                    model, config)
        except FileNotFoundError:
            paddle2_neural_net = None
        paddle1_neural_net = None
    else:
        paddle1_neural_net = neat.nn.FeedForwardNetwork.create(genome1, config)
        paddle2_neural_net = neat.nn.FeedForwardNetwork.create(genome2, config)

    paddle_x_offset = 20
    paddle1 = Paddle(paddle_x_offset, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, pygame.K_w, pygame.K_s,
                     genome1, paddle1_neural_net, enable_ai=TRAINING_AI)
    paddle2 = Paddle(SCREEN_WIDTH - PADDLE_WIDTH - paddle_x_offset, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, pygame.K_UP, pygame.K_DOWN,
                     genome2, paddle2_neural_net, enable_ai=True)

    clock = pygame.time.Clock()

    # Main game loop
    run = True
    while run:
        # Get quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        # Get pressed keys (returns the state of all keys)
        keys = pygame.key.get_pressed()

        # Function will return True if either player scores
        if update_game_objects(keys, ball, paddle1, paddle2):
            if TRAINING_AI:
                # Break the loop to start a new generation only during training
                run = False

        draw_game_objects(screen, ball, paddle1, paddle2)

        # Only limit the framerate if not training the AI so it trains at full speed
        if not TRAINING_AI:
            clock.tick(FPS)


def eval_genomes(genomes, config):
    # Since Pong is a two player game, each genome will play against every other genome for each generation
    for i, (genome_id1, genome1) in enumerate(genomes):
        # This prevents an index out of bounds error (since the next loop starts from i + 1)
        if i == len(genomes) - 1:
            break

        genome1.fitness = 0
        # This inner loop will start from the next genome so the genomes don't play against themselves
        for genome_id2, genome2 in genomes[i + 1:]:
            # Only reset the fitness if it's not None (i.e. if it's the first time the genome is being evaluated)
            genome2.fitness = 0 if genome2.fitness == None else genome2.fitness
            game_loop(genome1, genome2, config)


def run_neat(config):
    # pop = neat.Checkpointer.restore_checkpoint('neat-checkpoint-1')
    pop = neat.Population(config)
    pop.add_reporter(neat.StdOutReporter(True))
    pop.add_reporter(neat.StatisticsReporter())
    # Save a checkpoint every generation
    pop.add_reporter(neat.Checkpointer(1))

    # Run for up to 50 generations and save the best model
    winner = pop.run(eval_genomes, 50)
    with open("best_model.pickle", "wb") as f:
        pickle.dump(winner, f)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')

    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    if TRAINING_AI:
        run_neat(config)
    else:
        game_loop(None, None, config)
