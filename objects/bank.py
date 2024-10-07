import math
from objects.tilebag import TileBag
from objects.board import Board
from objects.player import Player
from objects.stats import Stats

class Bank:
  def __init__(self, tilebag: TileBag, board:Board,
               startingStockNumber: int = 25, finalCostAdd: float = 0., finalCostMultiplier: float = 1.,
               sizeCostFunc = "Classic", sizeCostRate: float = 100., fancyCostRate: float = 100., largeSize: int = 41, 
               smallSize: int = 5, 
               theDadTax: float = 600.,
               logMultiplier: float = 1.5, logBase: float = 2.6,
               expnDivisor: float = 240., expnPower: float = 2., expnOffsetReduc: float = 3.,
               ):
    #valid sizeCostFunc, from least to most expensive: Logarithmic, Classic, Linear, Exponential
    self.tilebag = tilebag
    self.board = board
    self.name = 'The Stock Market'
    self.balance = 'Balance: Unlimited'
    self.bal = 0
    self.stocks = {chain: int(startingStockNumber) for chain in tilebag.chainnames}
    self.stats = Stats(tilebag.chainnames, int(startingStockNumber), self.bal, True)
    # region custom settings args to attributes
    self.sizeCostFunc = sizeCostFunc
    self.smallSize = int(smallSize)
    self.largeSize = int(largeSize)
    self.sizeCostRate = float(sizeCostRate)
    self.theDadTax = float(theDadTax)
    self.fancyCostRate = float(fancyCostRate)
    self.logMultiplier = float(logMultiplier)
    self.logBase = float(logBase)
    self.expnDivisor = float(expnDivisor)
    self.expnPower = float(expnPower)
    self.expnOffsetReduc = float(expnOffsetReduc)
    self.finalCostAdd = float(finalCostAdd)
    self.finalCostMultiplier = float(finalCostMultiplier)
    # endregion
  
  def stockcost(self, chain: str, size: int):
    if size == 0:
      return 0
    
    def classicCost(chain, size):
      if size <= self.smallSize:
        sizecost = self.sizeCostRate*size
      else:
        sizecost = ((size - self.smallSize + 4)//10 + self.smallSize + 1)*self.sizeCostRate
      
      if chain in self.tilebag.chainTierGrouped['cheap']:
        fancycost = 0*self.fancyCostRate
      elif chain in self.tilebag.chainTierGrouped['med']:
        fancycost = 1*self.fancyCostRate
      else:
        fancycost = 2*self.fancyCostRate
      return sizecost + fancycost
    
    def linearCost(chain, size):
      sizecost = self.sizeCostRate*size + self.theDadTax
      
      if chain in self.tilebag.chainTierGrouped['cheap']:
        fancycost = 0*self.fancyCostRate
      elif chain in self.tilebag.chainTierGrouped['med']:
        fancycost = 1*self.fancyCostRate
      else:
        fancycost = 2*self.fancyCostRate
      return sizecost + fancycost
    
    def logCost(chain, size):
      return math.log(self.logMultiplier*linearCost(chain, size), self.logBase)*100
    
    def squareCost(chain, size):
      return ((linearCost(chain, size)//self.expnDivisor)**self.expnPower)*100 + self.theDadTax / self.expnOffsetReduc
    
    if self.sizeCostFunc == "Linear": 
       costFunc = linearCost
    elif self.sizeCostFunc == "Logarithmic": 
      costFunc = logCost
    elif self.sizeCostFunc == "Exponential": 
      costFunc = squareCost
    else:
      costFunc = classicCost
    
    realCost = costFunc(chain, size) * self.finalCostMultiplier + self.finalCostAdd
    maxCost = costFunc(chain, self.largeSize) * self.finalCostMultiplier + self.finalCostAdd
    return int(round(min(maxCost, realCost), -2))
  
  def fetchcheapeststock(self):
    chaincostpair = [ [chain, self.stockcost(chain, self.board.fetchchainsize(chain))] for chain in self.board.fetchactivechains()]
    chaincostpair.sort(key=lambda x: x[1])
    return chaincostpair[0]
  
  def chainpayout(self, players: list[Player], defunctchains: list[str]):
    # adds payout directly to players' balance internally
    statementsList = []
    for chain in defunctchains:
      chainsize = self.board.fetchchainsize(chain)
      stockstats = [ [p, p.stocks[chain] ] for p in players if p.stocks[chain] > 0]
      if len(players) < 3: 
        bankstocktileID = self.tilebag.drawtile()
        bankstocks = bankstocktileID // self.tilebag.rows + 1
        bankdrawntile = self.tilebag.tileIDinterp([bankstocktileID])[0]
        self.stats.bankTilesDrawn[-1] += 1
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
            stockstats[i][0].bal += firstprize
            winnerlist.append(stockstats[i][0].name)
          ', '.join(winnerlist)
          firstStatement = f'{", ".join(winnerlist)} hold Majority in {chain} and have earned ${firstprize} each!'
          secondStatement = None
        else:
          firstStatement = f'{stockstats[0][0].name} holds Majority in {chain} and has earned ${firstprize}!'
          stockstats[0][0].bal += firstprize
          secondplace = stockstats[1][1]
          tiecheck2 = sum(trifold[1] == secondplace for trifold in stockstats)
          if tiecheck2 > 1:
            secondprize = math.ceil( (secondprize/tiecheck2)/100 )*100
            winnerlist = []
            for i in range(tiecheck2):
              stockstats[i+1][0].bal += secondprize
              winnerlist.append(stockstats[i+1][0].name)
            ', '.join(winnerlist)
            secondStatement = f'{", ".join(winnerlist)} hold Second Majority in {chain} and have earned ${secondprize} each!'
          else:
            secondStatement = f'{stockstats[1][0].name} holds Second Majority in {chain} and has earned ${secondprize}!'
            stockstats[1][0].bal += secondprize
      statementsList.append((bankStatement, firstStatement, secondStatement))
    return bankdrawntile, statementsList
  
  def playtile(self, tile: str): #tile must be playable!
    self.board.debug_tilesinplayorder.append(tile)
    sortactiveIDs = self.tilebag.tilesToIDs(self.board.debug_tilesinplayorder)
    sortactiveIDs.sort()
    self.board.tilesinplay = self.tilebag.tileIDinterp(sortactiveIDs)
    return None
  
  def sellallstock(self, players: list[Player]):
    for chain in self.board.fetchactivechains():
      costper = self.stockcost(chain, self.board.fetchchainsize(chain))
      for p in players:
        p.bal += p.stocks[chain] * costper
    return None
