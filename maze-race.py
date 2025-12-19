import pygame
import sys
from network import Network

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1900, 900
TILE_SIZE = 30
FPS = 60

# COLORS
BLACK = (10, 10, 15)
FLOOR_COLOR = (20, 20, 30)
WALL_COLOR = (50, 50, 100)
PHASING_WALL_COLOR = (0, 255, 255) 
EXIT_COLOR = (50, 255, 50)         
LOBBY_BG = (15, 15, 20)
UI_BG = (0, 0, 0, 150) 

class Game:
    def __init__(self):
        self.name = input("Enter your name: ")
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"Maze-Race - {self.name}")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.score_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.lobby_font = pygame.font.SysFont("Arial", 30)
        self.title_font = pygame.font.SysFont("Arial", 60, bold=True)
        self.huge_font = pygame.font.SysFont("Arial", 100, bold=True)

        self.net = Network()
        start_data = self.net.p_id
        
        self.my_id = start_data["id"]
        
        self.my_color = (255, 255, 255) 
        
        # Grid Setup
        self.cols = WIDTH // TILE_SIZE
        self.rows = HEIGHT // TILE_SIZE
        
        self.rect = pygame.Rect(TILE_SIZE + 5, TILE_SIZE + 5, TILE_SIZE - 10, TILE_SIZE - 10)
        self.goal_pos = ((self.cols-3)*TILE_SIZE, (self.rows-3)*TILE_SIZE)
        self.goal_rect = pygame.Rect(self.goal_pos[0], self.goal_pos[1], TILE_SIZE, TILE_SIZE)

        # Game State Variables
        self.map_data = []
        self.players_data = {}
        self.server_walls_active = True 
        self.server_status = "LOBBY" 
        self.server_timer = 0
        self.winner_name = ""
        self.command_queue = ""

    def handle_input(self):
        keys = pygame.key.get_pressed()

        if self.server_status == "LOBBY":
            if self.my_id == 0 and keys[pygame.K_SPACE]:
                self.command_queue = "start_game"
            return 

        if self.server_status in ["PREVIEW", "MATCH_OVER"]:
            return 

        vel = 4
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -vel
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = vel
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -vel
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = vel

        self.rect.x += dx
        if self.check_collision(self.rect): self.rect.x -= dx
        self.rect.y += dy
        if self.check_collision(self.rect): self.rect.y -= dy
        
        if self.rect.colliderect(self.goal_rect):
            self.command_queue = "reached_goal"
            self.rect.x = TILE_SIZE + 5
            self.rect.y = TILE_SIZE + 5

    def check_collision(self, rect):
        if not self.map_data: return False
        
        start_c = rect.left // TILE_SIZE
        end_c = rect.right // TILE_SIZE
        start_r = rect.top // TILE_SIZE
        end_r = rect.bottom // TILE_SIZE
        
        for r in range(start_r, end_r + 1):
            for c in range(start_c, end_c + 1):
                if 0 <= r < len(self.map_data) and 0 <= c < len(self.map_data[0]):
                    tile = self.map_data[r][c]
                    if tile == 1: return True
                    if tile == 2 and self.server_walls_active: return True
        return False

    def send_update(self):
        my_data = {
            "x": self.rect.x,
            "y": self.rect.y,
            "color": self.my_color,
            "name": self.name
        }
        
        if self.command_queue:
            my_data["command"] = self.command_queue
            self.command_queue = "" 

        response = self.net.send(my_data)
        if response:
            self.players_data = response["players"]
            self.server_walls_active = response["walls_active"]
            self.server_status = response["status"]
            self.server_timer = response["timer"]
            self.map_data = response["map"]
            self.winner_name = response.get("winner_name", "")

            if self.my_id in self.players_data:
                self.my_color = self.players_data[self.my_id]["color"]

            if self.server_status == "PREVIEW":
                 if self.rect.x > 200:
                     self.rect.x = TILE_SIZE + 5
                     self.rect.y = TILE_SIZE + 5

    def draw_leaderboard(self):
        if not self.players_data: return

        sorted_players = sorted(self.players_data.values(), key=lambda p: p["score"], reverse=True)
        
        panel_w, panel_h = 250, 300
        panel_x = WIDTH - panel_w - 20
        panel_y = 20
        
        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        s.fill(UI_BG)
        self.screen.blit(s, (panel_x, panel_y))
        
        header = self.score_font.render("LEADERBOARD", True, (255, 215, 0))
        self.screen.blit(header, (panel_x + 10, panel_y + 10))
        
        y_off = 50
        for p in sorted_players:
            name = p['name']
            score = p['score']
            line_str = f"{name} : {score}"
            
            p_color = p['color']
            
            txt = self.score_font.render(line_str, True, p_color)
            self.screen.blit(txt, (panel_x + 20, panel_y + y_off))
            y_off += 30

    def draw_lobby(self):
        self.screen.fill(LOBBY_BG)
        title = self.title_font.render("GAME LOBBY", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        
        y_offset = 200
        if self.players_data:
            count_txt = self.lobby_font.render(f"Players: {len(self.players_data)}", True, (0, 200, 255))
            self.screen.blit(count_txt, (WIDTH//2 - count_txt.get_width()//2, 160))

            for p_id, p_data in self.players_data.items():
                p_name = p_data["name"]
                p_color = p_data["color"] 
                is_host = "[HOST]" if p_id == 0 else ""
                
                txt = self.lobby_font.render(f"{p_name} {is_host}", True, p_color)
                self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y_offset))
                y_offset += 40

        if self.my_id == 0:
            msg = self.lobby_font.render("Press [SPACE] to Start Match", True, (0, 255, 0))
            if pygame.time.get_ticks() % 1000 < 500:
                self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT - 100))
        else:
            msg = self.lobby_font.render("Waiting for Host...", True, (150, 150, 150))
            self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT - 100))

    def draw_game(self):
        self.screen.fill(BLACK)
        
        if self.map_data:
            for r in range(len(self.map_data)):
                for c in range(len(self.map_data[0])):
                    rect = pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    tile = self.map_data[r][c]
                    if tile == 0:
                        pygame.draw.rect(self.screen, FLOOR_COLOR, rect)
                        pygame.draw.rect(self.screen, (25, 25, 35), rect, 1)
                    elif tile == 1:
                        pygame.draw.rect(self.screen, WALL_COLOR, rect)
                    elif tile == 2:
                        if self.server_walls_active:
                            pygame.draw.rect(self.screen, PHASING_WALL_COLOR, rect)
                            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
                        else:
                            pygame.draw.rect(self.screen, (0, 50, 50), rect, 1)

        pygame.draw.rect(self.screen, EXIT_COLOR, self.goal_rect)

        if self.players_data:
            for p_id, p_data in self.players_data.items():
                if p_id != self.my_id:
                    p_rect = pygame.Rect(p_data["x"], p_data["y"], TILE_SIZE-10, TILE_SIZE-10)
                    pygame.draw.rect(self.screen, p_data["color"], p_rect)
                    name_txt = self.font.render(p_data["name"], True, (255, 255, 255))
                    self.screen.blit(name_txt, (p_data["x"], p_data["y"] - 15))

        pygame.draw.rect(self.screen, self.my_color, self.rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.rect, 2)

        self.draw_leaderboard()

        if self.server_status == "PREVIEW":
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(100)
            self.screen.blit(overlay, (0,0))
            
            time_left = int(self.server_timer) + 1
            txt = self.huge_font.render(f"NEW ROUND: {time_left}", True, (255, 255, 0))
            self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2))

        elif self.server_status == "MATCH_OVER":
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.fill((50, 0, 0))
            overlay.set_alpha(200)
            self.screen.blit(overlay, (0,0))
            
            w_txt = self.huge_font.render(f"WINNER: {self.winner_name}!", True, (0, 255, 0))
            self.screen.blit(w_txt, (WIDTH//2 - w_txt.get_width()//2, HEIGHT//2 - 50))
            
            sub = self.font.render("Returning to Lobby...", True, (255, 255, 255))
            self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 50))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
            
            self.handle_input()
            self.send_update()
            
            if self.server_status == "LOBBY":
                self.draw_lobby()
            else:
                self.draw_game()
                
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()