import pygame

# Initialize Pygame
pygame.init()
window_size = (1600, 900)
global screen
screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
pygame.display.set_caption('Game Setup')
clock = pygame.time.Clock()
pygame.key.set_repeat(500, 50) #time in ms

from pregame import config
successfullBoot, clientMode, newGame, saveData = config(screen, clock)

if not successfullBoot:
  pygame.quit()
  quit(0)

conn_dict = dict()

if clientMode == "hostServer":
  from networking import start_server
  serverConn, conn_dict = start_server(conn_dict, saveData)

if clientMode == "join":
  ip, playername = saveData
  from networking import start_client
  try:
    conn_dict = start_client(ip, conn_dict)
  except:
    print("[CONNECTION ERROR] Client Failed to Connect!")
    quit(1)
  
  while conn_dict["Server"]["data"] is None:
    pass
  
  saveData: bytes = conn_dict["Server"]["data"]
  conn_dict["Server"]["data"] = None

from pregame import lobby
conn_dict, saveData = lobby(screen, clock, conn_dict, clientMode, newGame, saveData)

from gameloop import gameloop
gameCompleted, saveData = gameloop(screen, clock, newGame, saveData)

from postgame import postgame
postgame(screen, clock, gameCompleted, saveData)

for conn in conn_dict.values():
  conn.kill()
if clientMode == "hostServer":
  serverConn.kill()

# Shut down Pygame
pygame.quit()
quit(0)