import os
import sys
import math
import random

import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('KunKhmer')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()
        
        self.movement = [False, False]
        self.death_count = 0
        self.lives = 5  # Initialize player lives
        self.heart_image = pygame.image.load('heart.png').convert_alpha()
        self.heart_image.set_colorkey((0, 0, 0))
        self.all_levels_completed = False


        
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'arc': load_image('arc.png'),
            'projectile': load_image('projectile.png'),
        }
        
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }
        
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)
        
        self.clouds = Clouds(self.assets['clouds'], count=16)
        
        self.player = Player(self, (50, 50), (8, 15))
        
        self.tilemap = Tilemap(self, tile_size=16)
        
        self.level = 0
        self.load_level(self.level)
        
        self.screenshake = 0

        
    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        self.dead = 0  
        self.transition = -3


        
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))
            
        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
        if self.level == len(os.listdir('data/maps')) - 1:
            self.all_levels_completed = True
            
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

    def draw_lives(self, surface):
        for i in range(self.lives):
            surface.blit(self.heart_image, (10 + i * 25, 5))
    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        
        self.sfx['ambience'].play(-1)

        button_image = pygame.image.load("button.png").convert_alpha()
        button_image.set_colorkey((0, 0, 0))
        button_image = pygame.transform.scale(button_image, (100, 65))
        back_to_menu_button = Button(button_image, 60, 440, "Menu", run_menu, self.screen)

        while True:

            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'], (0, 0))
            
            self.screenshake = max(0, self.screenshake - 1)
            
            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                    self.load_level(self.level)
                    
                if self.level == len(os.listdir('data/maps')) - 1:
                    self.level = 0
                else:
                    self.level += 1
                self.load_level(self.level)

            if self.transition < 0:
                self.transition += 1
            ############################################################################################################
            ############################################################################################################
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.death_count += 1  
                    if self.death_count >= 5:  
                        self.death_count = 0  
                        self.level = 0  
                        self.lives = 5  
                    else:
                        self.lives -= 1
                        if self.lives <= 0:
                            self.level = 0  
                            self.lives = 5  
                    self.load_level(self.level)
                    

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)
            
            self.tilemap.render(self.display, offset=render_scroll)
            
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
            
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)

            
            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                        
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
                    
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))

            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset)
            
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            ############################################################################################
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        self.player.jump()
                        if self.player.jump():
                            self.sfx['jump'].play()
                    if event.key == pygame.K_w:
                        self.player.jump()
                        if self.player.jump():
                            self.sfx['jump'].play() 
                    if event.key == pygame.K_f:
                        self.player.dash()
                    if event.key == pygame.K_KP_1:
                        self.player.dash()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_to_menu_button.rect.collidepoint(event.pos):
                        back_to_menu_button.action(screen)
                        mouse_pos = pygame.mouse.get_pos()
                        back_to_menu_button.check_for_input(mouse_pos)
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                
    
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
                

            
            self.display_2.blit(self.display, (0, 0))


            
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            back_to_menu_button.update(self.screen) 
            self.draw_lives(self.screen)
            pygame.display.update()
            back_to_menu_button.change_color(pygame.mouse.get_pos())
            pygame.display.update()
            self.clock.tick(60)



### Button class##########################################################################################
##########################################################################################################

class Button():
    
    def __init__(self, image, x_pos, y_pos, text_input, action, *args):
        self.image = image
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.text_input = text_input
        self.action = action
        self.args = args  
        self.font = pygame.font.SysFont("comicsansms", 30)
        self.text = self.font.render(self.text_input, True, (255, 255, 255))
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

    def check_for_input(self, position):
        if self.rect.collidepoint(position):

            self.action(*self.args)

    def update(self, screen):
        screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    def change_color(self, position):
        if self.rect.collidepoint(position):
            self.text = self.font.render(self.text_input, True, "green")
        else:
            self.text = self.font.render(self.text_input, True, "white")
    
    def render(self, screen):
        screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

def run_game(screen):
    game = Game()
    game.run()



def run_menu():
    run_game(screen)

