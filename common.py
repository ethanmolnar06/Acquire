import datetime
import os
import pickle
import pygame
from copy import deepcopy
from uuid import UUID

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

def find_player(uuid: UUID, players: list[Player]) -> Player:
  # i know this is less efficient than making players a dict[UUID, Player],
  # but it integrates easier into current gameloops so idc
  for p in players:
    if p.uuid == uuid or (p.conn is not None and p.conn.uuid == uuid):
      return p

def pack_gameState(tilebag:TileBag, board:Board, players:list[Player], bank:Bank) -> bytes:
  freshPlayers = deepcopy(players)
  for p in freshPlayers:
    if p.conn is not None and p.conn.addr != "host":
      p.conn = None
  
  objects = (tilebag, board, freshPlayers, bank)
  gameStateUpdate = pickle.dumps(objects, 5)
  
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
  board.tilebag = tilebag
  bank.tilebag = tilebag
  bank.board = board
  for p in players:
    p.name = p.falsename if HIDE_PERSONAL_INFO else p.truename
    p.tilebag = tilebag
    p.board = board
    
    if localPlayers is not None:
      p.conn = find_player(p.uuid, localPlayers).conn
      # host writes valid conns to client and dummy conn to host
      # clients write valid conn to server and None to host
  
  return (tilebag, board, players, bank)

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
