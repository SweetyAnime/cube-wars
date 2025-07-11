import pygame
import time
import random
import math


pygame.init()

# Constants
WIDTH, HEIGHT = 1200, 700  # Increased size for UI panel
TILE_SIZE = 40
GAME_AREA_WIDTH = 960  # Game area width remains the same
FPS = 60  # Frames per second for the game
GAME_COLS = GAME_AREA_WIDTH // TILE_SIZE
GAME_ROWS = HEIGHT // TILE_SIZE
UI_PANEL_WIDTH = WIDTH - GAME_AREA_WIDTH  # UI panel on the right
# Define ROWS and COLS here to be available throughout the code
ROWS = GAME_ROWS
COLS = GAME_COLS

# Colors
RED = (200, 50, 50)
BLUE = (50, 100, 200)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
BLACK = (0, 0, 0)

# Set up display
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cube Wars")
font = pygame.font.SysFont("arial", 18)

clock = pygame.time.Clock()

# Game State
player_coins = 50
ai_coins = 50
buildings = []
units = []
bullets = []
start_time = time.time()

# Score and timer
player_score = 0
ai_score = 0
GAME_TIME = 300  # 5 minutes

# Building costs and healths
BUILD_COSTS = {
    "windmill": 65,
    "tank": 30,
    "soldier": 25,
    "drone": 40,
    "spider": 50,
    "defense": 30,
}

BUILD_HEALTH = {
    "castle": 200,
    "windmill": 80,
    "tank": 100,
    "soldier": 60,
    "drone": 50,
    "spider": 70,
    "defense": 120,
}

UNIT_SPEEDS = {
    "tank": 0.05,
    "soldier": 0.1,
    "drone": 0.15,
    "spider": 0.2,
}

UNIT_RANGES = {
    "tank": 2,
    "soldier": 1,
    "drone": 3,
    "spider": 2,
}

UNIT_HEALTH = {
    "tank": 60,
    "soldier": 30,
    "drone": 20,
    "spider": 40
}

UNIT_DAMAGE = 10
CASTLE_DAMAGE = 15
BULLET_SPEED = 3

occupied_tiles = set()

