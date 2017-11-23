#Robo Breakout
#by Robert Leslie

import pygame
from pygame.locals import *
from random import randint

#global variables
WIN_WIDTH = 1000
WIN_HEIGHT = 750
HALF_WIDTH = int(WIN_WIDTH / 2)
HALF_HEIGHT = int(WIN_HEIGHT / 2)
LIVES = 3
KEEP_PLAYING = True


#camera class to track the movements of the player
#it only displays a small amount of the total level while keeping the player
#as the main focus
#camera was recieved from user sloth at
#https://stackoverflow.com/questions/14354171/add-scrolling-to-a-platformer-in-pygame
class Camera(object):
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.rect = Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.rect.topleft)

    def update(self, target):
        self.rect = self.camera_func(self.rect, target.rect)

#complex camera to make sure we dont see outside the bounds of our generated world
#the camera determines where to place the camera object so that the player is in focus
def complex_camera(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    l, t, _, _ = -l+HALF_WIDTH, -t+HALF_HEIGHT, w, h

    l = min(0, l)
    l = max(-(camera.width-WIN_WIDTH), l)
    t = max(-(camera.height-WIN_HEIGHT), t)
    t = min(0, t)
    return Rect(l, t, w, h)

#Parent class for all objects that need to be displayed as sprites
class Entity(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

#background class that creates an object to display the background
class Background(Entity):
    def __init__(self, imagefile, location):
        Entity.__init__(self)
        self.image = pygame.image.load(imagefile)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location

#loads image for platforms and postions rect for displaying on the screen
#has a smaller rect for proper collision with player
class Platform(Entity):
    def __init__(self, imagefile, location):
        Entity.__init__(self)
        self.image = pygame.image.load(imagefile)
        self.rect = Rect(location[0], location[1], 128, 30)

#class that loads images for decoration and postions rect for displaying
#sets the rect.top so they align with the platforms image
class Decoration(Entity):
    def __init__(self, imagefile, location):
        Entity.__init__(self)
        self.image = pygame.image.load(imagefile)
        self.rect = Rect(0, 0, 49, 43)
        self.rect.left = location[0]
        self.rect.top = location[1] + (128-self.image.get_height())

#class that loads images for collectibles and positions rect for displaying
#sets rect.top so they align with the platforms image
class Collectible(Entity):
    def __init__(self, imagefile, location):
        Entity.__init__(self)
        self.image = pygame.image.load(imagefile)
        self.rect = Rect(0, 0, 30, 30)
        self.rect.left = location[0]
        self.rect.top = location[1] + (128-self.image.get_height())

#class for displaying and exit door at given location
#enables player to complete the level
class Exit_door(Entity):
    def __init__(self, location):
        Entity.__init__(self)
        self.image = pygame.Surface((74, 128))
        self.image.fill((255, 255, 55))
        self.image.convert()
        self.rect = Rect(location[0], location[1], 90, 150)

#class that loads images for bullets, and sets their position to the users position
#uses original_pos to determine how far the bullet can travel
#uses users heading to determine which direction to fire
class Bullet(Entity):
    def __init__(self, imagefile, mob, bullet_type):
        Entity.__init__(self)
        self.image = pygame.image.load(imagefile)
        self.rect = self.image.get_rect()
        self.heading = mob.heading
        if self.heading == "left":
            self.rect.right = mob.rect.left
        else:
            self.rect.left = mob.rect.right
        self.bullet_type = bullet_type
        self.rect.top =  mob.rect.top + 64
        self.original_pos = self.rect.left

    #bullets update function moves the bullet and checks if it needs to be deleted
    def update(self, platforms, entities, bullets, world_width):
        if self.heading == "left":
            self.rect.right -= 16
        else:
            self.rect.left += 16
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                entities.remove(self)
                bullets.remove(self)
        if self.bullet_type == 'Y':
            if self.rect.left > self.original_pos+300 or self.rect.left < self.original_pos-300:
                entities.remove(self)
                bullets.remove(self)
        else:
            if self.rect.left > self.original_pos+600 or self.rect.left < self.original_pos-600:
                entities.remove(self)
                bullets.remove(self)

#creates a bullet object from the user
def shoot(entities, mob, color):
    bullet = Bullet("src/Object/{0}.png".format(color), mob, color)
    entities.add(bullet)
    return bullet
            
#class to generate and display Text in game
class Textbox(Entity):
    def __init__(self, message, entity):
        Entity.__init__(self)
        self.font = pygame.font.SysFont('Times New Roman', 30)
        self.image = self.font.render(message, True, (255, 140, 0))
        self.rect = Rect(entity.rect.right, entity.rect.top, self.image.get_width(), self.image.get_height())

#class to display the health of the player
class Health(Entity):
    def __init__(self, p, camera):
        Entity.__init__(self)
        self.font = pygame.font.SysFont('Times New Roman', 30)
        self.image = self.font.render("Health: {0}     Lives: {1}".format(p.health, LIVES), True, (255, 0, 0))
        self.rect = Rect(-camera.rect.left, -camera.rect.top, self.image.get_width(), self.image.get_height())

    #updates the displayed health of the player
    def update(self, p, camera):
        message = "Health: {0}     Lives: {1}".format(p.health, LIVES)
        if p.invincible:
            message += "     Cheating: Invincible"
        if p.burning:
            message += "     Status: Burning"
        if p.stunned:
            message += "     Status: Stunned"
        self.image = self.font.render(message, True, (255, 0, 0))
        self.rect = Rect(-camera.rect.left, -camera.rect.top, self.image.get_width(), self.image.get_height())

#class for displaying enemy's health bars above their heads
#changes color depending on amount of health lost
class Enemy_health(Entity):
    def __init__(self, enemy):
        Entity.__init__(self)
        color = (0, 255, 0)
        self.image = pygame.Surface((enemy.health, 25))
        self.image.convert()
        self.image.fill(color)
        self.rect = Rect(enemy.rect.left-10, enemy.rect.top-50, enemy.health, 25)
        
    def update(self, enemy):
        if enemy.health > 75:
            color = (0, 255, 0)
        elif enemy.health > 50:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)
        self.image = pygame.Surface((enemy.health, 25))
        self.image.convert()
        self.image.fill(color)
        self.rect = Rect(enemy.rect.left-10, enemy.rect.top-50, enemy.health, 25)

#parent class to all enemy's, retains their data fields and handles collisions        
class Enemy(Entity):
    def __init__(self, imagefile, location):
        Entity.__init__(self)
        self.image = pygame.image.load(imagefile)
        self.rect = self.image.get_rect()
        self.rect.left = location[0] + randint(-10, 10)
        self.rect.top = location[1]
        self.defense_rect = Rect(self.rect.left-200, self.rect.top-200, 528, 528)
        self.heading = 'right'
        self.health = 100
        self.original_pos = self.rect.left
        self.shot_timer = 0
        self.health_display = Enemy_health(self)
        self.health_added = False

    def collision(self, entities, bullets, enemies):
        for b in bullets:
            if b.bullet_type == 'Y':
                if pygame.sprite.collide_rect(self, b):
                    self.health -= 50
                    entities.remove(b)
                    bullets.remove(b)
        if self.health == 0:
            entities.remove(self)
            enemies.remove(self)

#fire type enemy, child of enemy, provides update method
#handles movement, shooting, and checking for collision or health changes
#main difference is bullet type shot from water enemy, adding unique damage type
class Fire_enemy(Enemy):
    def update(self, player, entities, bullets, enemies):
        if self.heading == 'left':
            self.rect.left -= 4
        else:
            self.rect.left += 4
        if self.rect.left > self.original_pos+120:
            self.heading = 'left'
        if self.rect.left < self.original_pos-120:
            self.heading = 'right'
        if self.defense_rect.colliderect(player.rect):
            if self.shot_timer <= 0:
                self.shot_timer = 15
                bullets.append(shoot(entities, self, 'R'))
        self.shot_timer -= 1
        self.collision(entities, bullets, enemies)
        if not self.health_added:
            entities.add(self.health_display, layer = 1)
            self.health_added = True
        self.health_display.update(self)

#water type enemy, child of enemy, provides update method
#handles movement, shooting, and checking for collision or health changes
#main difference is bullet type shot from fire enemy, adding unique damage type
class Water_enemy(Enemy):
    def update(self, player, entities, bullets, enemies):
        if self.heading == 'left':
            self.rect.left -= 4
        else:
            self.rect.left += 4
        if self.rect.left > self.original_pos+120:
            self.heading = 'left'
        if self.rect.left < self.original_pos-120:
            self.heading = 'right'
        if self.defense_rect.colliderect(player.rect):
            if self.shot_timer <= 0:
                self.shot_timer = 30
                bullets.append(shoot(entities, self, 'O'))
        self.shot_timer -= 1
        self.collision(entities, bullets, enemies)
        if not self.health_added:
            entities.add(self.health_display, layer = 1)
            self.health_added = True
        self.health_display.update(self)

#class to generate the player and contain their data fields
class Player(Entity):
    def __init__(self, imagefile, location):
        Entity.__init__(self)
        self.x_velocity = 0
        self.y_velocity = 0
        self.grounded = False
        self.image = pygame.image.load(imagefile)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location
        self.collected = False
        self.mushrooms = 0
        self.health = 75
        self.heading = "right"
        self.burning = False
        self.burn_timer = 0
        self.stunned = False
        self.stun_timer = 0
        self.invincible = False
        self.door_pos = (400, 500)

    #update to move the player and check if any collisions have occurred
    def update(self, up, down, left, right, running, platforms, collectibles, entities, bullets):
        if up:
            if self.grounded: self.y_velocity -= 20
        if down:
            pass
        if left:
            self.x_velocity = -8
            self.heading = "left"
            if running:
                self.x_velocity -= 8
        if right:
            self.x_velocity = 8
            self.heading = "right"
            if running:
                self.x_velocity += 8
        if not (left or right):
            self.x_velocity = 0
        #if on fire from enemy, add additional damage
        if self.burning:
            if (self.burn_timer % 50) == 0:
                self.health -= 5
            self.burn_timer -= 1
            if self.burn_timer == 0:
                self.burning = False
        #if stunned from enemy, stop movement
        if self.stunned:
            self.x_velocity = 0
            if up:
                self.y_velocity = 0
            self.stun_timer -= 1
            if self.stun_timer == 0:
                self.stunned = False
        if not self.grounded:
            self.y_velocity += 0.8
            if self.y_velocity > 100: self.y_velocity = 100
        self.rect.left += self.x_velocity
        death, message = self.collision(self.x_velocity, 0, platforms, collectibles, entities, bullets)
        #determine if player has died or won already
        if message == "Win" or message == "Lose":
            return death, message
        self.rect.top += self.y_velocity
        self.grounded = False
        death, message = self.collision(0, self.y_velocity, platforms, collectibles, entities, bullets)
        return death, message

    #handles any collisions if they have occurred
    #also collects any collectibles collided with
    def collision(self, x_velocity, y_velocity, platforms, collectibles, entities, bullets):
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                if x_velocity > 0:
                    self.rect.right = p.rect.left
                if x_velocity < 0:
                    self.rect.left = p.rect.right
                if y_velocity > 0:
                    self.rect.bottom = p.rect.top
                    self.grounded = True
                    self.y_velocity = 0
                if y_velocity < 0:
                    self.rect.top = p.rect.bottom
        for c in collectibles:
            if pygame.sprite.collide_rect(self, c):
                self.collected = True
                self.mushrooms += 1
                if self.collected == True and self.mushrooms == 1:
                    entities.add(Textbox(
                        "Collected mushrooms act as biofuel, increasing health!", self), layer = 0)  
                if self.health > 75:
                    self.health = 100
                else:
                    self.health += 25
                entities.remove(c)
                collectibles.remove(c)
        #damage player if not invincible
        if not self.invincible:
            for b in bullets:
                if pygame.sprite.collide_rect(self, b):
                    if b.bullet_type == 'R':                  
                        self.health -= 10
                        if randint(0, 10) > 7:
                            self.burning = True
                            self.burn_timer = 100
                        entities.remove(b)
                        bullets.remove(b)
                    if b.bullet_type == 'O':
                        self.health -= 20
                        if randint(0, 10) > 5:
                            self.stunned = True
                            self.stun_timer = 50
                        entities.remove(b)
                        bullets.remove(b)
        #determine if player has won or died
        if self.health <= 0:
            return True, "Lose"
        if self.rect.collidepoint(self.door_pos):
            return True, "Win"
        return False, "Quit"
                
#function to generate the world of any level given
#adds all platforms, decorations, enemies, and collectibles to their lists
#determines the proper location values by a 128x128 grid
def world_generator(world, platforms, collectibles, enemies, entities, folder, player):
    x = y = 0
    for row in world:
        for col in row:
            if col.isdigit():
                p = Platform("src/{0}/{1}.png".format(folder, col), (x, y))
                platforms.append(p)
                entities.add(p, layer = 0)
            elif col.islower():
                if col == 'r':
                    p = Fire_enemy("src/Robots/Red_enemy.png", (x, y))
                    enemies.append(p)
                    entities.add(p, layer = 1)
                elif col == 'b':
                    p = Water_enemy("src/Robots/Blue_enemy.png", (x, y))
                    enemies.append(p)
                    entities.add(p, layer = 1)
                elif col == 'z':
                    p = Exit_door((x, y))
                    player.door_pos = (x+90, y)
                    entities.add(p, layer = 0)
                elif col == 'x':
                    p = Platform("src/{0}/{1}.png".format(folder, col), (x, y-29))
                    entities.add(p, layer = 2)
                else:
                    p = Platform("src/{0}/{1}.png".format(folder, col), (x, y))
                    entities.add(p, layer = 0)
            elif col.isupper():
                if col == 'M' or col == 'N':
                    p = Collectible("src/{0}/{1}.png".format(folder, col), (x, y))
                    collectibles.append(p)
                else:
                    p = Decoration("src/{0}/{1}.png".format(folder, col), (x, y))
                entities.add(p, layer = 0)
            x += 128
        y += 128
        x = 0

#starts the game by displaying start menu
#checks if there are still lives to restart levels
#displays end screen if necessary
def main():
    pygame.init()
    global screen, KEEP_PLAYING, LIVES
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), 0, 32)
    pygame.display.set_caption("Robo Breakout")
    while KEEP_PLAYING:
        KEEP_PLAYING = False
        LIVES = 3
        message = "Quit"
        start()
        while LIVES > 0:
            message = level()
        if message != "Quit":
            end(message)

