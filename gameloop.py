import pygame
from uuid import UUID
from copy import copy

from objects import *
from objects.player import setPlayerOrder, statIncrement, assignStatVals
from objects.networking import fetch_updates, propagate, DISCONN
from common import ALLOW_QUICKSAVES, MAX_FRAMERATE, NO_RENDER_EVENTS, pack_gameState, unpack_gameState, write_save

def gameloop(gameUtils: tuple[pygame.Surface, pygame.time.Clock], newGame: bool, gameState: tuple[TileBag, Board, list[Player], Bank], 
             clientMode: str, my_uuid: UUID | None) -> tuple[bool, bytes]:
  global screen, tilebag, board, bank
  screen, clock = gameUtils
  tilebag, board, players, bank = gameState
  from gui import draw_popup, draw_main_screen
  
  p = None
  pDefuncting = None
  P = find_player(my_uuid, players) if not clientMode == "hostLocal" else None
  
  def send_gameStateUpdate():
    gameStateUpdate = pack_gameState(tilebag, board, players, bank)
    target = "client" if clientMode == "hostServer" else "server"
    propagate(players, None, Command(f"set {target} gameState", gameStateUpdate))
  
  def overflow_update(update: tuple[UUID, Command] | None):
    global u, u_overflow
    # try to be super safe, not drop any updates in either queue
    if update is not None:
      u_overflow += [update,]
    u_overflow += copy(u) 
    u = []
  
  def cycle_pDefuncting() -> tuple[str, Player]:
    global defunctchain, pDefuncting, pendingTileHandler
    if len(pDefunctingLoop):
      defunctchain = defunctchain
      pDefuncting = pDefunctingLoop.pop(0)
    elif len(defunctchains):
      chaingrowth = board.tileprop(turntile, bigchain, defunctchain, pendingTileHandler)
      p.stats.mostExpandedChain[chains[0]][-1] += chaingrowth
      defunctchain = defunctchains.pop(0)
      pDefunctingLoop = [p for p in players if p.stocks[defunctchain] > 0 ]
      pDefuncting = pDefunctingLoop.pop(0)
    else:
      chaingrowth = board.tileprop(turntile, bigchain, ignoreTile=pendingTileHandler)
      p.stats.mostExpandedChain[bigchain][-1] += chaingrowth
      board.chaindict[turntile] = bigchain
      if pendingTileHandler is not None:
        if isinstance(pendingTileHandler, tuple):
          board.chaindict[pendingTileHandler[0]] = pendingTileHandler[1]
          chaingrowth = board.tileprop(pendingTileHandler[0], pendingTileHandler[1])
          p.stats.mostExpandedChain[pendingTileHandler[1]][-1] += chaingrowth
          pendingTileHandler = None
      defunctchain = None
      pDefuncting = None
    return defunctchain, pDefuncting
  
  if newGame and "host" in clientMode:
    players = setPlayerOrder(tilebag, board, players)
    send_gameStateUpdate()
  
  cyclingPlayers = True
  gameCompleted = False
  skipStatIncrem = True
  u_overflow = []
  while cyclingPlayers:
    
    # region Save Game and Player Cycle
    if "host" in clientMode:
      if skipStatIncrem:
        skipStatIncrem = False
      else:
        statIncrement(players)
        bank.stats.turnCounter += [bank.stats.turnCounter[-1] + 1]
        bank.stats.bankTilesDrawn += [bank.stats.bankTilesDrawn[-1]]
      saveData = pack_gameState(tilebag, board, players, bank)
      
      if ALLOW_QUICKSAVES:
        write_save(saveData, [p._truename for p in players], bank.stats.turnCounter[-1], quicksave=True)
      
      p = players.pop(0)
      players.append(p)
      send_gameStateUpdate()
      propagate(players, None, Command("set player turn", p.uuid))
    # endregion
    
    # region StateMap Declarations
    forceRender = True
    ongoingTurn = True
    showTiles = False if clientMode == "hostLocal" else True
    turntile = None
    gameEndable = None
    bankdrawntile = None
    pendingTileHandler = None
    
    placePhase = True if clientMode == "hostLocal" or (clientMode == "hostServer" and p.uuid == my_uuid) else False
    choosingNewChain = False
    tiebreakMerge = False
    prepForMerge = False
    defunctPayout = False
    setupDefunctVars = False
    defunctMode = False
    checkGameEndable = False
    askToBuy = False
    buyPhase = False
    turnWrapup = False
    
    popup_open = False
    popupToClose = False
    dragging_knob1, dragging_knob2 = [False]*2
    # endregion
    
    while ongoingTurn:
      # region debug
      # print(p._truename, placePhase, checkGameEndable, turnWrapup)
      # endregion
      
      # region check for updates over network
      u = fetch_updates(players) if not u_overflow else u_overflow
      while len(u):
        uuid, comm = u.pop(0)
        if clientMode == "hostServer":
          # command revieved from clients
          if comm.dump() == "set server connection" and comm.val == DISCONN:
            p = find_player(uuid, players)
            print(f"[PLAYER DROPPED] Disconnect Message Recieved from {p.conn}")
            p.DISCONN()
            # TODO create choose (wait for rejoin) / (quit here) dialog
          
          elif comm.dump() == "set server gameState":
            gameStateUpdate: bytes = comm.val
            tilebag, board, players, bank = unpack_gameState(gameStateUpdate, players)
            overflow_update()
          
          elif comm.dump() == "set player turn" and not comm.val:
            ongoingTurn = False
          
          elif comm.dump() == "set game completed" and comm.val:
            gameCompleted = True
          
          # expecting u_overflow
          elif comm.dump() == "set bank merge":
            datatup: tuple[str, str, list[str], str | tuple[str], list[str], list[int, int]] = comm.val
            turntile, bigchain, defunctchains, pendingTileHandler, statementsList, iofnStatement = datatup
            defunctPayout = True
            propagate(players, None, Command("set bank merge", (statementsList, iofnStatement)))
            
            defunctchain = defunctchains.pop(0)
            pDefunctingLoop = [p for p in players if p.stocks[defunctchain] > 0 ]
            pDefuncting = pDefunctingLoop.pop(0)
            if pDefuncting.uuid == my_uuid:
              setupDefunctVars = True
            
            send_gameStateUpdate()
            propagate(players, None, Command("set player defunct", pDefuncting.uuid))
          
          # expecting u_overflow
          elif comm.dump() == "set player defunct" and not comm.val:
            defunctchain, pDefuncting = cycle_pDefuncting()
            if pDefuncting is not None:
              if pDefuncting.uuid == my_uuid:
                setupDefunctVars = True
              send_gameStateUpdate()
              propagate(players, None, Command("set player defunct", (bigchain, defunctchain, pDefuncting.uuid)))
            else:
              if p.uuid == my_uuid:
                if pendingTileHandler is not None:
                  turntile = pendingTileHandler
                  placePhase = True
                else:
                  checkGameEndable = True
              send_gameStateUpdate()
              propagate(players, None, Command("set player resume", (pendingTileHandler, p.uuid)))
          
          send_gameStateUpdate()
        
        else:
          # command recieved from server
          if comm.dump() == "set client connection" and comm.val == DISCONN:
            # will break if P not yet set for client, but this *shouldn't* be possible
            P.DISCONN()
            cyclingPlayers = False
            ongoingTurn = False
          
          elif comm.dump() == "set client gameState":
            gameStateUpdate: bytes = comm.val
            tilebag, board, players, bank = unpack_gameState(gameStateUpdate, players)
          
          elif comm.dump() == "set player turn" and comm.val:
            p_uuid: UUID = comm.val
            if my_uuid == p_uuid:
              p = P
              placePhase = True
            else:
              p = None
              placePhase = False
          
          elif comm.dump() == "set bank merge":
            datatup: tuple[str | None, list[str]] = comm.val
            statementsList, iofnStatement = datatup
            defunctPayout = True
          
          elif comm.dump() == "set player defunct" and comm.val:
            datatup: tuple[str, str, UUID] = comm.val
            bigchain, defunctchain, p_uuid = datatup
            if my_uuid == p_uuid:
              pDefuncting = P
              setupDefunctVars = True
            else:
              pDefuncting = None
              setupDefunctVars = False
          
          elif comm.dump() == "set player resume" and comm.val:
            datatup: tuple[str | None, UUID] = comm.val
            pendingTileHandler, p_uuid = datatup
            if my_uuid == p_uuid:
              p = P
              if pendingTileHandler is not None:
                turntile = pendingTileHandler
                placePhase = True
              else:
                checkGameEndable = True
            else:
              pendingTileHandler = None
              p = None
              checkGameEndable = False
        
        if my_uuid in [p.uuid for p in players]:
          P = find_player(my_uuid, players)
        forceRender = True
      # endregion
      
      event = pygame.event.poll()
      # region Render Process
      if forceRender or event.type not in NO_RENDER_EVENTS:
        forceRender = False
        # Clear the screen
        screen.fill((255, 255, 255))
        # Draw the Main Board Screen
        display_player = (pDefuncting if defunctMode else p) if clientMode == "hostLocal" else P
        prohibitedTiles = board.contraceptcheck(display_player.tiles, checkChainAvail=True)
        tilehider_rect, tile_rects, popup_select_rects = draw_main_screen(board, display_player, showTiles, prohibitedTiles, defunctMode)
        if popup_open:
          # draw over current popup-sized event
          close_button_rect, _ = draw_popup('playerStats', drawinfo)
        else:
          # TODO fewer pop-sized events, make more full screen with option to view board and/or stats
          #Draw ask to end game popup
          if gameEndable:
            _, yesandno_rects = draw_popup('endGameConfirm', None)
          # Draw choose new chain selection if choosingNewChain is True
          elif choosingNewChain: _, newchain_rects = draw_popup('newChain', None)
          # Draw merger prioritization if tiebreakMerge is True
          elif tiebreakMerge:
            stopmerger_button_rect, subdraw_output = draw_popup('mergeChainPriority', (mergeCart, chainoptions))
            mergeChain_rects, mergecart_rects = subdraw_output
          # Draw defunct payout if defunctMode is True
          elif defunctPayout:
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
        if not clientMode == "hostLocal":
          target = "client" if clientMode == "hostServer" else "server"
          propagate(players, None, Command(f"set {target} connection", DISCONN))
          P.DISCONN()
        cyclingPlayers = False
        ongoingTurn = False
        gameEndable = False
        break
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
      
      # region gameState elifs
      if clientMode == "hostLocal" or (p is not None and p.uuid == my_uuid) or (pDefuncting is not None and pDefuncting.uuid == my_uuid):
        
        # Hide Tiles from Players if clientMode == "hostLocal"
        if not showTiles:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            if tilehider_rect.collidepoint(pos): 
              showTiles = True
        
        # Waiting to Draw and Handle Events in Draw Mode
        elif placePhase:
          if turntile is None and event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            # Check if any of the tile_rects were clicked
            for i, tile_rect in enumerate(tile_rects):
              if (tile_rect.collidepoint(pos) and not prohibitedTiles[i]):
                turntile = p.tiles[i]
                break
          if turntile is not None:
            placePhase = False
            forceRender = True
            if pendingTileHandler is None:
              p.playtile(turntile) 
            mode, chains = board.tileplaymode(turntile)
            if mode == "place":
              checkGameEndable = True
              send_gameStateUpdate()
            elif mode == "create":
              choosingNewChain = True
              unopenedchains = [chain for chain in tilebag.chainnames if chain not in board.fetchactivechains()]
              p.stats.chainsFounded[-1] += 1
              send_gameStateUpdate()
            elif mode == "expand":
              checkGameEndable = True
              board.chaindict[turntile] = chains
              chaingrowth = board.tileprop(turntile, chains)
              p.stats.mostExpandedChain[chains][-1] += chaingrowth
              send_gameStateUpdate()
            else: #prep for merge
              prepForMerge = True
              mergeCartInit = board.mergeCart_init(chains) # mergeCart is sorted in order of size
              send_gameStateUpdate()
              if isinstance(mergeCartInit, list): # Feeds Directly to prepForMerge
                mergeCart = mergeCartInit
              else: # Merge needs player tiebreaking first
                tiebreakMerge = True
                mergeCart = mergeCartInit[0] 
                chainoptions = mergeCartInit[1]
                defunctchains = bigchain = None
        
        # Waiting to Choose New Chain
        elif choosingNewChain: 
          for i, newchain_rect in enumerate(newchain_rects):
            # print(newchain_rect, pos, newchain_rect.collidepoint(pos))
            if newchain_rect.collidepoint(pos):
              choosingNewChain = False
              checkGameEndable = True
              newchain = unopenedchains[i]
              board.chaindict[turntile] = newchain
              chaingrowth = board.tileprop(turntile, newchain)
              p.stats.mostExpandedChain[newchain][-1] += chaingrowth
              p.stocks[newchain] = p.stocks[newchain] + 1
              p.stats.stocksAcquired[-1] += 1
              p.stats.stockChainsOwned[-1].add(newchain)
              bank.stocks[newchain] = bank.stocks[newchain] - 1
              send_gameStateUpdate()
              break
        
        # Waiting to Choose Merger Prioritization if necessary
        elif tiebreakMerge:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            for i, mergeChain_rect in enumerate(mergeChain_rects):
              if mergeChain_rect is not None and mergeChain_rect.collidepoint(pos):
                if isinstance(mergeCart, tuple) and '' in mergeCart[i//2] and chainoptions[i//2][i%2] not in mergeCart[i//2]:
                  mergeCart[i//2][mergeCart[i//2].index('')] = chainoptions[i//2][i%2]
                elif '' in mergeCart and chainoptions[i] not in mergeCart:
                  mergeCart[mergeCart.index('')] = chainoptions[i]
                send_gameStateUpdate()
            for i, mergecart_rect in enumerate(mergecart_rects):
              if mergecart_rect is not None and mergecart_rect.collidepoint(pos):
                if isinstance(mergeCart, tuple) and mergeCart[i//2] != '':
                  mergeCart[i//2][i%2] = ''
                elif mergeCart[i] != '': 
                  mergeCart[i] = ''
                send_gameStateUpdate()
            if stopmerger_button_rect is not None and stopmerger_button_rect.collidepoint(pos) and not popup_open:
              tiebreakMerge = False
        
        # Setup Variables for Merging
        elif prepForMerge:
          prepForMerge = False
          bigchain = mergeCart[0]
          defunctchains = mergeCart[1:]
          defunctchains.reverse() # mergeCart displays as largest to smallest, we want to merge smallest to largest
          bankdrawntile, statementsList = bank.chainpayout(players, defunctchains)
          
          if bankdrawntile is not None:
            if board.deadduckcheck(bankdrawntile):
              bankdrawntile = None
            else:
              mode, chains = board.tileplaymode(bankdrawntile)
              bank.playtile(bankdrawntile)
              if mode == 'expand':
                # push tile through ongoing merge, then propogate
                pendingTileHandler = (bankdrawntile, chains)
              elif mode == "merge":
                # push tile through ongoing merge, recursive merger troubles!
                pendingTileHandler = bankdrawntile
            bankdrawntile = None
          
          iofnStatement = [1, len(statementsList)]
          p.stats.mergersMade[-1] += len(defunctchains)
          
          if clientMode == "hostLocal":
            defunctchain = defunctchains.pop(0)
            pDefunctingLoop = [p for p in players if p.stocks[defunctchain] > 0 ]
            pDefuncting = pDefunctingLoop.pop(0)
            
            defunctPayout = True
            setupDefunctVars = True
          elif clientMode == "hostServer":
            send_gameStateUpdate()
            overflow_update((my_uuid, Command("set bank merge", (turntile, bigchain, defunctchains, pendingTileHandler,
                                                               statementsList, iofnStatement))))
          else:
            send_gameStateUpdate()
            propagate(players, None, Command("set bank merge", (turntile, bigchain, defunctchains, pendingTileHandler,
                                                                statementsList, iofnStatement)))
        
        # Waiting to player to dismiss all merge payout popups
        elif defunctPayout:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            if stopdefunctpayout_button_rect.collidepoint(pos) and not popup_open:
              iofnStatement[0] += 1
              if len(statementsList) > 1:
                statementsList = statementsList[1:]
              else:
                statementsList = None; iofnStatement = None
                defunctPayout = False
        
        # Setup Variables for Defuncting
        elif setupDefunctVars:
          setupDefunctVars = False
          defunctMode = True
          defunctingStocks = pDefuncting.stocks[defunctchain]
          knob1_x = 0
          knob2_x = defunctingStocks
          tradeBanned = (defunctingStocks - knob2_x)/2 >= bank.stocks[bigchain]
        
        # Waiting for each Player to Handle Defunct Decision
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
              if stopdefunct_button_rect is not None and stopdefunct_button_rect.collidepoint(pos): # Player finished
                #sell
                pDefuncting.stocks[defunctchain] -= defunctStockInv['sell']
                bank.stocks[defunctchain] += defunctStockInv['sell']
                pDefuncting.bal += bank.stockcost(defunctchain, board.fetchchainsize(defunctchain))*defunctStockInv['sell']
                #trade
                pDefuncting.stocks[defunctchain] -= defunctStockInv['trade']
                bank.stocks[defunctchain] += defunctStockInv['trade']
                pDefuncting.stocks[bigchain] += int(defunctStockInv['trade']/2)
                bank.stocks[bigchain] -= int(defunctStockInv['trade']/2)
                #stats
                pDefuncting.stats.stocksSold[-1] += defunctStockInv['sell']
                pDefuncting.stats.stocksTradedAway[-1] += defunctStockInv['trade']
                pDefuncting.stats.stocksAcquired[-1] += int(defunctStockInv['trade']/2)
                send_gameStateUpdate()
                
                #cycle pDefuncting
                if clientMode == "hostLocal":
                  defunctchain, pDefuncting = cycle_pDefuncting()
                  if pDefuncting is not None:
                    defunctingStocks = pDefuncting.stocks[defunctchain]
                    knob1_x = 0
                    knob2_x = defunctingStocks
                  else:
                    defunctMode = False
                    checkGameEndable = True
                    if pendingTileHandler is not None:
                      turntile = pendingTileHandler
                      pendingTileHandler = None
                elif clientMode == "hostServer":
                  defunctMode = False
                  send_gameStateUpdate()
                  overflow_update((my_uuid, Command("set player defunct", False)))
                else:
                  defunctMode = False
                  send_gameStateUpdate()
                  propagate((my_uuid, Command("set player defunct", False)))
        
        #Post Draw Endgame and Buyability Check - SHOULD BE HIT EVERY TURN W/O FAIL
        elif checkGameEndable:
          checkGameEndable = False
          turnWrapup = True
          gameEndable = board.endgamecheck()
          buyPhase = len(board.fetchactivechains()) > 0 and any([bank.stocks[chain] for chain in board.fetchactivechains()]) and p.bal >= bank.fetchcheapeststock()[1]
          # print(gameEndable, buyPhase)
          if buyPhase:
            askToBuy = True
        
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
                    gameCompleted = True
                    propagate(players, None, Command("set game completed", gameCompleted))
                    if not clientMode == "hostLocal":
                      cyclingPlayers = False
        
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
        
        #Waiting to Buy and Handle Events in Buy Mode
        elif buyPhase:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = pygame.mouse.get_pos()
            for i, stock_plusmin_rect in enumerate(stock_plusmin_rects):
              # print(newchain_rect, pos, newchain_rect.collidepoint(pos))
              if stock_plusmin_rect is not None and stock_plusmin_rect.collidepoint(pos) and not popup_open:
                buykey = buyablechains[i//2]
                if i%2 == 0: #minus
                  if buykey in stockcart: 
                    stockcart.remove(buykey); stockcart = [entry for entry in stockcart if entry != '']
                    p.stocks[buykey] -= 1
                    bank.stocks[buykey] += 1
                    p.bal += bank.stockcost(buykey, board.fetchchainsize(buykey) )
                    boughtthisturn -= 1
                    send_gameStateUpdate()
                else: #plus
                  if boughtthisturn < 3:
                    if bank.stockcost(buykey, board.fetchchainsize(buykey)) > p.bal:
                      print('Transaction Failed! You are too poor! :(')
                    else:
                      stockcart.append(buykey); stockcart = [entry for entry in stockcart if entry != '']
                      p.stocks[buykey] += 1
                      bank.stocks[buykey] -= 1
                      p.bal -= bank.stockcost(buykey, board.fetchchainsize(buykey) )
                      boughtthisturn += 1
                      send_gameStateUpdate()
                  else: 
                    print('no cheating :(')
            # Check if stockbuy close was clicked
            if stopbuy_button_rect.collidepoint(pos) and not popup_open:
              p.stats.moneySpent[-1] += preBuyBal - p.bal
              p.stats.stocksAcquired[-1] += len(stockcart)
              for buykey in stockcart:
                p.stats.stockChainsOwned[-1].add(buykey)
              buyPhase = False
        
        # Turn Over
        elif turnWrapup:
          if cyclingPlayers and not gameCompleted:
            p.drawtile()
            p.deadduckremoval()
          send_gameStateUpdate()
          if "host" in clientMode:
            ongoingTurn = False
          propagate(players, None, Command("set player turn", False))
          p = None
          pDefuncting = None
      
      # endregion
      
      clock.tick(MAX_FRAMERATE if pygame.key.get_focused() else 1)
    
    # Endgame or Host Iter
    if "host" in clientMode:
      if gameCompleted:
        # adds payouts directly to players' balance internally
        _ = bank.chainpayout(players, board.fetchactivechains())
        bank.sellallstock(players)
      
      assignStatVals(players)
      send_gameStateUpdate()
  
  return gameCompleted, saveData
