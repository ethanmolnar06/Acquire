import pygame
from __main__ import HIDE_PERSONAL_INFO, ALLOW_SAVES, ALLOW_QUICKSAVES
from common import write_save
from gui import draw_grid, draw_player_info, draw_tilehider, draw_tiles, draw_popup, draw_popup_selects
from tilebag import TileBag
from board import Board
from bank import Bank
from stats import Stats, statIncrement, assignStatVals
from player import Player

def make_savestate(tilebag: TileBag, board: Board, bank: Bank, players: list[Player], personal_info_names: list[str], currentP: Player, globalStats: Stats):
  if HIDE_PERSONAL_INFO:
    for i, p in enumerate(players):
      p.name = personal_info_names[i]
  currentOrderP = players[players.index(currentP):] + players[:players.index(currentP)]
  saveData = (bank,
              currentOrderP,
              globalStats,
              board,
              tilebag) # reverse unpack priority
  if HIDE_PERSONAL_INFO:
    for i, p in enumerate(players):
      p.name = f"Player {i+1}"
  return saveData, currentOrderP

def gameloop(dir_path: str, screen: pygame.Surface, clock: pygame.time.Clock, framerate: int,
             tilebag: TileBag, board: Board, bank: Bank, players: list[Player], personal_info_names: list[str], globalStats: Stats, loadedSaveFile: bool):
  gameRunning = True
  while gameRunning:
    for p in players:
      # region StateMap Declarations and Game Init
      forceRender = True
      currentTurn = True
      showTiles = False
      turntile = None
      gameEndable = None
      bankdrawntile = None
      pendingTileHandler = None
      
      drawPhase = True
      
      choosingNewChain = False
      mergerMode = False
      defunctPayoutMode = False
      defunctMode = False
      askToBuy = None
      buyPhase = False
      
      popup_open = False
      popupToClose = False
      dragging_knob1, dragging_knob2 = [False]*2
      
      if loadedSaveFile:
        loadedSaveFile = False
      else:
        statIncrement(players)
        globalStats.turnCounter += [globalStats.turnCounter[-1] + 1]
        globalStats.bankTilesDrawn += [globalStats.bankTilesDrawn[-1]]
      saveData, currentOrderP = make_savestate(tilebag, board, bank, players, personal_info_names, p, globalStats)
      if ALLOW_QUICKSAVES:
        write_save(dir_path, currentOrderP, globalStats, saveData, quicksave=True)
      # endregion
      
      while currentTurn:
        # print(currentTurn, showTiles, gameEndable)
        # anyState = any((drawPhase, choosingNewChain, mergerMode, defunctPayoutMode, defunctMode, buyPhase))
        # print(drawPhase, choosingNewChain, mergerMode, defunctPayoutMode, defunctMode, buyPhase)
        
        event = pygame.event.poll()
        if forceRender or event.type:
          forceRender = False
          # region Render Process
          # Clear the screen
          screen.fill((255, 255, 255))
          # Draw the grid
          draw_grid(board.tilesinplay)
          # Draw the current player information
          draw_player_info(pDefuncting if defunctMode else p)
          # Draw the tile button grid if showTiles == True
          if not showTiles or defunctPayoutMode or defunctMode: tilehider_rect = draw_tilehider(p, showTiles)
          elif showTiles: tile_rects = draw_tiles(p, prohibitedTiles)
          # Draw the popup button grid
          popup_select_rects = draw_popup_selects()
          # Draw Players and Bank inventory popup if open
          if popup_open: 
            close_button_rect, _ = draw_popup('playerStats', drawinfo)
          else:
            #Draw ask to end game popup
            if gameEndable:
              _, yesandno_rects = draw_popup('endGameConfirm', None)
            # Draw choose new chain selection if choosingNewChain is True
            elif choosingNewChain: _, newchain_rects = draw_popup('newChain', None)
            # Draw merger prioritization if mergerMode is True
            elif mergerMode:
              stopmerger_button_rect, subdraw_output = draw_popup('mergeChainPriority', (mergeCart, chainoptions))
              mergeChain_rects, mergecart_rects = subdraw_output
            # Draw defunct payout if defunctMode is True
            elif defunctPayoutMode:
              stopdefunctpayout_button_rect, _ = draw_popup('defunctPayout', (statementsList[0], iofnStatement))
            # Draw defunct stock allocation if defunctMode is True
            elif defunctMode:
              stopdefunct_button_rect, knobs_slider_rects = draw_popup('defuncter', (knob1_x, knob2_x, tradeBanned, defunctingStocks, pDefuncting, defunctchains[0], bigchain))
              knob1_rect, knob2_rect, slider_rect = knobs_slider_rects
              slider_x = slider_rect.x; slider_width = slider_rect.width
            #Draw ask to buy popup if askToBuy == True
            elif askToBuy and not gameEndable:
              _, yesandno_rects = draw_popup('askToBuy', None)
            elif buyPhase and not gameEndable:
              stopbuy_button_rect, stock_plusmin_rects = draw_popup('stockBuy', [stockcart, p])
          # Update the display
          pygame.display.flip()
          # endregion
          # region Handle common events
        if popupToClose: #fixes double-counting popup-closing as game-event closing
          popupToClose = False
          popup_open = False
        if event.type == pygame.QUIT:
          gameRunning = False
          currentTurn = False
          gameEndable = False
        elif event.type == pygame.VIDEORESIZE:
          # Update the window size
          screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        elif event.type == pygame.MOUSEBUTTONDOWN:
          # Get the mouse position
          pos = pygame.mouse.get_pos()
          if popup_open and close_button_rect.collidepoint(pos): # Check if popup_close was clicked
            popupToClose = True
          for i, popup_select_rect in enumerate(popup_select_rects): # Check if any of the popup_selects were clicked
            if popup_select_rect.collidepoint(pos):
              drawinfo = [play for play in players if play != p] if i == 0 else [bank]
              popup_open = True
        # endregion
        
        #Waiting to Draw and Handle Events in Draw Mode
        if not showTiles:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            if tilehider_rect.collidepoint(pos): 
              showTiles = True
              prohibitedTiles = board.contraceptcheck(p.tiles, checkChainAvail=True)
        
        elif drawPhase:
          if turntile == None and event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            # Check if any of the tile_rects were clicked
            for i, tile_rect in enumerate(tile_rects):
              if (tile_rect.collidepoint(pos) and not prohibitedTiles[i]):
                turntile = p.tiles[i]
                break
          if turntile != None:
            drawPhase = False
            forceRender = True
            actingPlacer = p if pendingTileHandler == None else bank
            actingPlacer.playtile(turntile)
            adjinplay = board.fetchadjacent(turntile)
            if len(adjinplay) > 0: 
              #is actually touchind something, check if/what chain
              chainedonly = board.chainsContained(adjinplay)
              if len(chainedonly) == 0: #found new chain, head to New Chain Loop
                choosingNewChain = True
                unopenedchains = [chain for chain in tilebag.chainnames if chain not in board.fetchactivechains()]
                p.stats.chainsFounded[-1] += 1
              elif len(chainedonly) == 1: #expand
                board.chaindict[turntile] = chainedonly[0]
                chaingrowth = board.tileprop(turntile, chainedonly[0])
                p.stats.mostExpandedChain[chainedonly[0]][-1] += chaingrowth
              else: #prep for merge
                mergeCartInit = board.mergeCart_init(turntile, chainedonly)
                if type(mergeCartInit) == list: #Feeds Directly to Defunct Payout
                  defunctPayoutMode = True
                  bigchain = mergeCartInit[0]
                  defunctchains = mergeCartInit[1:]; defunctchains.reverse() #comes largest to smallest, we want to merge smallest to largest
                  bankdrawntile, statementsList = bank.chainpayout(players, defunctchains)
                  iofnStatement = [1, len(statementsList)]
                else: #merge needs player tiebreaking
                  mergerMode = True
                  mergeCart = mergeCartInit[0] #mergeCart is sorted in order of size
                  chainoptions = mergeCartInit[1]
                  defunctchains = bigchain = None
        
        #Waiting to Choose New Chain
        elif choosingNewChain: 
          for i, newchain_rect in enumerate(newchain_rects):
            # print(newchain_rect, pos, newchain_rect.collidepoint(pos))
            if newchain_rect.collidepoint(pos): 
              newchain = unopenedchains[i]
              board.chaindict[turntile] = newchain
              chaingrowth = board.tileprop(turntile, newchain)
              p.stats.mostExpandedChain[newchain][-1] += chaingrowth
              p.stocks[newchain] = p.stocks[newchain] + 1
              p.stats.stocksAcquired[-1] += 1
              p.stats.stockChainsOwned[-1].add(newchain)
              bank.stocks[newchain] = bank.stocks[newchain] - 1
              choosingNewChain = False
              break
        
        #Waiting to Choose Merger Prioritization if necessary
        elif mergerMode:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            for i, mergeChain_rect in enumerate(mergeChain_rects):
              if mergeChain_rect != None and mergeChain_rect.collidepoint(pos):
                if type(mergeCart) == tuple and '' in mergeCart[i//2] and chainoptions[i//2][i%2] not in mergeCart[i//2]:
                  mergeCart[i//2][mergeCart[i//2].index('')] = chainoptions[i//2][i%2]
                elif '' in mergeCart and chainoptions[i] not in mergeCart:
                  mergeCart[mergeCart.index('')] = chainoptions[i]
            for i, mergecart_rect in enumerate(mergecart_rects):
              if mergecart_rect != None and mergecart_rect.collidepoint(pos):
                if type(mergeCart) == tuple and mergeCart[i//2] != '':
                  mergeCart[i//2][i%2] = ''
                elif mergeCart[i] != '': 
                  mergeCart[i] = ''
            if stopmerger_button_rect != None and stopmerger_button_rect.collidepoint(pos) and not popup_open:
              mergerMode = False
              defunctPayoutMode = True
              if type(mergeCart) == tuple: mergeCart = mergeCart[0] + mergeCart[1]
              bigchain = mergeCart[0]
              defunctchains = mergeCart[1:]; defunctchains.reverse() #comes largest to smallest, we want to merge smallest to largest
              bankdrawntile, statementsList = bank.chainpayout(players, defunctchains)
              iofnStatement = [1, len(statementsList)]
        
        #bankdrawntile handler
        elif bankdrawntile != None:
          deadcheck = board.deadduckcheck(p, bankdrawntile)
          if deadcheck == True:
            bankdrawntile = None
          elif len(deadcheck[0]) == 0 or len(deadcheck[1]) <= 1:
            bank.playtile(bankdrawntile)
            if len(deadcheck[1]) == 1:
              pendingTileHandler = (bankdrawntile, deadcheck[1][0])
            bankdrawntile = None
          else: #recursive merger troubles!
            bank.playtile(bankdrawntile)
            pendingTileHandler = bankdrawntile
            bankdrawntile = None
        
        #Waiting to player to dismiss all merge payout popups
        elif defunctPayoutMode:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            if stopdefunctpayout_button_rect.collidepoint(pos) and not popup_open:
              iofnStatement[0] += 1
              if len(statementsList) > 1:
                statementsList = statementsList[1:]
              else: statementsList = None
          if statementsList == None:
            defunctPayoutMode = False
            defunctMode = True
            pDefunctingLoop = players[players.index(p):] + players[:players.index(p)]
            pDefunctingLoop = [hassome for hassome in pDefunctingLoop if hassome.stocks[defunctchains[0]] > 0 ]
            pDefuncting = pDefunctingLoop[0]
            defunctingStocks = pDefuncting.stocks[defunctchains[0]]
            defunctStockInv = {'keep': int(0),
                              'sell': int(0),
                              'trade': int(0)}
            knob1_x = 0
            knob2_x = defunctingStocks
            tradeBanned = (defunctingStocks - knob2_x)/2 >= bank.stocks[bigchain]
            p.stats.mergersMade[-1] += len(defunctchains)
        
        #Waiting for each Player to Handle Defunct Decision
        elif defunctMode:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            if not popup_open:
              if knob1_rect.collidepoint(event.pos):
                dragging_knob1 = True
              elif knob2_rect.collidepoint(event.pos) and bank.stocks[bigchain] > 0:
                dragging_knob2 = True
          elif event.type == pygame.MOUSEBUTTONUP:
            dragging_knob1 = False
            dragging_knob2 = False
          elif event.type == pygame.MOUSEMOTION:
            if dragging_knob1:
              knob1_x = round((event.pos[0] - slider_x) * (defunctingStocks / slider_width))
              knob1_x = max(knob1_x, 0)  #Ensure knob1_x doesn't go beyond the slider's left side
              knob1_x = min(knob1_x, knob2_x)  #Ensure knob1_x doesn't go beyond knob2_x
            elif dragging_knob2 and bank.stocks[bigchain] > 0:
              knob2_x = (round((event.pos[0] - slider_x) * (defunctingStocks / slider_width))// 2)*2 + defunctingStocks%2 #Make knob2_x odd if defunctingStocks is odd
              knob2_x = max(knob2_x, ((knob1_x + (defunctingStocks+1)%2) // 2)*2 + defunctingStocks%2 )  #Ensure knob2_x is greater than knob1_x
              knob2_x = min(knob2_x, defunctingStocks)  #Ensure knob2_x doesn't exceed defunctingStocks
              tradeBanned = (defunctingStocks - knob2_x)/2 >= bank.stocks[bigchain]
              if (tradeBanned):
                knob2_x = max(knob2_x, defunctingStocks - (bank.stocks[bigchain]*2) )
          defunctStockInv = {'keep': knob1_x,
                            'sell': defunctingStocks - (defunctingStocks - knob2_x + knob1_x),
                            'trade': defunctingStocks - knob2_x}
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            if not popup_open:
              if stopdefunct_button_rect != None and stopdefunct_button_rect.collidepoint(pos): #player finished
                #sell
                pDefuncting.stocks[defunctchains[0]] -= defunctStockInv['sell']
                bank.stocks[defunctchains[0]] += defunctStockInv['sell']
                pDefuncting.bal += bank.stockcost(defunctchains[0], board.fetchchainsize(defunctchains[0]))*defunctStockInv['sell']
                #trade
                pDefuncting.stocks[defunctchains[0]] -= defunctStockInv['trade']
                bank.stocks[defunctchains[0]] += defunctStockInv['trade']
                pDefuncting.stocks[bigchain] += int(defunctStockInv['trade']/2)
                bank.stocks[bigchain] -= int(defunctStockInv['trade']/2)
                #stats
                pDefuncting.stats.stocksSold[-1] += defunctStockInv['sell']
                pDefuncting.stats.stocksTradedAway[-1] += defunctStockInv['trade']
                pDefuncting.stats.stocksAcquired[-1] += int(defunctStockInv['trade']/2)
                #cycle pDefuncting
                if pDefuncting == pDefunctingLoop[-1]:
                  #cycle defunctchains once all players taken their turn
                  if len(defunctchains) > 1:
                    chaingrowth = board.tileprop(turntile, bigchain, defunctchains[0], pendingTileHandler)
                    p.stats.mostExpandedChain[chainedonly[0]][-1] += chaingrowth
                    defunctchains = defunctchains[1:]

                    pDefunctingLoop = players[players.index(p):] + players[:players.index(p)]
                    pDefunctingLoop = [hassome for hassome in pDefunctingLoop if hassome.stocks[defunctchains[0]] > 0 ]
                    pDefuncting = pDefunctingLoop[0]
                    defunctingStocks = pDefuncting.stocks[defunctchains[0]]
                    knob1_x = 0
                    knob2_x = defunctingStocks
                  else: #exit the defuncting loop!!!
                    defunctMode = False
                    chaingrowth = board.tileprop(turntile, bigchain, ignoreTile=pendingTileHandler)
                    p.stats.mostExpandedChain[chainedonly[0]][-1] += chaingrowth
                    board.chaindict[turntile] = bigchain
                    if pendingTileHandler != None:
                      if type(pendingTileHandler) == tuple:
                        board.chaindict[pendingTileHandler[0]] = pendingTileHandler[1]
                        chaingrowth = board.tileprop(pendingTileHandler[0], pendingTileHandler[1])
                        p.stats.mostExpandedChain[pendingTileHandler[1]][-1] += chaingrowth
                        pendingTileHandler = None
                      else:
                        drawPhase = True
                        turntile = pendingTileHandler
                else:
                  pDefuncting = pDefunctingLoop[pDefunctingLoop.index(pDefuncting)+1]
                  defunctingStocks = pDefuncting.stocks[defunctchains[0]]
                  knob1_x = 0
                  knob2_x = defunctingStocks
        
        #Post Draw Endgame and Buyability Check
        elif gameEndable == None:
          gameEndable = board.endgamecheck()
          buyPhase = len(board.fetchactivechains()) > 0 and any([bank.stocks[chain] for chain in board.fetchactivechains()]) and p.bal >= bank.fetchcheapeststock()[1]
          if buyPhase:
            askToBuy = True
          else:
            if not gameEndable: currentTurn = False
        
        #Waiting for Player to Choose to End Game
        elif gameEndable:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            if not popup_open:
              # Check ask to end the game
              for i, yesorno_rect in enumerate(yesandno_rects):
                if yesorno_rect.collidepoint(pos):
                  gameEndable = False
                  if i == 1:
                    currentTurn = False
                    gameRunning = False
                    break
        
        #Waiting for Player to Choose to Buy Stocks
        elif askToBuy:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            if not popup_open:
              # Check if askToBuy was clicked
              for i, yesorno_rect in enumerate(yesandno_rects):
                if yesorno_rect.collidepoint(pos):
                  askToBuy = False
                  if i == 1:
                    boughtthisturn = 0
                    stockcart = []
                    buyablechains = [chain for chain in board.fetchactivechains() if bank.stocks[chain] or chain in stockcart]
                    preBuyBal = p.bal
                  else:
                    buyPhase = False
                    currentTurn = False
        
        #Waiting to Buy and Handle Events in Buy Mode
        elif buyPhase:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            for i, stock_plusmin_rect in enumerate(stock_plusmin_rects):
              # print(newchain_rect, pos, newchain_rect.collidepoint(pos))
              if stock_plusmin_rect != None and stock_plusmin_rect.collidepoint(pos) and not popup_open:
                buykey = buyablechains[i//2]
                if i%2 == 0: #minus
                  if buykey in stockcart: 
                    stockcart.remove(buykey); stockcart = [entry for entry in stockcart if entry != '']
                    p.stocks[buykey] -= 1
                    bank.stocks[buykey] += 1
                    p.bal += bank.stockcost(buykey, board.fetchchainsize(buykey) )
                    boughtthisturn -= 1
                else: #plus
                  if boughtthisturn < 3:
                    if bank.stockcost(buykey, board.fetchchainsize(buykey)) > p.bal: print('Transaction Failed! You are too poor! :(')
                    else:
                      stockcart.append(buykey); stockcart = [entry for entry in stockcart if entry != '']
                      p.stocks[buykey] += 1
                      bank.stocks[buykey] -= 1
                      p.bal -= bank.stockcost(buykey, board.fetchchainsize(buykey) )
                      boughtthisturn += 1
                  else: print('no cheating :(')
            # Check if stockbuy close was clicked
            if stopbuy_button_rect.collidepoint(pos) and not popup_open:
              p.stats.moneySpent[-1] += preBuyBal - p.bal
              p.stats.stocksAcquired[-1] += len(stockcart)
              for buykey in stockcart:
                p.stats.stockChainsOwned[-1].add(buykey)
              buyPhase = False
              currentTurn = False
      
      #turn finished handling
      assignStatVals(players)
      if gameRunning == True:
        p.drawtile()
        board.deadduckcheck(p)
      if not gameRunning: 
        break
      clock.tick(framerate)
  return saveData, currentOrderP, players, globalStats
