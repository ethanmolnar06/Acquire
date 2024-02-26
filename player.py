from pregame import tilebag, board
from stats import Stats

class Player:
  def __init__(self, name, startingStockNumber = 0, startCash = 6000, tileQuant = 6):
    self.name = name
    self.tiles = []
    self.tileQuant = tileQuant
    self.bal = startCash
    self.stocks = {chain: startingStockNumber for chain in tilebag.chainnames}
    self.stats = Stats(startingStockNumber, startCash)

  def drawtile(self, n = 1):
    for i in range(n):
      newtileID = tilebag.drawtile()
      if newtileID != None: 
        oldtileIDs = tilebag.tilesToIDs(self.tiles)
        oldtileIDs.append(newtileID)
        oldtileIDs.sort(key=int)
        self.tiles = tilebag.tileIDinterp(oldtileIDs) #stored as human name string, **NOT ID as int**
      # else: print('Tilebag Empty!')
    return None

  def playtile(self, tile): #tile must be playable!
    self.tiles.remove(tile)
    board.debug_tilesinplayorder.append(tile)
    sortactiveIDs = tilebag.tilesToIDs(board.debug_tilesinplayorder)
    sortactiveIDs.sort()
    board.tilesinplay = tilebag.tileIDinterp(sortactiveIDs)
    return None