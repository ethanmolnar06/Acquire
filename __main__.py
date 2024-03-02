import pygame
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

# Initialize Pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "silent"
pygame.init()
window_size = (1600, 900)
screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
pygame.display.set_caption('Game Setup')
clock = pygame.time.Clock()
framerate = 120

# GLOBAL GAME PERMISSIONS
HIDE_PERSONAL_INFO = False
ALLOW_SAVES = True
ALLOW_QUICKSAVES = True

from pregame import pregame
successfullBoot, gameStart, tilebag, board, bank, players, personal_info_names, globalStats, loadedSaveFile = pregame(dir_path, screen, clock, framerate)

if gameStart:
  from gameloop import gameloop
  saveData, currentOrderP, players, globalStats = gameloop(dir_path, screen, clock, framerate, tilebag, board, bank, players, personal_info_names, globalStats, loadedSaveFile)

if successfullBoot:
  from postgame import postgame
  postgame(dir_path, screen, clock, framerate, players, saveData, currentOrderP, globalStats)

# Shut down Pygame
pygame.quit()