from pregame import tilebag

class Stats:
  def __init__(self, startingStockNumber = 0, startCash = 6000, globalStats = False):
    self.moneySpent = [0]
    self.chainsFounded = [0]
    self.stocksAcquired = [0]
    self.stocksTradedAway = [0] 
    self.stocksSold = [0]
    self.mergersMade = [0]
    self.mostExpandedChain = {chain: [0] for chain in tilebag.chainnames}
    self.deadDucksTrashed = [0]
    if not globalStats:
      self.stockChainsOwned = [set()]
      self.bal = [startCash]
      self.stocks = {chain: [startingStockNumber] for chain in tilebag.chainnames}
    else:
      self.turnCounter = [0]
      self.bankTilesDrawn = [0]

def assignStatVals(players):
  for p in players:
    p.stats.bal[-1] = p.bal
    for chain in p.stats.stocks.keys():
      p.stats.stocks[chain] += [p.stocks[chain]]
  return None
  
def statIncrement(players):
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
