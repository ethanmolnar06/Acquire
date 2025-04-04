from objects.tilebag import TileBag

class Board:
  def __init__(self, tilebag:TileBag, maxChainSize: int):
    self.setGameObj(tilebag)
    self.maxChainSize = int(maxChainSize)
    self._tilesinplayorder = []
    self.tilesinplay = []
    self.deadducks = set()
    self.chaindict = {}
  
  def setGameObj(self, tilebag: TileBag):
    self._tilebag = tilebag
  
  def _play_tile(self, tile: str, remove: bool = False):
    if remove:
      self._tilesinplayorder.remove(tile)
    else:
      self._tilesinplayorder.append(tile)
    sortactiveIDs = self._tilebag.tilesToIDs(self._tilesinplayorder)
    sortactiveIDs.sort()
    self.tilesinplay = self._tilebag.tileIDinterp(sortactiveIDs)
  
  def fetchchainsize(self, chain: str) -> int:
    return sum(chainvalue == chain for chainvalue in self.chaindict.values())
  
  def fetchactivechains(self, inv: bool = False) -> list[str]: #returns an ordered list
    activechainset = {chainvalue for chainvalue in self.chaindict.values()}
    if not inv:
      activechains = [chain for chain in self._tilebag.chainnames if chain in activechainset]
    else:
      activechains = [chain for chain in self._tilebag.chainnames if chain not in activechainset]
    return activechains
  
  def fetchsmallestchain(self, inv: bool = False) -> list[str, int]:
    chainsizepairs = [ [chain, self.fetchchainsize(chain)] for chain in self.fetchactivechains()]
    chainsizepairs.sort(key=lambda x: x[1])
    return chainsizepairs[0 if not inv else -1]
  
  def fetchadjacent(self, tile: str): #tiles in play order may
    tileID = self._tilebag.tilesToIDs([tile])[0]
    adjacentIDs = [tileID - self._tilebag.rows, tileID - 1, tileID + 1, tileID + self._tilebag.rows]
    filtered = [ID for ID in adjacentIDs if ID >= 0 and ID < len(self._tilebag.alltiles)]
    adjacent = self._tilebag.tileIDinterp([ID for ID in filtered if (ID % self._tilebag.rows - tileID % self._tilebag.rows) in {-1, 0, 1}])
    adjinplay = [adj for adj in adjacent if adj in self.tilesinplay]
    return adjinplay
  
  def fetchchainsgrouped(self, chain_subset : list[str] | None = None, invert_subset: bool = False) -> list[list[str]]:
    if not chain_subset:
      chain_subset = self.fetchactivechains()
    if invert_subset:
      chain_subset = [chain for chain in self._tilebag.chainnames if chain not in chain_subset]
    
    chaingroup1 = [chain for chain in chain_subset if chain in self._tilebag.chainTierGrouped['cheap']]
    chaingroup2 = [chain for chain in chain_subset if chain in self._tilebag.chainTierGrouped['med']]
    chaingroup3 = [chain for chain in chain_subset if chain in self._tilebag.chainTierGrouped['high']]
    return [group for group in [chaingroup1, chaingroup2, chaingroup3] if len(group) > 0]
  
  def chainsContained(self, tiles: list[str]) -> list[str]:
    return list({self.chaindict[tile] for tile in tiles if tile in self.chaindict})
  
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
  
  def tileprop(self, tile: str, chainToSpread: str, victimChain: str | None = None, ignoreTile: str | tuple[str] | None = None):
    #assumes tile has already been set to correct chain, need not be for mid-multimerge propagation
    ignoreTile = ignoreTile[0] if isinstance(ignoreTile, tuple) else ignoreTile
    oldchainsize = self.fetchchainsize(chainToSpread)
    checked = {tile} if ignoreTile is None else {tile, ignoreTile}
    for pairs in self.chaindict.items():
      if pairs[1] == chainToSpread: checked.add(pairs[0])
    unchecked = set( self.fetchadjacent(tile) if victimChain is None else [t for t in self.fetchadjacent(tile) if t in self.chaindict.keys() and self.chaindict[t] == victimChain] )
    while len(unchecked) != 0:
      iterToCheck = []
      for adj in unchecked:
        self.chaindict[adj] = chainToSpread
        iterToCheck.extend( self.fetchadjacent(adj) if victimChain is None else [t for t in self.fetchadjacent(adj) if t in self.chaindict.keys() and self.chaindict[t] == victimChain] )
        checked.add(adj)
      unchecked.update(iterToCheck)
      unchecked.difference_update(checked)
    return self.fetchchainsize(chainToSpread) - oldchainsize #growth of chain (new vs old)
  
  def mergeCart_init(self, chainedonly: list[str]) -> list[str] | tuple[list[str], list[str]]:
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
    return (mergeCart, chainoptions) # mergeCart is sorted in order of size
  
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
      if len(adjinplay) > 0: # is actually touching something, check if/what chain
        chainedonly = self.chainsContained(adjinplay)
        if len(chainedonly) == 0 and (self.fetchactivechains() == self._tilebag.chainnames if checkChainAvail else True): # would found new chain
          makeBabies[i] = True
    return makeBabies
  
  def endgamecheck(self):
    bigtest = any([self.fetchchainsize(chain) >= self.maxChainSize for chain in self.fetchactivechains()] )
    birthingTilesLeft = self.contraceptcheck(self._tilebag.tileIDinterp(self._tilebag.tilesleft))
    nomovesleft = all(self.toobigtofail()) and not any(birthingTilesLeft)
    return bigtest or nomovesleft
