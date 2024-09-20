import pygame

# Initialize Pygame
pygame.init()
window_size = (1600, 900)
global screen
screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
pygame.display.set_caption('Game Setup')
clock = pygame.time.Clock()
pygame.key.set_repeat(500, 50) #time in ms

from pregame import config, lobby
successfullBoot, clientMode, newGame, saveData = config(screen, clock)

if not successfullBoot:
  pygame.quit()
  quit(0)

if clientMode == "hostLocal":
  if saveData is None:
    tilebag, board, globalStats, bank, players, personal_info_names = newGame
  else:
    tilebag, board, globalStats, bank, players, personal_info_names = saveData
  
  pygame.display.set_caption('Acquire Board')
  from local.gameloop import gameloop
  saveData, currentOrderP, players, globalStats, gameCompleted = gameloop(screen, clock, tilebag, board, globalStats, bank, players, personal_info_names)
  
  from local.postgame import postgame
  postgame(screen, clock, players, saveData, currentOrderP, globalStats, gameCompleted)
  
  # Shut down Pygame
  pygame.quit()
  quit(0)

if clientMode == "join":
  ip, playername = newGame
  from networking import start_client
  try:
    client, listen_thread, conn_dict = start_client(ip)
  except:
    print("[CONNECTION ERROR] Client Failed to Connect!")
    quit(1)
  
  from networking import send, Command
  send(client, Command("set", "player", "name", playername))

if clientMode == "hostServer":
  from networking import start_server
  conn_dict = dict()
  server, accept_conn_thread, conn_dict = start_server(conn_dict)
  
  lobby(screen, clock, conn_dict, clientMode, newGame, saveData)

lobby(screen, clock, conn_dict, clientMode, newGame, saveData)
