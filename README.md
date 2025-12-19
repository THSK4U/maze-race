# Maze-Race
## Features

* **Online Multiplayer:** Support for multiple players in the same maze.
* **Lobby System:** Players wait in a lobby until the host starts the match.
* **Round System:** When a player reaches the goal, the maze resets for everyone, and a new round begins.
* **Scoring:** The first player to reach the goal gets 1 point. The first to reach 10 points wins the match.
* **Dynamic Obstacles:** Walls that appear and disappear (Phasing Walls) are synchronized for all players.
* **Player Colors:** The server automatically assigns a unique color to each player.
* **Leaderboard:** A real-time scoreboard shows player names and scores.

# Project Files
* **server.py**: The main program that manages the game state, map generation, and player connections.

* **maze-race.py**: The game window that players use to play.

* **network.py**: A helper file that handles the connection between the client and the server.

# How to Run the Game

Follow these steps to play the game on a single computer.

---

## 1. Start the Server

Open your terminal or command prompt and run the server file.  
This terminal **must stay open** while the game is running.

**Command:**
```bash
python server.py
```
## 2. Start the Clients (Players)

Open a **new terminal window** for each player and run the maze-race file.

**Command:**
```bash
python maze-race.py
```
# How to Play on Different Computers

To play with friends on **different computers connected to the same Wi-Fi network**:

1. Find the **local IP address** of the computer running `server.py`  
   Example:
```bash
192.168.1.5
```
2. Open the following files:
- `network.py`
- `server.py`

3. Replace:
```bash
server = "localhost"
```
with:
```bash
    server = "192.168.1.5"
```

4. Run the server on the **host computer** and run the maze-race on the **other computers**.

---

Enjoy the game

<img width="1918" height="910" alt="image" src="https://github.com/user-attachments/assets/c5e43421-7892-4026-846a-542840527be5" />
