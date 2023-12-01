import pygame
import random
import neat
import pickle

WIN_WIDTH = 500
WIN_HEIGHT = 750

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load('imgs/bird1.png')),
             pygame.transform.scale2x(pygame.image.load('imgs/bird2.png')),
             pygame.transform.scale2x(pygame.image.load('imgs/bird3.png'))]

PIPE_IMG = pygame.transform.scale2x(pygame.image.load('imgs/pipe.png'))
GROUND_IMG = pygame.transform.scale2x(pygame.image.load('imgs/base.png'))
BG_IMG = pygame.transform.scale2x(pygame.image.load('imgs/bg.png'))
GEN = 0

pygame.init()
font = pygame.font.Font('Pixeltype.ttf', 50)


class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_RATE = 0.7

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_index = 0
        self.reverse_animate = False
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2

        if d >= 16:
            d = 16

        if d < 0:
            d -= 2

        self.y += d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION

        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        if self.reverse_animate:
            self.img_index -= self.ANIMATION_RATE
        else:
            self.img_index += self.ANIMATION_RATE

        if self.img_index >= 3:
            self.reverse_animate = True
            self.img_index = 2

        elif self.img_index <= 0:
            self.reverse_animate = False
            self.img_index = 0

        self.img = self.IMGS[int(self.img_index)]

        if self.tilt <= -80:
            self.img = self.IMGS[2]
            self.img_index = 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.passed = False  # Denotes whether the bird has passed the pipe or not
        self.top_pipe_pos = 0
        self.bottom_pipe_pos = 0

        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top_pipe_pos = self.height - self.PIPE_TOP.get_height()
        self.bottom_pipe_pos = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top_pipe_pos))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom_pipe_pos))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top_pipe_pos - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom_pipe_pos - round(bird.y))

        # Returns None if there is no collision between bird mask and top mask
        t_point = bird_mask.overlap(top_mask, top_offset)
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)

        if t_point or b_point:
            return True

        return False


class Ground:
    VEL = 5
    WIDTH = GROUND_IMG.get_width()
    IMG = GROUND_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # x1 and x2 represent 2 ground images. Once one of them gets off-screen we put that one behind the other one
        # Works kind of like Recycler View in order to create infinite ground

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, ground, score, gen):
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    score_text = font.render(f'Score: {score}', False, (255, 255, 255))
    gen_text = font.render(f'Gen: {gen}', False, (255, 255, 255))
    num_of_birds_text = font.render(f'Birds: {len(birds)}', False, (255, 255, 255))

    win.blit(score_text, (WIN_WIDTH - 10 - score_text.get_width(), 10))
    win.blit(gen_text, (10, 10))
    win.blit(num_of_birds_text, (10, 10 + gen_text.get_height()))

    pipe_index = 0
    if len(birds) > 0:
        if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_index = 1

    for bird in birds:
        bird.draw(win)

        pygame.draw.line(win, (255, 255, 255), (200 + bird.img.get_width(), bird.y),
                         (pipes[pipe_index].x, pipes[pipe_index].height), 3)
        pygame.draw.line(win, (255, 255, 255), (200 + bird.img.get_width(), bird.y),
                         (pipes[pipe_index].x, pipes[pipe_index].bottom_pipe_pos), 3)

    ground.draw(win)
    pygame.display.update()


def main(genomes, config):
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(200, 280))
        g.fitness = 0
        ge.append(g)

    pipes = [Pipe(600)]
    ground = Ground(680)
    score = 0
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption('Flappy Bird')
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_index = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_index = 1
        else:
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate(
                (bird.y, abs(bird.y - pipes[pipe_index].height), abs(bird.y - pipes[pipe_index].bottom_pipe_pos)))

            if output[0] > 0.5:
                bird.jump()

        rem = []
        add_pipe = False

        for pipe in pipes:
            for bird in list(birds):
                bird_index = birds.index(bird)
                if pipe.collide(bird):
                    ge[bird_index].fitness -= 1
                    nets.pop(bird_index)
                    ge.pop(bird_index)
                    birds.remove(bird)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for bird in list(birds):
            bird_index = birds.index(bird)
            if bird.y + bird.img.get_height() >= 680 or bird.y < 0:
                nets.pop(bird_index)
                ge.pop(bird_index)
                birds.remove(bird)

        if score > 30:
            break

        ground.move()
        draw_window(win, birds, pipes, ground, score, GEN)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())

    winner = p.run(main, 10)
    pickle.dump(winner,open('winner.p','wb'))


if __name__ == '__main__':
    config_path = 'config.txt'
    run(config_path)