#function to create a start menu, it displays the name of the game
#and two buttons for starting the game or opening help menu
def start():
    global LIVES, screen
    clock = pygame.time.Clock()
    
    started = False
    font = pygame.font.SysFont('Times New Roman', 30)
    start_game_image = font.render("Start Game", True, (255, 140, 0))
    start_game_rect = Rect(HALF_WIDTH-65, HALF_HEIGHT+10, start_game_image.get_width(), start_game_image.get_height())
    start_game_button = Rect(HALF_WIDTH-100, HALF_HEIGHT, 200, 50)
    start_game_color = (255, 255, 255)
    how_to_image = font.render("How to Play", True, (255, 140, 0))
    how_to_rect = Rect(HALF_WIDTH-70, HALF_HEIGHT+110, how_to_image.get_width(), how_to_image.get_height())
    how_to_button = Rect(HALF_WIDTH-100, HALF_HEIGHT+100, 200, 50)
    how_to_color = (255, 255, 255)
    font = pygame.font.SysFont('Times New Roman', 100)
    title_image = font.render("Robo Breakout", True, (255, 140, 0))
    title_rect = Rect(205, 175, title_image.get_width(), title_image.get_height())
    pos = (0, 0)
    while not started:
        clock.tick(60)
        screen.fill((64, 224, 208))
        if how_to_button.collidepoint(pygame.mouse.get_pos()):
            how_to_color = (211, 211, 211)
        else:
            how_to_color = (255, 255, 255)
        if start_game_button.collidepoint(pygame.mouse.get_pos()):
            start_game_color = (211, 211, 211)
        else:
            start_game_color = (255, 255, 255)
        pygame.draw.rect(screen, (255, 255, 255), (205, 185, 610, 93))
        pygame.draw.rect(screen, start_game_color, start_game_button) 
        pygame.draw.rect(screen, how_to_color, how_to_button)
        
        screen.blit(start_game_image, start_game_rect)
        screen.blit(title_image, title_rect)
        screen.blit(how_to_image, how_to_rect)
        for event in pygame.event.get():
            if event.type == QUIT:
                LIVES = 0
                return
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    LIVES = 0
                    return
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                if start_game_button.collidepoint(pos):
                    started = True
                if how_to_button.collidepoint(pos):
                    help_menu()
                    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), 0, 32)
        pygame.display.update()

