from pregame import tilebag, board
from objects.stats import Stats

class Player:
  def __init__(self, name: str, startingStockNumber: int = 0, startCash: int = 6000, tileQuant: int = 6, maxPlayers = 6):
    self.name = name
    self.tiles = []
    self.tileQuant = int(tileQuant)
    self.bal = round(int(startCash), -2)
    self.stocks = {chain: int(startingStockNumber) for chain in tilebag.chainnames}
    self.stats = Stats(int(startingStockNumber), self.bal)
  
  def drawtile(self, n: int = 1):
    for i in range(n):
      newtileID = tilebag.drawtile()
      if newtileID is not None: 
        oldtileIDs = tilebag.tilesToIDs(self.tiles)
        oldtileIDs.append(newtileID)
        oldtileIDs.sort(key=int)
        self.tiles = tilebag.tileIDinterp(oldtileIDs) #stored as human name string, **NOT ID as int**
      # else: print('Tilebag Empty!')
    return None
  
  def playtile(self, tile: str): #tile must be playable!
    self.tiles.remove(tile)
    board.debug_tilesinplayorder.append(tile)
    sortactiveIDs = tilebag.tilesToIDs(board.debug_tilesinplayorder)
    sortactiveIDs.sort()
    board.tilesinplay = tilebag.tileIDinterp(sortactiveIDs)
    return None
  
  def deadduckremoval(self):
    checked = set()
    unchecked = set(self.tiles)
    while len(unchecked) != 0:
      for tile in unchecked:
        if board.deadduckcheck(tile):
          self.tiles.remove(tile)
          self.stats.deadDucksTrashed[-1] += 1
          self.drawtile()
        checked.add(tile)
      unchecked = set(self.tiles)
      unchecked.difference_update(checked)
    return None

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