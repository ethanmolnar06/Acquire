import pygame

# Initialize Pygame
pygame.init()
window_size = (1600, 900)
screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
pygame.scrap.init()
pygame.display.set_caption('Game Setup')
clock = pygame.time.Clock()
pygame.key.set_repeat(300, 50) #time in ms
gameUtils = (screen, clock)

from pregame import config
successfullBoot, clientMode, newGame, gameState = config(gameUtils)

from objects.networking import *
conn_dict = dict()
def clean_quit():
  if clientMode == "hostServer":
    serverThread.kill()
  for conn in conn_dict.values():
    conn.kill()
  # Shut down Pygame
  pygame.quit()
  quit(0)

if not successfullBoot:
  clean_quit()

if clientMode == "hostServer":
  serverThread, conn_dict = start_server(conn_dict, newGame, gameState)

if clientMode == "join":
  ip: str = gameState
  try:
    print("[CONNECTING]")
    conn_dict = start_client(ip, conn_dict)
    gameState = None
  except:
    print("[CONNECTION ERROR] Client Failed to Connect!")
    quit(1)

from pregame import lobby
successfulStart, gameState = lobby(gameUtils, conn_dict, clientMode, newGame, gameState)

if not successfulStart:
  clean_quit()

# stop looking for new client connections
del conn_dict
if clientMode == "hostServer":
  serverThread.kill()

from gameloop import gameloop
gameCompleted, saveData = gameloop(gameUtils, newGame, gameState)

from postgame import postgame
postgame(gameUtils, gameCompleted, saveData)

# Shut down Pygame
pygame.quit()
quit(0)