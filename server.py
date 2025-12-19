import socket
from _thread import *
import pickle
import random
import time

server = "localhost" # بدل هنا ل ip ديالك او لي غيكون server 
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(10)
print("--- Server Started. Waiting for connections... ---")

# --- SETTINGS ---
WIDTH, HEIGHT = 1900, 900
TILE_SIZE = 30
COLS = WIDTH // TILE_SIZE
ROWS = HEIGHT // TILE_SIZE
if COLS % 2 == 0: COLS -= 1
if ROWS % 2 == 0: ROWS -= 1

PREVIEW_TIME = 5.0
WIN_SCORE = 10 

PLAYER_COLORS = [
    (255, 0, 0),    # أحمر
    (0, 0, 255),    # أزرق
    (0, 255, 0),    # أخضر
    (255, 255, 0),  # أصفر
    (255, 0, 255),  # أرجواني
    (0, 255, 255),  # سماوي
    (255, 165, 0),  # برتقالي
    (128, 0, 128),  # بنفسجي غامق
    (255, 192, 203),# وردي
    (255, 255, 255) # أبيض
]

# --- Game State ---
game_state = {
    "status": "LOBBY", 
    "timer": PREVIEW_TIME,
    "walls_active": True,
    "players": {},
    "map": [],      
    "winner_name": "" 
}

def generate_maze():
    map_data = [[1 for _ in range(COLS)] for _ in range(ROWS)]
    stack = [(1, 1)]
    map_data[1][1] = 0
    while stack:
        x, y = stack[-1]
        neighbors = []
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 < nx < COLS and 0 < ny < ROWS:
                if map_data[ny][nx] == 1:
                    neighbors.append((nx, ny, dx, dy))
        if neighbors:
            nx, ny, dx, dy = random.choice(neighbors)
            map_data[y + dy//2][x + dx//2] = 0 
            map_data[ny][nx] = 0 
            stack.append((nx, ny))
        else:
            stack.pop()
    
    goal_r, goal_c = ROWS - 2, COLS - 2
    map_data[goal_r][goal_c] = 0      
    map_data[goal_r][goal_c - 1] = 0  
    map_data[goal_r - 1][goal_c] = 0  
    map_data[goal_r - 1][goal_c - 1] = 0 

    map_data[1][2] = 0 
    map_data[2][1] = 0 

    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if map_data[r][c] == 1:
                dist_start = abs(r - 1) + abs(c - 1)
                dist_goal = abs(r - goal_r) + abs(c - goal_c)
                if dist_start < 4 or dist_goal < 4:
                    continue 
                if random.random() < 0.08:
                    map_data[r][c] = 2
    return map_data

game_state["map"] = generate_maze()

def reset_round():
    game_state["map"] = generate_maze()
    game_state["status"] = "PREVIEW"
    game_state["timer"] = PREVIEW_TIME
    for p_id in game_state["players"]:
        game_state["players"][p_id]["x"] = TILE_SIZE + 5
        game_state["players"][p_id]["y"] = TILE_SIZE + 5

def reset_match():
    game_state["status"] = "LOBBY"
    game_state["winner_name"] = ""
    game_state["map"] = generate_maze()
    for p_id in game_state["players"]:
        game_state["players"][p_id]["score"] = 0
        game_state["players"][p_id]["x"] = TILE_SIZE + 5
        game_state["players"][p_id]["y"] = TILE_SIZE + 5

def game_logic_loop():
    wall_cycle_timer = 0
    while True:
        time.sleep(0.1)
        if game_state["status"] == "LOBBY":
            pass 
        elif game_state["status"] == "PREVIEW":
            game_state["timer"] -= 0.1
            if game_state["timer"] <= 0:
                game_state["status"] = "PLAYING"
                game_state["timer"] = 0
        elif game_state["status"] == "PLAYING":
            wall_cycle_timer += 0.1
            if wall_cycle_timer >= 2.0:
                game_state["walls_active"] = not game_state["walls_active"]
                wall_cycle_timer = 0
        elif game_state["status"] == "MATCH_OVER":
            game_state["timer"] -= 0.1
            if game_state["timer"] <= 0:
                reset_match()

start_new_thread(game_logic_loop, ())

def threaded_client(conn, current_player_id):
    start_info = {"id": current_player_id}
    conn.send(pickle.dumps(start_info))

    while True:
        try:
            data = pickle.loads(conn.recv(2048*8))
            if not data: break
            

            assigned_color = game_state["players"][current_player_id]["color"]

            current_score = 0
            if current_player_id in game_state["players"]:
                current_score = game_state["players"][current_player_id]["score"]

            game_state["players"][current_player_id] = {
                "x": data["x"], 
                "y": data["y"], 
                "color": assigned_color,
                "name": data["name"],
                "score": current_score
            }

            if "command" in data:
                cmd = data["command"]
                if cmd == "start_game" and game_state["status"] == "LOBBY":
                    reset_round()
                if cmd == "reached_goal" and game_state["status"] == "PLAYING":
                    game_state["players"][current_player_id]["score"] += 1
                    new_score = game_state["players"][current_player_id]["score"]
                    if new_score >= WIN_SCORE:
                        game_state["status"] = "MATCH_OVER"
                        game_state["winner_name"] = data["name"]
                        game_state["timer"] = 5.0 
                    else:
                        reset_round()

            conn.sendall(pickle.dumps(game_state))
        except Exception as e:
            print(e)
            break

    print(f"Player {current_player_id} Disconnected")
    if current_player_id in game_state["players"]:
        del game_state["players"][current_player_id]
    conn.close()

player_id_counter = 0
while True:
    conn, addr = s.accept()

    unique_color = PLAYER_COLORS[player_id_counter % len(PLAYER_COLORS)]
    
    game_state["players"][player_id_counter] = {
        "x": TILE_SIZE + 5,
        "y": TILE_SIZE + 5,
        "color": unique_color, 
        "name": f"P{player_id_counter}",
        "score": 0
    }
    
    start_new_thread(threaded_client, (conn, player_id_counter))
    player_id_counter += 1