class Building:
    def __init__(self, x, y, b_type, owner):
        self.x = x
        self.y = y
        self.type = b_type
        self.owner = owner
        self.last_spawn = time.time()
        self.last_coin = time.time()
        self.health = BUILD_HEALTH.get(b_type, 100)
        self.fire_timer = time.time()
        if b_type in UNIT_SPEEDS:
            units.append(Unit(self.x, self.y, self.type, self.owner))
            occupied_tiles.add((self.x, self.y))

    def draw(self):
        pygame.draw.rect(win, BLUE if self.owner == "player" else RED, (self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        label = font.render(self.type[:3].upper(), True, WHITE)
        win.blit(label, (self.x * TILE_SIZE + 3, self.y * TILE_SIZE + 10))
        bar_width = TILE_SIZE
        bar_height = 4
        bar_x = self.x * TILE_SIZE
        bar_y = self.y * TILE_SIZE - 5
        health_ratio = max(0, self.health / BUILD_HEALTH.get(self.type, 100))
        pygame.draw.rect(win, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(win, GREEN, (bar_x, bar_y, bar_width * health_ratio, bar_height))

    def shoot(self):
        if self.type == "castle":
            now = time.time()
            if now - self.fire_timer >= 2:
                targets = [u for u in units if u.owner != self.owner and abs(u.grid_x - self.x) + abs(u.grid_y - self.y) <= 3]
                if targets:
                    target = min(targets, key=lambda u: abs(u.grid_x - self.x) + abs(u.grid_y - self.y))
                    bullets.append(Bullet(self.x, self.y, target, self.owner, CASTLE_DAMAGE))
                    self.fire_timer = now
        elif self.type == "defense":
            now = time.time()
            if now - self.fire_timer >= 2:
                # Defense building attacks enemy units in range 5
                targets = [u for u in units if u.owner != self.owner and abs(u.grid_x - self.x) + abs(u.grid_y - self.y) <= 5]
                if targets:
                    target = min(targets, key=lambda u: abs(u.grid_x - self.x) + abs(u.grid_y - self.y))
                    bullets.append(Bullet(self.x, self.y, target, self.owner, CASTLE_DAMAGE))
                    self.fire_timer = now

class Unit:
    def __init__(self, x, y, u_type, owner):
        self.grid_x = x
        self.grid_y = y
        self.u_type = u_type
        self.owner = owner
        self.speed = UNIT_SPEEDS.get(u_type, 0.05)
        self.range = UNIT_RANGES.get(u_type, 1)
        self.health = UNIT_HEALTH.get(u_type, 20)
        self.timer = 0
        self.fire_timer = time.time()
        occupied_tiles.add((self.grid_x, self.grid_y))

    def move(self):
        self.timer += self.speed / 10
        if self.timer >= 1:
            self.timer = 0
            targets = [b for b in buildings if b.owner != self.owner and b.type == "castle"]
            if not targets:
                return
            target = targets[0]
            dx = target.x - self.grid_x
            dy = target.y - self.grid_y

            if abs(dx) + abs(dy) <= 1:
                return

            directions = [
                (1 if dx > 0 else -1 if dx < 0 else 0, 0),
                (0, 1 if dy > 0 else -1 if dy < 0 else 0),
                (1 if dx > 0 else -1 if dx < 0 else 0, 1 if dy > 0 else -1 if dy < 0 else 0)
            ]
            random.shuffle(directions)
            for dir_x, dir_y in directions:
                next_x = self.grid_x + dir_x
                next_y = self.grid_y + dir_y
                if (next_x, next_y) not in occupied_tiles and 0 <= next_x < COLS and 0 <= next_y < ROWS:
                    occupied_tiles.discard((self.grid_x, self.grid_y))
                    self.grid_x = next_x
                    self.grid_y = next_y
                    occupied_tiles.add((self.grid_x, self.grid_y))
                    break

    def shoot(self):
        now = time.time()
        if now - self.fire_timer >= 2:
            # Units target enemy units first, then non-castle buildings, then castle
            # 1. Enemy units in range
            targets = [u for u in units if u.owner != self.owner and abs(u.grid_x - self.grid_x) + abs(u.grid_y - self.grid_y) <= self.range]
            if targets:
                def get_target_pos(t):
                    return t.grid_x, t.grid_y
                target = min(targets, key=lambda t: abs(t.grid_x - self.grid_x) + abs(t.grid_y - self.grid_y))
                bullets.append(Bullet(self.grid_x, self.grid_y, target, self.owner, UNIT_DAMAGE))
                self.fire_timer = now
                return
            # 2. Enemy non-castle buildings in range
            targets = [b for b in buildings if b.owner != self.owner and b.type != "castle" and abs(b.x - self.grid_x) + abs(b.y - self.grid_y) <= self.range]
            if targets:
                def get_target_pos(t):
                    return t.x, t.y
                target = min(targets, key=lambda t: abs(t.x - self.grid_x) + abs(t.y - self.grid_y))
                bullets.append(Bullet(self.grid_x, self.grid_y, target, self.owner, UNIT_DAMAGE))
                self.fire_timer = now
                return
            # 3. Enemy castle in range
            targets = [b for b in buildings if b.owner != self.owner and b.type == "castle" and abs(b.x - self.grid_x) + abs(b.y - self.grid_y) <= self.range]
            if targets:
                def get_target_pos(t):
                    return t.x, t.y
                target = min(targets, key=lambda t: abs(t.x - self.grid_x) + abs(t.y - self.grid_y))
                bullets.append(Bullet(self.grid_x, self.grid_y, target, self.owner, UNIT_DAMAGE))
                self.fire_timer = now

    def draw(self):
        color = ORANGE if self.u_type == "tank" else YELLOW if self.u_type == "soldier" else PURPLE if self.u_type == "drone" else WHITE
        px = self.grid_x * TILE_SIZE + TILE_SIZE // 2
        py = self.grid_y * TILE_SIZE + TILE_SIZE // 2
        if self.owner == "ai":
            # Draw AI units as triangles
            points = [
                (px, py - 8),
                (px - 7, py + 7),
                (px + 7, py + 7)
            ]
            pygame.draw.polygon(win, color, points)
        else:
            # Draw player units as circles
            pygame.draw.circle(win, color, (px, py), 6)
        health_ratio = max(0, self.health / UNIT_HEALTH.get(self.u_type, 20))
        pygame.draw.rect(win, RED, (px - 10, py - 15, 20, 4))
        pygame.draw.rect(win, GREEN, (px - 10, py - 15, 20 * health_ratio, 4))

class Bullet:
    def __init__(self, x, y, target, owner, damage):
        self.x = x * TILE_SIZE + TILE_SIZE // 2
        self.y = y * TILE_SIZE + TILE_SIZE // 2
        self.target = target
        self.owner = owner
        self.damage = damage

    def update(self):
        dx = self.target.x * TILE_SIZE + TILE_SIZE // 2 - self.x if isinstance(self.target, Building) else self.target.grid_x * TILE_SIZE + TILE_SIZE // 2 - self.x
        dy = self.target.y * TILE_SIZE + TILE_SIZE // 2 - self.y if isinstance(self.target, Building) else self.target.grid_y * TILE_SIZE + TILE_SIZE // 2 - self.y
        dist = math.hypot(dx, dy)
        if dist < 5:
            global player_score, ai_score
            if isinstance(self.target, Building):
                self.target.health -= self.damage
                if self.target.health <= 0:
                    if self.target in buildings:
                        # Score for destroying building
                        score_val = BUILD_COSTS.get(self.target.type, 10)
                        if self.owner == "player":
                            player_score += score_val
                        else:
                            ai_score += score_val
                        # If castle destroyed, end game
                        if self.target.type == "castle":
                            show_winner(self.owner)
                        buildings.remove(self.target)
                        occupied_tiles.discard((self.target.x, self.target.y))
            else:
                self.target.health -= self.damage
                if self.target.health <= 0:
                    occupied_tiles.discard((self.target.grid_x, self.target.grid_y))
                    if self.target in units:
                        # Score for killing unit
                        score_val = BUILD_COSTS.get(self.target.u_type, 5)
                        if self.owner == "player":
                            player_score += score_val
                        else:
                            ai_score += score_val
                        units.remove(self.target)
            return True
        else:
            self.x += BULLET_SPEED * dx / dist
            self.y += BULLET_SPEED * dy / dist
        return False

    def draw(self):
        try:
            pygame.draw.circle(win, BLACK, (int(self.x), int(self.y)), 3)
        except Exception:
            pass

# Setup initial castles
buildings.append(Building(2, ROWS - 2, "castle", "player"))
buildings.append(Building(COLS - 3, 1, "castle", "ai"))

def draw_grid():
    for y in range(ROWS):
        for x in range(COLS):
            color = BLUE if y >= ROWS // 2 else RED
            pygame.draw.rect(win, color, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(win, GRAY, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)
    # Draw UI panel background
    pygame.draw.rect(win, (30, 30, 30), (GAME_AREA_WIDTH, 0, UI_PANEL_WIDTH, HEIGHT))

def draw_game(selected_building):
    win.fill(GRAY)
    draw_grid()
    for b in buildings:
        b.draw()
    for u in units:
        u.draw()
    for bullet in bullets:
        bullet.draw()
    draw_ui(selected_building)
    pygame.display.update()

def draw_ui(selected_building):
    # Draw all UI elements in the right panel
    panel_x = GAME_AREA_WIDTH + 20
    y = 30
    timer_left = max(0, int(GAME_TIME - (time.time() - start_time)))
    time_text = font.render(f"Time left: {timer_left}s", True, ORANGE)
    win.blit(time_text, (panel_x, y))
    y += 40
    score_text = font.render(f"Player Score: {player_score}", True, GREEN)
    win.blit(score_text, (panel_x, y))
    y += 30
    ai_score_text = font.render(f"AI Score: {ai_score}", True, GREEN)
    win.blit(ai_score_text, (panel_x, y))
    y += 40
    coins_text = font.render(f"Player Coins: {player_coins}", True, YELLOW)
    win.blit(coins_text, (panel_x, y))
    y += 30
    ai_coins_text = font.render(f"AI Coins: {ai_coins}", True, YELLOW)
    win.blit(ai_coins_text, (panel_x, y))
    y += 40
    name = f"{selected_building} ({BUILD_COSTS[selected_building]})" if selected_building else "None"
    sel_text = font.render(f"Selected: {name}", True, WHITE)
    win.blit(sel_text, (panel_x, y))
    y += 30
    info = font.render("Press 1-6 to select and click to place", True, WHITE)
    win.blit(info, (panel_x, y))

def spawn_unit(building):
    if time.time() - building.last_spawn >= 11:
        new_unit = Unit(building.x, building.y, building.type, building.owner)
        units.append(new_unit)
        building.last_spawn = time.time()

def update_income():
    global player_coins
    now = time.time()
    for b in buildings:
        if b.owner == "player" and b.type in ["castle", "windmill"]:
            if now - b.last_coin >= 8:
                player_coins += 10
                b.last_coin = now

def get_adjacent(x, y):
    for b in buildings:
        if b.owner == "player":
            if abs(b.x - x) + abs(b.y - y) == 1:
                return True
    return False

def get_ai_adjacent(x, y):
    for b in buildings:
        if b.owner == "ai":
            if abs(b.x - x) + abs(b.y - y) == 1:
                return True
    return False

def ai_strategy():
    global ai_coins
    available_builds = ["windmill", "tank", "soldier", "drone", "spider"]
    random.shuffle(available_builds)
    for y in range(ROWS // 2):
        for x in range(COLS):
            if (x, y) not in occupied_tiles and get_ai_adjacent(x, y):
                for btype in available_builds:
                    if ai_coins >= BUILD_COSTS[btype]:
                        buildings.append(Building(x, y, btype, "ai"))
                        ai_coins -= BUILD_COSTS[btype]
                        return

def update_ai_income():
    global ai_coins
    now = time.time()
    for b in buildings:
        if b.owner == "ai" and b.type in ["castle", "windmill"]:
            if now - b.last_coin >= 8:
                ai_coins += 10
                b.last_coin = now

def show_winner(winner_owner=None):
    # Show winner and final score
    win.fill(GRAY)
    if winner_owner == "player":
        msg = "Player Wins!"
    elif winner_owner == "ai":
        msg = "AI Wins!"
    else:
        # Timer ended, decide by score
        if player_score > ai_score:
            msg = "Player Wins by Score!"
        elif ai_score > player_score:
            msg = "AI Wins by Score!"
        else:
            msg = "Draw!"
    msg_text = font.render(msg, True, YELLOW)
    score_text = font.render(f"Player Score: {player_score} | AI Score: {ai_score}", True, WHITE)
    win.blit(msg_text, (WIDTH // 2 - 100, HEIGHT // 2 - 30))
    win.blit(score_text, (WIDTH // 2 - 120, HEIGHT // 2 + 10))
    pygame.display.update()
    pygame.time.wait(5000)
    pygame.quit()
    exit()

def game_loop():
    global player_coins
    selected_building = None
    running = True
    ai_timer = time.time()
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                gx, gy = x // TILE_SIZE, y // TILE_SIZE
                if selected_building:
                    cost = BUILD_COSTS[selected_building]
                    if player_coins >= cost and get_adjacent(gx, gy):
                        buildings.append(Building(gx, gy, selected_building, "player"))
                        player_coins -= cost
                        selected_building = None
            if event.type == pygame.KEYDOWN:
                keys = {
                    pygame.K_1: "windmill",
                    pygame.K_2: "tank",
                    pygame.K_3: "soldier",
                    pygame.K_4: "drone",
                    pygame.K_5: "spider",
                    pygame.K_6: "defense"
                }
                if event.key in keys:
                    selected_building = keys[event.key]

        for b in buildings:
            if b.type in UNIT_SPEEDS:
                spawn_unit(b)
            b.shoot()

        update_income()
        update_ai_income()

        if time.time() - ai_timer > 4:
            ai_strategy()
            ai_timer = time.time()

        for u in units:
            u.move()
            u.shoot()

        for bullet in bullets[:]:
            if bullet.update():
                bullets.remove(bullet)

        draw_game(selected_building)

        # Check timer
        if (time.time() - start_time) >= GAME_TIME:
            show_winner()
            break

    pygame.quit()

ROWS = GAME_ROWS
COLS = GAME_COLS

if __name__ == '__main__':
    game_loop()

