import operator
import uuid
from typing import Self
from copy import deepcopy

from objects.tilebag import TileBag
from objects.board import Board
from objects.stats import Stats
from objects.connection import Connection

class Player:
  def __init__(self, tilebag: TileBag, board: Board, name: str, creation_n: int,
               startingStockNumber: int = 0, startCash: int = 6000, tileQuant: int = 6, maxPlayers = 6):
    self.setGameObj(tilebag, board)
    self.maxPlayers = maxPlayers
    self.name = (name, creation_n)
    
    self.uuid: uuid.UUID = uuid.uuid4()
    self.conn: Connection | None = Connection("host", None, self.uuid)
    self.connClaimed: bool = True
    self.ready: bool = False
    
    self.tiles: list[str] = []
    self.tileQuant = int(tileQuant)
    self.bal = round(int(startCash), -2)
    self.stocks: dict[str, int] = {chain: int(startingStockNumber) for chain in tilebag.chainnames}
    self.stats = Stats(tilebag.chainnames, int(startingStockNumber), self.bal)
  
  def __str__(self) -> str:
    return f"{self.name} ({self.uuid}) <{id(self)}>"
  
  @property
  def name(self) -> str:
    from common import HIDE_PERSONAL_INFO
    return self._falsename if HIDE_PERSONAL_INFO else self._truename
  
  @name.setter
  def name(self, nametup: tuple[str, int]):
    self._truename = nametup[0]
    self._falsename: str = f"Player {nametup[1]}"
    self.connClaimed: bool = True
    self.ready: bool = False
  
  @property
  def conn(self) -> Connection:
    return self._conn
  
  @conn.setter
  def conn(self, conn: Connection | None):
    self._conn = conn
    self.ready = False
    if conn is not None:
      self.connClaimed = True
      self.uuid = conn.uuid
    else:
      self.connClaimed = False
      self.uuid = uuid.uuid4()
  
  def copy(self) -> Self:
    CONN = self._conn
    self._conn = None
    newplayer = deepcopy(self)
    self._conn = CONN
    newplayer.setGameObj(self._tilebag, self._board)
    return newplayer
  
  def syncSendDISCONN(self, inResponse: bool = False):
    if self.conn is not None:
      self.conn.syncSendDISCONN(inResponse)
  
  def setGameObj(self, tilebag: TileBag, board: Board):
    self._tilebag = tilebag
    self._board = board
  
  def _updateTileList(self, newtileID: int):
    oldtileIDs = self._tilebag.tilesToIDs(self.tiles)
    oldtileIDs.append(newtileID)
    oldtileIDs.sort()
    self.tiles = self._tilebag.tileIDinterp(oldtileIDs) #stored as human name string, **NOT ID as int**
  
  def drawtile(self, n: int = 1):
    for i in range(n):
      newtileID = self._tilebag.drawtile()
      if newtileID is not None: 
        self._updateTileList(newtileID)
  
  def playtile(self, tile: str): #tile must be playable!
    self.tiles.remove(tile)
    self._board._play_tile(tile)
    return None
  
  def returntile(self, tile: str):
    self.tiles.remove(tile)
    self._tilebag.returntile(tile)
  
  def swapnexttile(self, tile: str, prev: bool = False):
    newtileID = self._tilebag.nexttile(tile, prev)
    self._updateTileList(newtileID)
  
  def deadduckremoval(self):
    checked = set()
    unchecked = set(self.tiles)
    while len(unchecked) != 0:
      for tile in unchecked:
        if self._board.deadduckcheck(tile):
          self.tiles.remove(tile)
          self.stats.deadDucksTrashed[-1] += 1
          self.drawtile()
        checked.add(tile)
      unchecked = set(self.tiles)
      unchecked.difference_update(checked)
    return None

def find_player(uuid: uuid.UUID, players: list[Player]) -> Player:
  # i know this is less efficient than making players a dict[UUID, Player],
  # but it integrates easier into current gameloops so idc
  for p in players:
    if p.uuid == uuid or (p.conn is not None and p.conn.uuid == uuid):
      return p
  raise LookupError(f"No Player of uuid [{uuid}] found!")

def setPlayerOrder(tilebag: TileBag, board: Board, players: list[Player]):
  order = []
  for p in players:
    gamestarttileID = tilebag.drawtile()
    gamestarttile = tilebag.tileIDinterp([gamestarttileID])
    board._tilesinplayorder.append(gamestarttile[0])
    # print(f'{name} drew {gamestarttile[0]}!')
    order.append((p, gamestarttile))
  
  players = [tup[0] for tup in sorted(order, key=operator.itemgetter(1))]
  
  for p in players:
    p.drawtile(p.tileQuant)
  sortactiveIDs = tilebag.tilesToIDs(board._tilesinplayorder)
  sortactiveIDs.sort()
  board.tilesinplay = tilebag.tileIDinterp(sortactiveIDs)
 
  return players

def assignStatVals(players: list[Player]):
  for p in players:
    p.stats.bal[-1] = p.bal
    for chain in p.stats.stocks.keys():
      p.stats.stocks[chain] += [p.stocks[chain]]
  return None

def statIncrement(players: list[Player]):
  for p in players:
    for k, v in p.stats.__dict__.items():
      if k not in ('stocks', 'mostExpandedChain'):
        setattr(p.stats, k, v + [v[-1]])
      elif k == "stocks":
        for chain in p.stats.stocks.keys():
          p.stats.stocks[chain] += [p.stats.stocks[chain][-1]]
      elif k == 'mostExpandedChain':
        for chain in p.stats.mostExpandedChain.keys():
          p.stats.mostExpandedChain[chain] += [p.stats.mostExpandedChain[chain][-1]]
  return None
