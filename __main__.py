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
successfullBoot, clientMode, newGame, gameState = config(screen, clock)

conn_dict = dict()
def clean_quit():
  for conn in conn_dict.values():
    conn.kill()
  if clientMode == "hostServer":
    serverConn.kill()
  
  # Shut down Pygame
  pygame.quit()
  quit(0)

if not successfullBoot:
  clean_quit()

if clientMode == "hostServer":
  from networking import start_server
  serverConn, conn_dict = start_server(conn_dict, newGame, gameState)

if clientMode == "join":
  ip: str = gameState
  from networking import start_client
  try:
    conn_dict = start_client(ip, conn_dict)
    gameState = None
  except:
    print("[CONNECTION ERROR] Client Failed to Connect!")
    quit(1)

from pregame import lobby
successfulStart, gameState = lobby(screen, clock, conn_dict, clientMode, newGame, gameState)

if not successfulStart:
  clean_quit()

# stop looking for new client connections
del conn_dict
if clientMode == "hostServer":
  serverConn.kill_thread()

from gameloop import gameloop
gameCompleted, saveData = gameloop(screen, clock, newGame, gameState)

from postgame import postgame
postgame(screen, clock, gameCompleted, saveData)

clean_quit()
