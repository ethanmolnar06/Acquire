import datetime
import os
import pickle
import pygame
from copy import deepcopy

from objects import *

# TODO move these permisions to config.json & add argparse for cmd line launching
# GLOBAL GAME PERMISSIONS
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "silent"
DIR_PATH = os.path.realpath(os.curdir)
HIDE_PERSONAL_INFO = False
ALLOW_SAVES = True
ALLOW_QUICKSAVES = True
MAX_FRAMERATE = 120

class Colors:
  BLACK = (0, 0, 0)
  WHITE = (255, 255, 255)
  GRAY = (192, 192, 192)
  UNSELECTABLEGRAY = (158, 158, 158)
  RED = (255, 0, 0)
  LIGHTGREEN = (72, 178, 72)
  GREEN = (34, 139, 34)
  DARKGREEN = (27, 108, 27)
  YELLOW = (240, 230, 140)
  OUTLINE = (189, 183, 107)
  
  class ChainColors:
    Tower = (255, 255, 0) #bright yellow
    Luxor = (255, 145, 0), # bright orange
    Surfside = (32, 178, 170), # teal
    Nomad = (78, 49, 82), # murky purple
    Keystone = (27, 108, 27), # green
    Eclipse = (99, 38, 95), # deep purple
    
    American = (0, 0, 230), # blue
    Festival = (35, 70, 41), # dark green
    Worldwide = (130, 76, 0), # brown
    Highrise = (219, 120, 130), # rose/peach
    Boulevard = (185, 20, 20), # deep brick red
    Rendezvous = (34, 205, 66), # neon green
    Voyager = (71, 71, 71), # smoggy dark gray
    Journeyman = (123, 249, 206), # mint 
    
    Imperial = (255, 51, 153), # bright pink
    Continental = (100, 149, 237), # light blue
    Wynand = (153, 122, 141), # gray
    Mirage = (211, 57, 238), # magenta
    Panorama = (84, 248, 254) #searing bright blue
  
  @classmethod
  def get_all_colors(cls):
    return [isinstance(attr, tuple) for attr in cls.__dict__.values()] + [isinstance(attr, tuple) for attr in cls.ChainColors.__dict__.values()]
  
  @classmethod
  def colorcount(cls):
    return sum([isinstance(attr, tuple) for attr in cls.__dict__.values()])
  
  @classmethod
  def chaincolorcount(cls):
    return sum([isinstance(attr, tuple) for attr in cls.ChainColors.__dict__.values()])
  
  @classmethod
  def chain(cls, chainname: str) -> tuple[int, int, int]:
    CC = cls.ChainColors
    try:
      chaincolor = CC.__getattribute__(CC, chainname)
    except AttributeError as err:
      print("Invalid ChainColors chainname:", err)
      raise
    return chaincolor

class Fonts:
  main = 'timesnewroman'
  tile = "arial"
  oblivious = r'fonts/oblivious-font.regular.ttf'

def colortest(screen: pygame.Surface, clock: pygame.time.Clock):
  while colorLoop:
    for color in Colors.get_all_colors():
      screen.fill(color)
      pygame.display.flip()
      event = pygame.event.poll()
      if event.type == pygame.QUIT:
        colorLoop = False
        break
      clock.tick(1)

def pack_gameState(tilebag:TileBag, board:Board, players:list[Player], bank:Bank) -> bytes:
  conn_list = [p.conn for p in players]
  for p in players:
    if p.conn is not None and p.conn.sock is not None:
      p._conn = None
  
  # cannot pickle sockets
  objects = (tilebag, board, players, bank)
  gameStateUpdate = pickle.dumps(objects, 5)
  
  for i, p in enumerate(players):
    p._conn = conn_list[i]
  
  return gameStateUpdate

def pack_save(tilebag:TileBag, board:Board, players:list[Player], bank:Bank, currentP:Player = None) -> tuple[bytes, list[str]]:
  if currentP is not None:
    reorderedPlayers = players[players.index(currentP):] + players[:players.index(currentP)]
  else:
    reorderedPlayers = players
  
  saveData = pack_gameState(tilebag, board, reorderedPlayers, bank)
  currentOrderNames = [p.name for p in reorderedPlayers]
  
  return saveData, currentOrderNames

def unpack_gameState(gameState: bytes, localPlayers: list[Player] | None = None) -> tuple[TileBag, Board, list[Player], Bank]:
  objects: tuple[TileBag, Board, list[Player], Bank] = pickle.loads(gameState)
  tilebag, board, players, bank = objects
  
  # re-link internal Tilebags, Boards, Player names, and Connections (if host)
  board.setGameObj(tilebag)
  bank.setGameObj(tilebag, board)
  for p in players:
    p.setGameObj(tilebag, board)
    
    if localPlayers is not None:
      p.conn = find_player(p.uuid, localPlayers).conn
      # host writes valid conns to client and dummy conn to host
      # clients write valid conn to server and None to host
  
  return (tilebag, board, players, bank)

def write_save(saveData: bytes, currentOrderNames: list[str] = None, turnnumber: int = None, quicksave: bool = False):
  date = datetime.date.isoformat(datetime.date.today())
  if quicksave:
    save_file_new = "quicksave"
  else:
    save_file_new = date
    if currentOrderNames is not None:
      save_file_new += f'_{len(currentOrderNames)}players_{"".join(currentOrderNames)}'
    if turnnumber is not None:
      save_file_new += f'_turn{turnnumber}'
  
  if not os.path.exists(rf'{DIR_PATH}\saves\{save_file_new}'):
    with open(rf'{DIR_PATH}\saves\{save_file_new}', 'x') as file:
      pass
  with open(rf'{DIR_PATH}\saves\{save_file_new}', 'wb') as file:
    file.write(saveData)
  return
