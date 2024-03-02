from pregame import tilebag

class Board:
  def __init__(self):
    self.debug_tilesinplayorder = []
    self.debug_count = 0
    self.tilesinplay = []
    self.deadducks = set()
    self.chaindict = {}

  def fetchadjacent(self, tile): #tiles in play order may
    tileID = tilebag.tilesToIDs([tile])[0]
    adjacentIDs = [tileID - tilebag.rows, tileID-1, tileID+1, tileID+tilebag.rows]
    adjacent = tilebag.tileIDinterp([ID for ID in adjacentIDs if ID >= 0 and ID <= len(tilebag.alltiles)-1])
    numbqnt = len([char for char in tile if char in "1234567890"])
    adjacent = [check for check in adjacent if (check[:numbqnt] == tile[:numbqnt] or check[numbqnt:] == tile[numbqnt:])]
    adjinplay = [adj for adj in adjacent if adj in self.tilesinplay]
    return adjinplay

  def fetchchainsize(self, chain):
    return sum(chainvalue == chain for chainvalue in self.chaindict.values())

  def fetchactivechains(self): #returns a list
    activechains = {chainvalue for chainvalue in self.chaindict.values()}
    activechains = [chain for chain in tilebag.chainnames if chain in activechains]
    return activechains

  def fetchsmallestchain(self):
    chainsizepairs = [ [chain, self.fetchchainsize(chain)] for chain in tilebag.chainnames]
    chainsizepairs.sort(key=lambda x: x[1])
    return chainsizepairs[0]

  def chainsContained(self, tiles):
    tileandchains = [self.chaindict[tile] for i, tile in enumerate(tiles) if tile in self.chaindict]
    tileflavors = list(set(tileandchains))
    return tileflavors

  def tileprop(self, tile, chainToSpread, targetChain = None, ignoreTile = None): #assumes tile has already been set to correct chain, need not be for mid-multimerge propagation
    ignoreTile = ignoreTile[0] if type(ignoreTile) == tuple else ignoreTile
    oldchainsize = self.fetchchainsize(chainToSpread)
    checked = {tile} if ignoreTile == None else {tile, ignoreTile}
    for pairs in self.chaindict.items():
      if pairs[1] == chainToSpread: checked.add(pairs[0])
    unchecked = set( self.fetchadjacent(tile) if targetChain == None else [t for t in self.fetchadjacent(tile) if t in self.chaindict.keys() and self.chaindict[t] == targetChain] )
    while len(unchecked) != 0:
      iterToCheck = []
      for adj in unchecked:
        self.chaindict[adj] = chainToSpread
        iterToCheck.extend( self.fetchadjacent(adj) if targetChain == None else [t for t in self.fetchadjacent(adj) if t in self.chaindict.keys() and self.chaindict[t] == targetChain] )
        checked.add(adj)
      unchecked.update(iterToCheck)
      unchecked.difference_update(checked)
    return self.fetchchainsize(chainToSpread) - oldchainsize #growth of chain (new vs old)
  
  def mergeCart_init(self, tile, chainedonly):
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

  def deadduckcheck(self, p, bankdrawntile = None):
    if bankdrawntile != None:
      adjinplay = self.fetchadjacent(bankdrawntile)
      connectedChains = self.chainsContained(adjinplay)
      if len([chain for chain in connectedChains if chain in self.toobigtofail()]) > 1:
        return True
      return (adjinplay, connectedChains)
    checked = set()
    unchecked = set(p.tiles)
    while len(unchecked) != 0:
      for tile in unchecked:
        adjinplay = self.fetchadjacent(tile)
        connectedChains = self.chainsContained(adjinplay)
        if len([chain for chain in connectedChains if chain in self.toobigtofail()]) > 1:
          p.tiles.remove(tile)
          p.stats.deadDucksTrashed[-1] += 1
          print(f'{p.name} had the newly dead duck tile {tile}, and will now draw a new tile.')
          p.drawtile()
        checked.add(tile)
      unchecked = set(p.tiles)
      unchecked.difference_update(checked)
    return None

  def contraceptcheck(self, tiles, checkChainAvail = False):
    makeBabies = [False]*len(tiles)
    for i, tile in enumerate(tiles):
      adjinplay = self.fetchadjacent(tile)
      if len(adjinplay) > 0: #is actually touchind something, check if/what chain
        chainedonly = self.chainsContained(adjinplay)
        if len(chainedonly) == 0 and (self.fetchactivechains() == tilebag.chainnames if checkChainAvail else True): #would found new chain
          makeBabies[i] = True
    return makeBabies
  
  def endgamecheck(self):
    bigtest = any([self.fetchchainsize(chain) >= 41 for chain in self.fetchactivechains()] )
    birthingTilesLeft = self.contraceptcheck(tilebag.tileIDinterp(tilebag.tilesleft))
    nomovesleft = all(self.toobigtofail()) and not any(birthingTilesLeft)
    return bigtest or nomovesleft