def show_guidance_page(screen):
    
    screen.fill((0, 0, 0))
    

    font = pygame.font.SysFont("comicsansms", 40)
    title = font.render("Welcome to KunKhmer", True, (255, 255, 255))
    title_rect = title.get_rect(center=(320, 50))
    screen.blit(title, title_rect)

    def blit_text(font_name, font_size, text, color, center_pos):
        font = pygame.font.SysFont(font_name, font_size)
        rendered_text = font.render(text, True, color)
        text_rect = rendered_text.get_rect(center=center_pos)
        screen.blit(rendered_text, text_rect)

    white_color = (255, 255, 255)

    guidance_texts = [
        "",
        "Here are some tips to help you to know how to use keyboad to play the game",
        "",
        "use 'A' or 'Left' keyboad for go left.",
        "use 'D' or 'Right' keyboad for go right.",
        "use 'W' or 'Up' keyboad for jump up.",
        "use 'F' or '1 (in number pad)' keyboad for dash to kill enemy.",
        "",
        "",
        "Note: for jumping while sliding you need to keep pressing 'A' or 'Left'",
        " and press 'Up' or 'W' one time for jump to the right, and keep pressing 'D' ",
        "or 'Right' and press 'Up' or 'W' one time for jump to the left.",

]

    for i, guidance_text in enumerate(guidance_texts):
        blit_text("comicsansms", 17, guidance_text, white_color, (320, 100 + i*20))
    back_button = Button(pygame.Surface((200, 50)), 320, 450, "Back", run_menu, screen)
    back_button.update(screen)
    
    pygame.display.flip()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.rect.collidepoint(event.pos):
                    running = False

def show_guidance():
    show_guidance_page(screen)


def show_story_page(screen):
    screen.fill((0, 0, 0))
    

    font = pygame.font.SysFont("comicsansms", 40)
    title = font.render("Welcome to KunKhmer", True, (255, 255, 255))
    title_rect = title.get_rect(center=(320, 50))
    screen.blit(title, title_rect)
    


    def blit_text(font_name, font_size, text, color, center_pos):
        font = pygame.font.SysFont(font_name, font_size)
        rendered_text = font.render(text, True, color)
        text_rect = rendered_text.get_rect(center=center_pos)
        screen.blit(rendered_text, text_rect)

    white_color = (255, 255, 255)

    guidance_texts = [
        "",
        "",
        "Kun Khmer, also known as Pradal Serey, is a traditional Cambodian martial art",
        "renowned for its striking techniques and clinch fighting. Originating",
        "from the ancient martial art of Bokator, which dates back to the Khmer Empire,",
        "Kun Khmer was codified in the early 20th century during the French colonial period.",
        "The sport emphasizes powerful kicks generated from hip rotation, along with",
        "punches, elbows, and knee strikes. Fighters engage in intense battles, aiming for",
        "knockouts or technical knockouts to secure victory.",
        "",
        "The avatar in this game is inspired by a Kun Khmer fighter,",
        "which is why we decided to call our game ‘KunKhmer’."
]

    for i, guidance_text in enumerate(guidance_texts):
        blit_text("comicsansms", 15, guidance_text, white_color, (320, 100 + i*20))
        
    back_button = Button(pygame.Surface((200, 50)), 320, 450, "Back", run_menu, screen)
    back_button.update(screen)
    
    pygame.display.flip()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.rect.collidepoint(event.pos):
                    running = False
                    
                

def show_story():
    show_story_page(screen)



def exit_game():
    pygame.quit()
    sys.exit()


def run_menu(screen):
    pygame.mixer.music.load('data/music.wav')
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
    bg_image = pygame.image.load("background.png").convert()
    bg_image = pygame.transform.scale(bg_image, (640, 480))

    button_image = pygame.image.load("button.png").convert_alpha()
    button_image.set_colorkey((255, 255, 255))
    button_image = pygame.transform.scale(button_image, (250, 100))
    start_button = Button(button_image, 320, 180, "Play Game", run_game, screen)
    guidance_button = Button(button_image, 320, 260, "Guidance", show_guidance_page, screen)
    story_button = Button(button_image, 320, 340, "Story", show_story_page, screen)
    exit_button = Button(button_image, 320, 420, "Exit", exit_game)

    menu_running = True
    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                start_button.check_for_input(mouse_pos)
                guidance_button.check_for_input(mouse_pos)
                story_button.check_for_input(mouse_pos)
                exit_button.check_for_input(mouse_pos)

        screen.blit(bg_image, (0, 0))
        start_button.update(screen)
        start_button.change_color(pygame.mouse.get_pos())
        guidance_button.update(screen)
        guidance_button.change_color(pygame.mouse.get_pos())
        story_button.update(screen)
        story_button.change_color(pygame.mouse.get_pos())
        exit_button.update(screen)
        exit_button.change_color(pygame.mouse.get_pos())

        pygame.display.update()


pygame.init()
pygame.display.set_caption('KunKhmer')
screen = pygame.display.set_mode((640, 480))
run_menu(screen)

Game().run()