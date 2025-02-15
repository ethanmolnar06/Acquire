# region Initialize Pygame
import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "silent"
import pygame
pygame.init()
window_size = (1600, 900)
screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
pygame.scrap.init()
pygame.display.set_caption('Game Setup')
clock = pygame.time.Clock()
pygame.key.set_repeat(300, 50) #time in ms
gameUtils = (screen, clock)
# endregion

# region Pregame Config
from pregame import config
from objects.networking import start_client, start_server

clientReady = False
while not clientReady:
  successfullBoot, clientMode, newGame, gameState = config(gameUtils)
  
  conn_dict = dict()
  def clean_quit(conn_dict):
    for conn in conn_dict.values():
      conn.kill()
    del conn_dict
    if clientMode == "hostServer":
      serverThread.kill()
    # Shut down Pygame
    pygame.quit()
    sys.exit()
  
  if not successfullBoot:
    clean_quit(conn_dict)
  
  if clientMode == "hostLocal":
    pygame.display.set_caption('Acquire')
  
  elif clientMode == "hostServer":
    serverThread, conn_dict = start_server(conn_dict, newGame, gameState)
    pygame.display.set_caption('Game Lobby [Host]')
  
  elif clientMode == "join":
    ip: str = gameState
    try:
      print(f"[CONNECTING] to {ip}")
      conn_dict = start_client(ip, conn_dict)
      print(f"[CONNECTION SUCCESS] Client Connected to {conn_dict["server"]}")
      gameState = None
      clientReady = True
      pygame.display.set_caption('Game Lobby [Client]')
    except:
      print("[CONNECTION FAILURE] Client Failed to Connect")
      continue
  clientReady = True
# endregion

from pregame import lobby
successfulStart, gameState, my_uuid = lobby(gameUtils, conn_dict, clientMode, newGame, gameState)

if not successfulStart:
  clean_quit(conn_dict)

# Stop Looking for New Client Connections
from common import ALLOW_REJOIN
if clientMode == "hostServer" and not ALLOW_REJOIN:
  serverThread.kill()

pygame.display.set_caption('Acquire')
from gameloop import gameloop
gameCompleted, saveData = gameloop(gameUtils, newGame, gameState, clientMode, my_uuid)

pygame.display.set_caption('Post Game')
from postgame import postgame
postgame(gameUtils, gameCompleted, saveData)

# Shut Down
clean_quit(conn_dict)