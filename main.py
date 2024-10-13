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

clientReady = False
while not clientReady:
  from pregame import config
  successfullBoot, clientMode, newGame, gameState = config(gameUtils)
  
  from objects.networking import *
  conn_dict = dict()
  def clean_quit():
    for conn in conn_dict.values():
      conn.kill()
    if clientMode == "hostServer":
      serverThread.kill()
    # Shut down Pygame
    pygame.quit()
    quit(0)
  
  if not successfullBoot:
    clean_quit()
  
  if clientMode == "hostLocal":
    clientReady = True
  
  elif clientMode == "hostServer":
    serverThread, conn_dict = start_server(conn_dict, newGame, gameState)
    clientReady = True
  
  elif clientMode == "join":
    ip: str = gameState
    try:
      print("[CONNECTING]")
      conn_dict = start_client(ip, conn_dict)
      print(f"[CONNECTION SUCCESS] Client Connected to {conn_dict["server"]}")
      gameState = None
      clientReady = True
    except:
      print("[CONNECTION FAILURE] Client Failed to Connect")

pygame.display.set_caption('Game Lobby')
from pregame import lobby
successfulStart, gameState, host_uuid, my_uuid = lobby(gameUtils, conn_dict, clientMode, newGame, gameState)

if not successfulStart:
  clean_quit()

# stop looking for new client connections
del conn_dict
if clientMode == "hostServer":
  serverThread.kill()

pygame.display.set_caption('Acquire')
from gameloop import gameloop
gameCompleted, saveData = gameloop(gameUtils, newGame, gameState, host_uuid, my_uuid)

pygame.display.set_caption('Post Game')
from postgame import postgame
postgame(gameUtils, gameCompleted, saveData)

# Shut down Pygame
pygame.quit()
quit(0)