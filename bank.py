import math
from pregame import tilebag, board, globalStats

class Bank:
  def __init__(self, startingStockNumber = 25,
               sizeCostFunc = "classic", smallSize = 5, largeSize = 41, sizeCostRate = 100, 
               theDadTax = 600, maxSizeCost = 1000, fancyCostRate = 100,
               linMaxFrac = 3/4,
               logMultiplier = 1.5, logBase = 2.6,
               expnDivisor = 240, expnPower = 2, expnMinFrac = 1/3,
               finalCostAdd = 0, finalCostMultiplier = 1):
    #valid sizeCostFunc, from least to most expensive: log, classic, linear, expn
    self.name = 'The Stock Market'
    self.balance = 'Balance: Unlimited'
    self.bal = 0
    self.stocks = {chain: startingStockNumber for chain in tilebag.chainnames}
    # region custom settings args to attributes
    self.sizeCostFunc = sizeCostFunc
    self.smallSize = smallSize
    self.largeSize = largeSize
    self.sizeCostRate = sizeCostRate
    self.theDadTax = theDadTax
    self.maxSizeCost = maxSizeCost
    self.fancyCostRate = fancyCostRate
    self.linMaxFrac = linMaxFrac
    self.logMultiplier = logMultiplier
    self.logBase = logBase
    self.expnDivisor = expnDivisor
    self.expnPower = expnPower
    self.expnMinFrac = expnMinFrac
    self.finalCostAdd = finalCostAdd
    self.finalCostMultiplier = finalCostMultiplier
    # endregion
  
  def stockcost(self, chain, size):
    if size == 0:
      return 0
    
    def classicCost(chain, size):
      if size <= self.smallSize:
        sizecost = self.sizeCostRate*size
      elif size > self.smallSize and size < self.largeSize:
        sizecost = ((size-1)//10)*self.sizeCostRate + self.theDadTax
      else:
        sizecost = self.maxSizeCost
      if chain in tilebag.chainTierGrouped['cheap']:
        fancycost = 0*self.fancyCostRate
      elif chain in tilebag.chainTierGrouped['med']:
        fancycost = 1*self.fancyCostRate
      else:
        fancycost = 2*self.fancyCostRate
      return sizecost + fancycost
  
    def linearCost(chain, size):
      if size <= self.largeSize:
        sizecost = self.sizeCostRate*size + self.theDadTax
      else: 
        sizecost = int(round(min(self.maxCost, self.sizeCostRate*(self.largeSize*self.linMaxFrac) + self.theDadTax), -2))
      if chain in tilebag.chainTierGrouped['cheap']:
        fancycost = 0*self.fancyCostRate
      elif chain in tilebag.chainTierGrouped['med']:
        fancycost = 1*self.fancyCostRate
      else:
        fancycost = 2*self.fancyCostRate
      return int(round(sizecost + fancycost, -2))
  
    def logCost(chain, size):
      return round(math.log(self.logMultiplier*linearCost(chain, size), self.logBase)*100, -2)
    
    def squareCost(chain, size):
      return round(((linearCost(chain, size)//self.expnDivisor)**self.expnPower)*100, -2) + (self.theDadTax*self.expnMinFrac)
  
    if self.sizeCostFunc == "linear": 
       costFunc = linearCost
    elif self.sizeCostFunc == "log": 
      costFunc = logCost
    elif self.sizeCostFunc == "expn": 
      costFunc = squareCost
    else:
      costFunc = classicCost
    return costFunc(chain, size) * self.finalCostMultiplier + self.finalCostAdd

  def fetchcheapeststock(self):
    chaincostpair = [ [chain, self.stockcost(chain, board.fetchchainsize(chain))] for chain in board.fetchactivechains()]
    chaincostpair.sort(key=lambda x: x[1])
    return chaincostpair[0]
  
  def chainpayout(self, players, defunctchains):
    statementsList = []
    for chain in defunctchains:
      chainsize = board.fetchchainsize(chain)
      stockstats = [ [p, p.stocks[chain] ] for p in players if p.stocks[chain] > 0]
      if len(players) < 3: 
        bankstocktileID = tilebag.drawtile()
        bankstocks = bankstocktileID // tilebag.rows + 1
        bankdrawntile = tilebag.tileIDinterp([bankstocktileID])[0]
        globalStats.bankTilesDrawn[-1] += 1
        bankStatement = f'The Bank drew {bankdrawntile}, which means it holds {bankstocks} stocks in {chain}.'
        stockstats.append([self, bankstocks])
      else:
        bankdrawntile = None
        bankStatement = None
      stockstats.sort(key=lambda x: x[1], reverse=True)
      firstprize = self.stockcost(chain, chainsize)*10
      secondprize = int(firstprize/2)
      firstplace = stockstats[0][1]
      if len(stockstats) == 1: #only one person holding stock in merging chain
        stockstats[0][0].bal = stockstats[0][0].bal + (firstprize + secondprize)
        firstStatement = f'{stockstats[0][0].name} holds all stock in {chain} and has earned ${firstprize + secondprize}!'
        secondStatement = None
      else:
        tiecheck1 = sum([trifold[1] == firstplace for trifold in stockstats])
        if tiecheck1 > 1:
          firstprize = math.ceil( ((firstprize + secondprize)/tiecheck1)/100 )*100
          winnerlist = []
          for i in range(tiecheck1): 
            stockstats[i][0].bal = stockstats[i][0].bal + firstprize
            winnerlist.append(stockstats[i][0].name)
          ', '.join(winnerlist)
          firstStatement = f'{", ".join(winnerlist)} hold Majority in {chain} and have earned ${firstprize} each!'
          secondStatement = None
        else:
          firstStatement = f'{stockstats[0][0].name} holds Majority in {chain} and has earned ${firstprize}!'
          stockstats[0][0].bal = stockstats[0][0].bal + firstprize
          secondplace = stockstats[1][1]
          tiecheck2 = sum(trifold[1] == secondplace for trifold in stockstats)
          if tiecheck2 > 1:
            secondprize = math.ceil( (secondprize/tiecheck2)/100 )*100
            winnerlist = []
            for i in range(tiecheck2):
              stockstats[i+1][0].bal = stockstats[i+1][0].bal + secondprize
              winnerlist.append(stockstats[i+1][0].name)
            ', '.join(winnerlist)
            secondStatement = f'{", ".join(winnerlist)} hold Second Majority in {chain} and have earned ${secondprize} each!'
          else:
            secondStatement = f'{stockstats[1][0].name} holds Second Majority in {chain} and has earned ${secondprize}!'
            stockstats[1][0].bal = stockstats[1][0].bal + secondprize
      statementsList.append((bankStatement, firstStatement, secondStatement))
        
    return bankdrawntile, statementsList

  def playtile(self, tile): #tile must be playable!
    board.debug_tilesinplayorder.append(tile)
    sortactiveIDs = tilebag.tilesToIDs(board.debug_tilesinplayorder)
    sortactiveIDs.sort()
    board.tilesinplay = tilebag.tileIDinterp(sortactiveIDs)
    return None
