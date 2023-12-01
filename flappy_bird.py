import pygame
import random

WIN_WIDTH = 500
WIN_HEIGHT = 750

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load('imgs/bird1.png')),
             pygame.transform.scale2x(pygame.image.load('imgs/bird2.png')),
             pygame.transform.scale2x(pygame.image.load('imgs/bird3.png'))]

PIPE_IMG = pygame.transform.scale2x(pygame.image.load('imgs/pipe.png'))
GROUND_IMG = pygame.transform.scale2x(pygame.image.load('imgs/base.png'))
BG_IMG = pygame.transform.scale2x(pygame.image.load('imgs/bg.png'))

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
        self.isAlive = True

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


def draw_window(win, bird, pipes, ground, score):
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    score_text = font.render(f'Score: {score}', False, (255, 255, 255))
    win.blit(score_text, (WIN_WIDTH - 10 - score_text.get_width(), 10))

    bird.draw(win)
    ground.draw(win)
    pygame.display.update()


def game_over_screen(win, score):
    win.fill((0, 0, 0))

    game_over_text = font.render('Game Over !', False, (255, 255, 255))
    score_text = font.render(f'Score: {score}', False, (255, 255, 255))
    restart_text = font.render(f'Press Space to Restart !',False,(255,255,255))

    win.blit(game_over_text, (WIN_WIDTH / 2 - game_over_text.get_width() / 2, WIN_HEIGHT / 2 - 50))
    win.blit(score_text, (WIN_WIDTH / 2 - score_text.get_width() / 2, WIN_HEIGHT / 2))
    win.blit(restart_text, (WIN_WIDTH / 2 - restart_text.get_width() / 2, WIN_HEIGHT / 2 + 50))

    pygame.display.update()


def main():
    bird = Bird(200, 280)
    pipes = [Pipe(600)]
    ground = Ground(680)
    score = 0
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption('Flappy Bird')
    clock = pygame.time.Clock()
    game_active = True

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

            if game_active:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and bird.isAlive:
                        bird.jump()
            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_active = True
                    # main()
                    score = 0

        if game_active:
            bird.move()

            rem = []
            add_pipe = False

            for pipe in pipes:
                if pipe.collide(bird):
                    bird.isAlive = False
                    game_active = False

                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem.append(pipe)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

                pipe.move()

            if add_pipe and bird.isAlive:
                score += 1
                pipes.append(Pipe(600))

            for r in rem:
                pipes.remove(r)

            if bird.y + bird.img.get_height() >= 680:
                bird.isAlive = False
                game_active = False
                bird.y = 680 - bird.img.get_height()

            ground.move()
            draw_window(win, bird, pipes, ground, score)

        else:
            game_over_screen(win, score)
            bird = Bird(200, 280)
            pipes = [Pipe(600)]
            ground = Ground(680)


if __name__ == '__main__':
    main()
