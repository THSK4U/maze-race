import pygame
import random
import sys

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1920, 900
TILE_SIZE = 30
FPS = 60
LEVEL_TIME = 60.0 # time to play
PREVIEW_TIME = 5.0 # time to analyze the map
P1_NAME = input("[ P1 ] What's your name: ").lower()
P2_NAME = input("[ P2 ] What's your name: ").lower()

# COLORS
BLACK = (10, 10, 15)
FLOOR_COLOR = (20, 20, 30)
WALL_COLOR = (50, 50, 100)
PHASING_WALL_COLOR = (0, 255, 255) 
EXIT_COLOR = (50, 255, 50)         
UI_BAR_BG = (50, 50, 50)
UI_BAR_FILL = (0, 200, 255)
RED_ALERT = (255, 50, 50)
TEXT_WHITE = (255, 255, 255)

# PLAYERS COLORS
P1_COLOR = (255, 200, 50)  # Gold
P2_COLOR = (50, 100, 255)  # Blue

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Labyrinth: Analyze & Race")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.big_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.huge_font = pygame.font.SysFont("Arial", 100, bold=True)
        
        # Grid Setup
        self.cols = WIDTH // TILE_SIZE
        self.rows = HEIGHT // TILE_SIZE
        if self.cols % 2 == 0: self.cols -= 1
        if self.rows % 2 == 0: self.rows -= 1
        
        # SCORE SYSTEM
        self.p1_score = 0
        self.p2_score = 0
        
        # Start First Level
        self.start_new_level()

    def start_new_level(self):
        """Resets map and players"""
        self.map_data = [] 
        self.generate_perfect_maze()
        
        # Players Start Position
        start_x = TILE_SIZE + 5
        start_y = TILE_SIZE + 5
        size = TILE_SIZE - 10
        
        self.p1_rect = pygame.Rect(start_x, start_y, size, size)
        self.p2_rect = pygame.Rect(start_x, start_y, size, size)
        
        # Goal Position
        self.goal_rect = pygame.Rect((self.cols-2)*TILE_SIZE, (self.rows-2)*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        
        # Reset Mechanics
        self.time_scale = 1.0 
        self.time_energy = 100 
        self.max_energy = 100
        self.phase_timer = 0
        self.walls_active = True 
        self.countdown = LEVEL_TIME 
        
        # === NEW: PREVIEW STATE ===
        self.game_state = "PREVIEW" # 'PREVIEW' or 'PLAYING'
        self.preview_timer = PREVIEW_TIME

    def trigger_round_end(self, winner_name):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        if winner_name == "DRAW":
            overlay.fill(RED_ALERT)
            msg = "TIME UP! DRAW!"
        else:
            if P1_NAME in winner_name:
                overlay.fill(P1_COLOR)
                self.p1_score += 1
            else:
                overlay.fill(P2_COLOR)
                self.p2_score += 1
            msg = f"{winner_name} WINS!"

        overlay.set_alpha(200)
        self.screen.blit(overlay, (0,0))
        
        txt = self.huge_font.render(msg, True, BLACK)
        self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2))
        
        pygame.display.flip()
        pygame.time.delay(2000)
        self.start_new_level()

    def generate_perfect_maze(self):
        self.map_data = [[1 for _ in range(self.cols)] for _ in range(self.rows)]
        stack = [(1, 1)]
        self.map_data[1][1] = 0 
        
        while stack:
            x, y = stack[-1]
            neighbors = []
            directions = [(0, -2), (0, 2), (-2, 0), (2, 0)] 
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 < nx < self.cols and 0 < ny < self.rows:
                    if self.map_data[ny][nx] == 1: 
                        neighbors.append((nx, ny, dx, dy))
            
            if neighbors:
                nx, ny, dx, dy = random.choice(neighbors)
                self.map_data[y + dy//2][x + dx//2] = 0
                self.map_data[ny][nx] = 0
                stack.append((nx, ny))
            else:
                stack.pop()

        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if self.map_data[r][c] == 1: 
                    if random.random() < 0.08: 
                        self.map_data[r][c] = 2

        self.map_data[1][2] = 0
        self.map_data[2][1] = 0
        self.map_data[self.rows-2][self.cols-3] = 0
        self.map_data[self.rows-3][self.cols-2] = 0

    def handle_input(self):
        # === IMPORTANT: FREEZE INPUT DURING PREVIEW ===
        if self.game_state == "PREVIEW":
            return # لا تستقبل أي ضغطات أزرار
            
        keys = pygame.key.get_pressed()
        vel = 4
        
        # Time Control
        if (keys[pygame.K_RCTRL] or keys[pygame.K_LSHIFT]) and self.time_energy > 0:
            self.time_scale = 0.1
            self.time_energy -= 0.5 
        else:
            self.time_scale = 1.0 
            if self.time_energy < self.max_energy:
                self.time_energy += 0.1 

        # P1 Move
        dx1, dy1 = 0, 0
        if keys[pygame.K_LEFT]: dx1 = -vel
        if keys[pygame.K_RIGHT]: dx1 = vel
        if keys[pygame.K_UP]: dy1 = -vel
        if keys[pygame.K_DOWN]: dy1 = vel
        self.move_player(self.p1_rect, dx1, dy1)

        # P2 Move
        dx2, dy2 = 0, 0
        if keys[pygame.K_a]: dx2 = -vel
        if keys[pygame.K_d]: dx2 = vel
        if keys[pygame.K_w]: dy2 = -vel
        if keys[pygame.K_s]: dy2 = vel
        self.move_player(self.p2_rect, dx2, dy2)

    def move_player(self, rect, dx, dy):
        rect.x += dx
        if self.check_collision(rect):
            rect.x -= dx 
        rect.y += dy
        if self.check_collision(rect):
            rect.y -= dy 

    def check_collision(self, rect):
        start_c = rect.left // TILE_SIZE
        end_c = rect.right // TILE_SIZE
        start_r = rect.top // TILE_SIZE
        end_r = rect.bottom // TILE_SIZE
        
        for r in range(start_r, end_r + 1):
            for c in range(start_c, end_c + 1):
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    tile = self.map_data[r][c]
                    if tile == 1: return True
                    if tile == 2 and self.walls_active: return True
        return False

    def update_logic(self):
        # === PREVIEW LOGIC ===
        if self.game_state == "PREVIEW":
            self.preview_timer -= 1 / FPS
            if self.preview_timer <= 0:
                self.game_state = "PLAYING"
            return

        # === GAMEPLAY LOGIC ===
        # 1. Update Game Timer
        self.countdown -= (1.0 / FPS) * self.time_scale
        if self.countdown <= 0:
            self.trigger_round_end("DRAW")
            return

        # 2. Update Walls
        self.phase_timer += 1 * self.time_scale
        if self.phase_timer > 120: 
            self.walls_active = not self.walls_active
            self.phase_timer = 0
            
            p1_dead = self.walls_active and self.check_collision(self.p1_rect)
            p2_dead = self.walls_active and self.check_collision(self.p2_rect)
            
            if p1_dead and p2_dead:
                self.trigger_round_end("DRAW")
            elif p1_dead:
                self.trigger_round_end(P2_NAME)
            elif p2_dead:
                self.trigger_round_end(P1_NAME)

        # 3. Win Check
        if self.p1_rect.colliderect(self.goal_rect):
            self.trigger_round_end(P1_NAME)
        elif self.p2_rect.colliderect(self.goal_rect):
            self.trigger_round_end(P2_NAME)

    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw Map
        for r in range(self.rows):
            for c in range(self.cols):
                rect = pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                tile = self.map_data[r][c]
                if tile == 0:
                    pygame.draw.rect(self.screen, FLOOR_COLOR, rect)
                    pygame.draw.rect(self.screen, (25, 25, 35), rect, 1) 
                elif tile == 1:
                    pygame.draw.rect(self.screen, WALL_COLOR, rect)
                elif tile == 2:
                    if self.walls_active:
                        pygame.draw.rect(self.screen, PHASING_WALL_COLOR, rect)
                        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2) 
                    else:
                        pygame.draw.rect(self.screen, (0, 50, 50), rect, 1)

        # Draw Goal
        pygame.draw.rect(self.screen, EXIT_COLOR, self.goal_rect)

        # Draw Players
        pygame.draw.rect(self.screen, P1_COLOR, self.p1_rect)
        pygame.draw.rect(self.screen, P2_COLOR, self.p2_rect)
        
        p1_lbl = self.font.render(P1_NAME[:2], True, BLACK)
        p2_lbl = self.font.render(P2_NAME[:2], True, BLACK)
        self.screen.blit(p1_lbl, (self.p1_rect.centerx - 10, self.p1_rect.y))
        self.screen.blit(p2_lbl, (self.p2_rect.centerx - 10, self.p2_rect.y))

        # --- UI ELEMENTS ---
        pygame.draw.rect(self.screen, UI_BAR_BG, (10, 10, 200, 20))
        current_fill = (self.time_energy / self.max_energy) * 200
        pygame.draw.rect(self.screen, UI_BAR_FILL, (10, 10, current_fill, 20))
        
        timer_color = TEXT_WHITE
        if self.countdown < 10: timer_color = RED_ALERT 
        time_text = f"{self.countdown:.1f}"
        txt_surf = self.big_font.render(time_text, True, timer_color)
        self.screen.blit(txt_surf, (WIDTH//2 - txt_surf.get_width()//2, 10))

        s1 = self.big_font.render(f"{P1_NAME}: {self.p1_score}", True, P1_COLOR)
        self.screen.blit(s1, (10, 40))
        s2 = self.big_font.render(f"{P2_NAME}: {self.p2_score}", True, P2_COLOR)
        self.screen.blit(s2, (WIDTH - s2.get_width() - 10, 40))

        # === PREVIEW OVERLAY (BIG COUNTDOWN) ===
        if self.game_state == "PREVIEW":
            # Darken the background slightly
            dark_overlay = pygame.Surface((WIDTH, HEIGHT))
            dark_overlay.fill(BLACK)
            dark_overlay.set_alpha(150)
            self.screen.blit(dark_overlay, (0,0))
            
            # Show Numbers (3.. 2.. 1..)
            num = int(self.preview_timer) + 1
            if num > 0:
                preview_txt = self.huge_font.render(str(num), True, (255, 255, 0)) # Yellow
                self.screen.blit(preview_txt, (WIDTH//2 - preview_txt.get_width()//2, HEIGHT//2 - 50))
                
                info_txt = self.font.render("ANALYZE THE MAP!", True, TEXT_WHITE)
                self.screen.blit(info_txt, (WIDTH//2 - info_txt.get_width()//2, HEIGHT//2 + 50))
            else:
                 # Last frame before starting
                go_txt = self.huge_font.render("GO!", True, EXIT_COLOR)
                self.screen.blit(go_txt, (WIDTH//2 - go_txt.get_width()//2, HEIGHT//2 - 50))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.handle_input()
            self.update_logic()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()
