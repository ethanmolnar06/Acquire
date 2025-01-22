class Stats:
  def __init__(self, chainnames: list[str], startingStockNumber: int = 0, startCash: int = 6000, globalStats: bool = False):
    self.moneySpent = [0]
    self.chainsFounded = [0]
    self.stocksAcquired = [0]
    self.stocksTradedAway = [0] 
    self.stocksSold = [0]
    self.mergersMade = [0]
    self.mostExpandedChain = {chain: [0] for chain in chainnames}
    self.deadDucksTrashed = [0]
    if not globalStats:
      self.stockChainsOwned = [set()]
      self.bal = [int(startCash)]
      self.stocks = {chain: [int(startingStockNumber)] for chain in chainnames}
    else:
      self.turnCounter = [0]
      self.bankTilesDrawn = [0]