#handles all of the game logic for levels
#would just need to pass world, and decoration arrays to make more levels
def level():
    #local variables
    global LIVES, screen
    clock = pygame.time.Clock()
    background = Background('src/BG/BG.png', (0,0))
    entities = pygame.sprite.LayeredUpdates()
    platforms = []
    collectibles = []
    bullets = []
    enemies = []
    player = Player("src/Robots/Idle1.png", (300, 650))
    up = down = left = right = running = False

    #map for the current world
    world = [
        "                                                     ",
        "                     123                123 r        ",
        "        456          kil  456      456  efj823       ",
        "     b                         r        effffj83     ",
        "   4556          b           1223       kiiiiiil     ",
        "                123        17hffg                    ",
        "        123     efg   456  kiiiil        46    b    z",
        "ww8223  efg    12223               123        127ww83",
        "xx                                               xx  ",]
    #map for the current world's decorations and collectibles
    decorations = [
        "                     DMD                AA              ",
        "        B S                T        U      VU        ",
        "                                              P       ",
        "   MAAP                       BE                     ",
        "                 V                                   ",
        "                       EC                              ",
        "  PVUB          DCD                           AV     ",
        "                                                     ",]

    #generate world, determine world size, and configure camera
    world_generator(world, platforms, collectibles, enemies, entities, "Tiles", player)
    world_generator(decorations, platforms, collectibles, enemies, entities, "Object", player)
        
    world_width = len(world[0])*128
    world_height = (len(world)-1)*128
    camera = Camera(complex_camera, world_width, world_height)
    health = Health(player, camera)
    entities.add(player, layer = 1)
    entities.add(health, layer = 1)
    #for displaying tooltip in upper right corner
    font = pygame.font.SysFont('Times New Roman', 30)
    tooltip_image = font.render("?", True, (255, 140, 0))
    tooltip_rect = Rect(985, 0, 32, 32)
    #set for how long until player can fire again
    shot_timer = 0
    while 1:
        clock.tick(60)
        screen.fill((255, 255, 255))
        screen.blit(background.image, background.rect)
        screen.blit(tooltip_image, tooltip_rect)
        keys = pygame.key.get_pressed()
        #shoot if player can
        if keys[K_SPACE]:
            if shot_timer <= 0:
                shot_timer = 15
                bullets.append(shoot(entities, player, 'Y'))
        #handle movement, quitting, invincibility, or help menu displayal
        for event in pygame.event.get():
            if event.type == QUIT:
                LIVES = 0
                return "Quit"
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                if tooltip_rect.collidepoint(pos):
                    help_menu()
                    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), 0, 32)
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    LIVES = 0
                    return "Quit"
                if event.key == K_UP or event.key == K_w:
                    up = True
                if event.key == K_DOWN or event.key == K_s:
                    down = True
                if event.key == K_LEFT or event.key == K_a:
                    left = True
                if event.key == K_RIGHT or event.key == K_d:
                    right = True
                if event.key == K_i:
                    player.invincible = not player.invincible
                #if event.key == K_SHIFT:
                #    running = True
            if event.type == KEYUP:
                if event.key == K_UP or event.key == K_w:
                    up = False
                if event.key == K_DOWN or event.key == K_s:
                    down = False
                if event.key == K_LEFT or event.key == K_a:
                    left = False
                if event.key == K_RIGHT or event.key == K_d:
                    right = False
        #update objects on screen
        camera.update(player)
        death, message = player.update(up, down, left, right, running, platforms, collectibles, entities, bullets)
        health.update(player, camera)
        for b in bullets:
            b.update(platforms, entities, bullets, world_width)
        for e in enemies:
            e.update(player, entities, bullets, enemies)
        #check if player has fallen out of the world or died, reset if so
        #or if player wins then end game
        if player.rect.top > world_height+50 or death:
            if message == "Win":
                LIVES = 0
            else:
                LIVES -= 1
                message = "Lose"
            return message
        #reset camera
        for e in entities:
            screen.blit(e.image, camera.apply(e))
        #pygame.draw.rect(screen, (60, 60, 100), platforms[0].rect, 0)
        pygame.display.update()
        shot_timer -= 1

