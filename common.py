import os
import sys
import pickle
import pygame
import pkgutil
import json
from datetime import date
from uuid import UUID

from objects import *
from objects.networking import extrctConns, propagate

class DefaultConfig:
  # GLOBAL GAME PERMISSIONS
  HIDE_PERSONAL_INFO: bool = False
  ALLOW_SAVES: bool = True
  ALLOW_QUICKSAVES: bool = True
  VARIABLE_FRAMERATE: bool = True
  MAX_FRAMERATE: int = 120
  # MULTIPLAYER
  ALLOW_REJOIN: bool = True
  ALLOW_PUBLIC_IP: bool = True
  ALLOW_REVERSE_PROXY: bool = False
  PRINT_NETWORKING_DEBUG: bool = False
  PRINT_PROXY_DEBUG: bool = False

class CONFIG(DefaultConfig):
  NO_RENDER_EVENTS = {0, 770, 1024, 1027,
                    32768, 32783, 32784, 32785, 32786, 32770}
  DIR_PATH = os.path.realpath(os.curdir)
  SAVES_PATH = os.path.join(DIR_PATH, 'saves')
  if not os.path.exists(SAVES_PATH):
    os.makedirs(SAVES_PATH, exist_ok=True)
  CONFIG_PATH = os.path.join(DIR_PATH, 'config.json')
  
  @classmethod
  def load(cls):
    if not os.path.exists(cls.CONFIG_PATH):
      with open(cls.CONFIG_PATH, 'x') as file:
        json.dump({k: v for k, v in DefaultConfig.__dict__.items() if "__" not in k}, file)
    
    try:
      with open(cls.CONFIG_PATH, 'r') as file:
        cls._config_data: dict = json.load(file)
        for k, v in cls._config_data.items():
          setattr(cls, k, v)
    except json.JSONDecodeError as e:
      print(f"[CONFIG ERROR] Error Decoding config.json @ {cls.CONFIG_PATH}")
      sys.exit(1)

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
    if not chainname:
      return None
    CC = cls.ChainColors
    try:
      chaincolor = CC.__getattribute__(CC, chainname)
    except AttributeError as err:
      print("Invalid ChainColors chainname:", err)
      raise
    return chaincolor

class Fonts:
  try: # for pyinstaller version
    fontspath: str = pkgutil.resolve_name("fonts").__path__[0]
  except Exception as e:
    fontspath: str = r".\assets\fonts"
  main = os.path.join(fontspath, 'timesnewroman.ttf')
  tile = os.path.join(fontspath, 'arial_narrow.ttf')
  oblivious = os.path.join(fontspath, 'oblivious.ttf')

def iter_flatten(iterable: list) -> list:
  flattened = []
  for item in iterable:
    if isinstance(item, (list, tuple)):
      flattened.extend(iter_flatten(item))
    else:
      flattened.append(item)
  return flattened

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

def overflow_update(u: list[tuple[UUID, Command]], u_overflow: list[tuple[UUID, Command]], update: tuple[UUID, Command] | None = None):
  # send to self as update
  # try to be super safe, not drop any updates in either queue
  if update is not None:
    u_overflow.append(update)
  u_overflow = u_overflow.extend(u)
  u.clear()

def overflow(u_overflow: list[tuple[UUID, Command]]) -> list[tuple[UUID, Command]]:
  u = u_overflow.copy()
  u_overflow.clear()
  return u

def pack_gameState(tilebag:TileBag, board:Board, players:list[Player], bank:Bank) -> bytes:
  conn_list = [p.conn for p in players]
  for p in players:
    # send actual connections as None, self as dummy "host"/"client", others as None
    if p.conn is not None and p.conn.sock is not None:
      p._conn = None
  
  # cannot pickle sockets
  objects = (tilebag, board, players, bank)
  gameStateUpdate = pickle.dumps(objects, 5)
  
  for i, p in enumerate(players):
    p._conn = conn_list[i]
  
  return gameStateUpdate

def unpack_gameState(gameState: bytes, currentConns: dict[UUID, Connection] | list[Player] | None = None) -> tuple[TileBag, Board, list[Player], Bank]:
  objects: tuple[TileBag, Board, list[Player], Bank] = pickle.loads(gameState)
  tilebag, board, players, bank = objects
  
  # re-link internal Tilebags, Boards
  board.setGameObj(tilebag)
  bank.setGameObj(tilebag, board)
  
  # re-link internal  Player names, and Connections
  if currentConns is not None:
    conns = extrctConns(currentConns)
    conn_uuids = {conn.uuid for conn in conns}
    if isinstance(currentConns, dict):
      def getConn(uuid):
        return currentConns[uuid]
    elif isinstance(currentConns, list):
      def getConn(uuid):
        return find_player(uuid, currentConns).conn
  
  for p in players:
    # print(f"unpacking {p.name} {p.conn}")
    p.setGameObj(tilebag, board)
    if currentConns is not None and p.uuid in conn_uuids:
      # host writes valid conns to clients and dummy to self
      # clients write valid conn to host, dummy to self, and leaves None on other clients
      p._conn = getConn(p.uuid)
      # print(f"overwrote {p.name} with {p.conn}")
  # print("unpack complete")
  
  return (tilebag, board, players, bank)

def write_save(saveData: bytes, playernames: list[str] = None, turnnumber: int = None, quicksave: bool = False, levelEditor: bool = False):
  today = date.isoformat(date.today())
  if quicksave:
    save_file_new = "quicksave"
  else:
    save_file_new = today
    if playernames is not None:
      save_file_new += f'_{len(playernames)}players_{"".join(playernames)}'
    if levelEditor:
      save_file_new += f'_customboard'
    if turnnumber is not None:
      save_file_new += f'_turn{turnnumber}'
  
  save_folder = os.path.join(CONFIG.DIR_PATH, "saves")
  if not os.path.exists(save_folder):
    os.makedirs(save_folder)
  
  save_path = os.path.join(save_folder, save_file_new)
  if not os.path.exists(save_path):
    with open(save_path, 'x') as file:
      pass
  with open(save_path, 'wb') as file:
    file.write(saveData)
  return

def send_gameStateUpdate(tilebag, board, players, bank, clientMode, source: UUID | None = None):
  if clientMode == "hostLocal":
    return
  gameStateUpdate = pack_gameState(tilebag, board, players, bank)
  target = "client" if clientMode == "hostServer" else "server"
  propagate(players, source, Command(f"set {target} gameState", gameStateUpdate))
