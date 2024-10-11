from objects.tilebag import TileBag

class Board:
  def __init__(self, tilebag:TileBag, maxChainSize: int):
    self._tilebag = tilebag
    self.maxChainSize = int(maxChainSize)
    self.debug_tilesinplayorder = []
    self.debug_count = 0
    self.tilesinplay = []
    self.deadducks = set()
    self.chaindict = {}
  
  def fetchchainsize(self, chain: str):
    return sum(chainvalue == chain for chainvalue in self.chaindict.values())
  
  def fetchactivechains(self): #returns a list
    activechains = {chainvalue for chainvalue in self.chaindict.values()}
    activechains = [chain for chain in self._tilebag.chainnames if chain in activechains]
    return activechains
  
  def fetchsmallestchain(self):
    chainsizepairs = [ [chain, self.fetchchainsize(chain)] for chain in self.fetchactivechains()]
    chainsizepairs.sort(key=lambda x: x[1])
    return chainsizepairs[0]
  
  def fetchlargestchain(self):
    chainsizepairs = [ [chain, self.fetchchainsize(chain)] for chain in self.fetchactivechains()]
    chainsizepairs.sort(key=lambda x: x[1])
    return chainsizepairs[-1]
  
  def fetchadjacent(self, tile: str): #tiles in play order may
    tileID = self._tilebag.tilesToIDs([tile])[0]
    adjacentIDs = [tileID - self._tilebag.rows, tileID-1, tileID+1, tileID+self._tilebag.rows]
    adjacent = self._tilebag.tileIDinterp([ID for ID in adjacentIDs if ID >= 0 and ID <= len(self._tilebag.alltiles)-1])
    numbqnt = len([char for char in tile if char in "1234567890"])
    adjacent = [check for check in adjacent if (check[:numbqnt] == tile[:numbqnt] or check[numbqnt:] == tile[numbqnt:])]
    adjinplay = [adj for adj in adjacent if adj in self.tilesinplay]
    return adjinplay
  
  def chainsContained(self, tiles: list[str]):
    tileandchains = [self.chaindict[tile] for i, tile in enumerate(tiles) if tile in self.chaindict]
    tileflavors = list(set(tileandchains))
    return tileflavors
  
  def tileplaymode(self, tile: str, bankdrawn: bool = False):
    adjinplay = self.fetchadjacent(tile)
    connectedChains = self.chainsContained(adjinplay)
    if len(adjinplay) == 0 or (bankdrawn and len(connectedChains) == 0):
      return "place", None
    elif not bankdrawn and len(connectedChains) == 0:
      return "create", None
    elif len(connectedChains) == 1:
      return "expand", connectedChains[0]
    else:
      return "merge", connectedChains
  
  def tileprop(self, tile: str, chainToSpread: str, targetChain: str | None = None, ignoreTile: str | tuple[str] = None):
    #assumes tile has already been set to correct chain, need not be for mid-multimerge propagation
    ignoreTile = ignoreTile[0] if type(ignoreTile) == tuple else ignoreTile
    oldchainsize = self.fetchchainsize(chainToSpread)
    checked = {tile} if ignoreTile is None else {tile, ignoreTile}
    for pairs in self.chaindict.items():
      if pairs[1] == chainToSpread: checked.add(pairs[0])
    unchecked = set( self.fetchadjacent(tile) if targetChain is None else [t for t in self.fetchadjacent(tile) if t in self.chaindict.keys() and self.chaindict[t] == targetChain] )
    while len(unchecked) != 0:
      iterToCheck = []
      for adj in unchecked:
        self.chaindict[adj] = chainToSpread
        iterToCheck.extend( self.fetchadjacent(adj) if targetChain is None else [t for t in self.fetchadjacent(adj) if t in self.chaindict.keys() and self.chaindict[t] == targetChain] )
        checked.add(adj)
      unchecked.update(iterToCheck)
      unchecked.difference_update(checked)
    return self.fetchchainsize(chainToSpread) - oldchainsize #growth of chain (new vs old)
  
  def mergeCart_init(self, chainedonly: list[str]):
    chainsizepairs = [ [self.fetchchainsize(chain), chain] for chain in chainedonly ]
    chainsizepairs.sort(key=lambda x: x[0], reverse=True)
    truthtables = [ [1 if chainsizepairs[i][0] == chainsizepairs[j][0] else 0 for j in range(len(chainsizepairs))] for i in range(len(chainsizepairs)) ]
    matchcount = [sum(table)-1 for table in truthtables]
    chainoptions = [chain[1] for chain in chainsizepairs]
    if not any(matchcount):
      return chainoptions
    mergeCart = [chain if matchcount[chainoptions.index(chain)] == 0 else '' for chain in chainoptions]
    chainoptions = [chain for chain in chainoptions if chain not in mergeCart]
    if matchcount == [1, 1, 1, 1]:
      mergeCart = (mergeCart[:2], mergeCart[2:])
      chainoptions = (chainoptions[:2], chainoptions[2:])
    return (mergeCart, chainoptions) #mergeCart is sorted in order of size
  
  def toobigtofail(self):
    toobig = [self.fetchchainsize(chain) >= 11 for chain in self.fetchactivechains()]
    return toobig if toobig != [] else [False]
  
  def deadduckcheck(self, tile: str):
    adjinplay = self.fetchadjacent(tile)
    connectedChains = self.chainsContained(adjinplay)
    return len([chain for chain in connectedChains if chain in self.toobigtofail()]) > 1
  
  def contraceptcheck(self, tiles: list[str], checkChainAvail: bool = False):
    makeBabies = [False]*len(tiles)
    for i, tile in enumerate(tiles):
      adjinplay = self.fetchadjacent(tile)
      if len(adjinplay) > 0: #is actually touchind something, check if/what chain
        chainedonly = self.chainsContained(adjinplay)
        if len(chainedonly) == 0 and (self.fetchactivechains() == self._tilebag.chainnames if checkChainAvail else True): #would found new chain
          makeBabies[i] = True
    return makeBabies
  
  def endgamecheck(self):
    bigtest = any([self.fetchchainsize(chain) >= self.maxChainSize for chain in self.fetchactivechains()] )
    birthingTilesLeft = self.contraceptcheck(self._tilebag.tileIDinterp(self._tilebag.tilesleft))
    nomovesleft = all(self.toobigtofail()) and not any(birthingTilesLeft)
    return bigtest or nomovesleft
