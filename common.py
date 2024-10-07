import datetime
import os
import pickle
import pygame

from objects.tilebag import TileBag
from objects.board import Board
from objects.player import Player
from objects.bank import Bank

# GLOBAL GAME PERMISSIONS
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "silent"
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
HIDE_PERSONAL_INFO = False
ALLOW_SAVES = True
ALLOW_QUICKSAVES = True
MAX_FRAMERATE = 120

class Colors:
  def __init__(self):
    self.BLACK = (0, 0, 0)
    self.WHITE = (255, 255, 255)
    self.GRAY = (192, 192, 192)
    self.UNSELECTABLEGRAY = (158, 158, 158)
    self.RED = (255, 0, 0)
    self.LIGHTGREEN = (72, 178, 72)
    self.GREEN = (34, 139, 34)
    self.DARKGREEN = (27, 108, 27)
    self.YELLOW = (240, 230, 140)
    self.OUTLINE = (189, 183, 107)
    
    self.Tower = (255, 255, 0) #bright yellow
    self.Luxor = (255, 145, 0), # bright orange
    self.Surfside = (32, 178, 170), # teal
    self.Nomad = (78, 49, 82), # murky purple
    self.Keystone = (27, 108, 27), # green
    self.Eclipse = (99, 38, 95), # deep purple
    
    self.American = (0, 0, 230), # blue
    self.Festival = (35, 70, 41), # dark green
    self.Worldwide = (130, 76, 0), # brown
    self.Highrise = (219, 120, 130), # rose/peach
    self.Boulevard = (185, 20, 20), # deep brick red
    self.Rendezvous = (34, 205, 66), # neon green
    self.Voyager = (71, 71, 71), # smoggy dark gray
    self.Journeyman = (123, 249, 206), # mint 
    
    self.Imperial = (255, 51, 153), # bright pink
    self.Continental = (100, 149, 237), # light blue
    self.Wynand = (153, 122, 141), # gray
    self.Mirage = (211, 57, 238), # magenta
    self.Panorama = (84, 248, 254) #searing bright blue
    
    self.colorcount = 10
    self.chaincolorcount = 19

class Fonts:
  def __init__(self) -> None:
    self.main = 'timesnewroman'
    self.tile = "arial"
    self.oblivious = r'fonts/oblivious-font.regular.ttf'

colors = Colors()
fonts = Fonts()

def colortest(screen: pygame.Surface, clock: pygame.time.Clock):
  colors = Colors()
  while colorLoop:
    for color in colors.__dict__.keys():
      screen.fill(colors.__getattribute__(color))
      pygame.display.flip()
      event = pygame.event.poll()
      if event.type == pygame.QUIT:
        colorLoop = False
        break
      clock.tick(1)

def pack_save(tilebag:TileBag, board:Board, players:list[Player], bank:Bank, personal_info_names:list[str] = None, currentP:Player = None) -> tuple[bytes, list[str]]:
  if HIDE_PERSONAL_INFO and personal_info_names is not None:
    for i, p in enumerate(players):
      p.name = personal_info_names[i]
  
  if currentP is not None:
    currentOrderP = players[players.index(currentP):] + players[:players.index(currentP)]
  else:
    currentOrderP = players
  currentOrderNames = [p.name for p in currentOrderP]
  
  objects = (tilebag, board, currentOrderP, bank)
  saveData = pickle.dumps(objects, 5)
  
  if HIDE_PERSONAL_INFO and personal_info_names is not None:
    for i, p in enumerate(players):
      p.name = f"Player {i+1}"
  
  return saveData, currentOrderNames

def unpack_save(saveData: bytes, ignore_PIN: bool = False, clearConns: bool = False) -> tuple[TileBag, Board, list[Player], Bank, list[str] | None]:
  objects: tuple[TileBag, Board, list[Player], Bank] = pickle.loads(saveData)
  tilebag, board, players, bank = objects
  
  # re-link internal tilebags and boards
  board.tilebag = tilebag
  bank.tilebag = tilebag
  bank.board = board
  for p in players:
    p.tilebag = tilebag
    p.board = board
    if clearConns:
      p.conn = None
  
  if HIDE_PERSONAL_INFO and not ignore_PIN:
    personal_info_names = [p.name for p in players]
    for i, p in enumerate(players):
      p.name = f"Player {i+1}"
  else: 
    personal_info_names = None
  return (tilebag, board, players, bank, personal_info_names)

def write_save(saveData: bytes, currentOrderNames: list[str] = None, turnnumber: str = None, quicksave: bool = False):
  date = datetime.date.isoformat(datetime.date.today())
  if quicksave:
    save_file_new = "quicksave"
  else:
    save_file_new = date
    if currentOrderNames is not None:
      save_file_new += f'_{len(currentOrderNames)}players_{"".join(currentOrderNames)}'
    if turnnumber is not None:
      save_file_new += f'_turn{turnnumber.turnCounter[-1]}'
  if not os.path.exists(rf'{DIR_PATH}\saves\{save_file_new}'):
    with open(rf'{DIR_PATH}\saves\{save_file_new}', 'x') as file:
      pass
  with open(rf'{DIR_PATH}\saves\{save_file_new}', 'wb') as file:
    pickle.dump(saveData, file)
  return