#function for displaying the end message
#give option to restart
def end(message):
    global KEEP_PLAYING
    screen.fill((64, 224, 208))
    font = pygame.font.SysFont('Times New Roman', 200)
    final_image = font.render("You %s" % message, True, (255, 140, 0))
    final_rect = Rect(115, 175, final_image.get_width(), final_image.get_height())
    font = pygame.font.SysFont('Times New Roman', 30)
    restart_image = font.render("Restart", True, (255, 140, 0))
    restart_rect = Rect(HALF_WIDTH-65, 480, restart_image.get_width(), restart_image.get_height())
    restart_button = Rect(HALF_WIDTH-125, 475, 200, 50)
    restart_color = (255, 255, 255)
    while 1:
        if restart_button.collidepoint(pygame.mouse.get_pos()):
            restart_color = (211, 211, 211)
        else:
            restart_color = (255, 255, 255)
        pygame.draw.rect(screen, restart_color, restart_button)

        screen.blit(final_image, final_rect)
        screen.blit(restart_image, restart_rect)
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                if restart_button.collidepoint(pos):
                    KEEP_PLAYING = True
                    return
        pygame.display.update()

#function for displaying the help menu
def help_menu():
    screen2 = pygame.display.set_mode((WIN_WIDTH+200, WIN_HEIGHT), 0, 32)
    image = pygame.image.load("src/help.jpg")
    rect = Rect(0, 0, 1200, 750)
    up = False
    down = True
    clock = pygame.time.Clock()
    while 1:
        clock.tick(30)
        screen2.blit(image, rect)
        #handle scrolling of image or quitting
        keys = pygame.key.get_pressed()
        if keys[K_DOWN]:
            screen.scroll(0, 20)
            rect.top -= 20
        if keys[K_UP]:
            screen.scroll(0, -20)
            rect.top += 20
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return
            if event.type == MOUSEBUTTONDOWN:
                if up:
                    rect.top += 100
                if down:
                    rect.top -= 100
        if rect.bottom <= 0:
            up = True
            down = False
        if rect.top >= WIN_HEIGHT:
            up = False
            down = True
        pygame.display.update()
        
#start and end game
if __name__ == '__main__':
    try:
        main()
    finally:
        pygame.quit()
