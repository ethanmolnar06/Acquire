import pygame
from uuid import UUID

from objects import *
from objects.player import setPlayerOrder, statIncrement, assignStatVals
from objects.networking import fetch_updates, propagate, DISCONN
from common import ALLOW_QUICKSAVES, MAX_FRAMERATE, VARIABLE_FRAMERATE, NO_RENDER_EVENTS, pack_gameState, unpack_gameState, write_save, send_gameStateUpdate, overflow_update, iter_flatten
from gui import GUI_area, draw_main_screen, draw_game_board, draw_newChain_fullscreen, draw_other_player_stats, draw_stockbuy_fullscreen, draw_mergeChainPriority_fullscreen, draw_defunctPayout_fullscreen, draw_focus_area_select, draw_defunctMode_fullscreen

def gameloop(gameUtils: tuple[pygame.Surface, pygame.time.Clock], newGame: bool, gameState: tuple[TileBag, Board, list[Player], Bank], 
             clientMode: str, my_uuid: UUID | None, host_uuid: UUID | None) -> tuple[bool, bytes]:
  screen, clock = gameUtils
  tilebag, board, players, bank = gameState
  
  def cycle_pDefuncting(pDefunctingLoop: list[Player], defunctchains: list[str],
                        turntile: str, bigchain: str, defunctChain: str, pendingTileHandler: str | tuple[str] | None) -> tuple[str, Player]:
    if len(pDefunctingLoop):
      pDefuncting = pDefunctingLoop.pop(0)
    elif len(defunctchains):
      chaingrowth = board.tileprop(turntile, bigchain, defunctChain, pendingTileHandler)
      p.stats.mostExpandedChain[bigchain][-1] += chaingrowth
      defunctChain = defunctchains.pop(0)
      pDefunctingLoop = [p for p in players if p.stocks[defunctChain] > 0 ]
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
      defunctChain = None
      pDefuncting = None
    return pDefunctingLoop, pDefuncting, defunctchains, defunctChain, pendingTileHandler
  
  if newGame and "host" in clientMode:
    players = setPlayerOrder(tilebag, board, players)
    send_gameStateUpdate(tilebag, board, players, bank, clientMode)
  else:
    # confirm to host that this client is in the gameloop and ready for play
    propagate(players, None, Command("set game start", True))
  
  u_overflow = [] # used to forceRender in the middle of updating
  saveData = None
  P = find_player(my_uuid, players) if not clientMode == "hostLocal" else None
  HOST = find_player(host_uuid, players) if clientMode == "hostServer" else None
  focus_content = GUI_area()
  
  cyclingPlayers = True
  gameCompleted = False
  skipStatIncrem = True
  
  while cyclingPlayers:
    # region StateMap Declarations
    p = None
    pDefuncting = None
    
    forceRender: bool = True
    skipRender: bool = False
    ongoingTurn: bool = True
    showTiles: bool = False if clientMode == "hostLocal" else True
    turntile: bool = None
    endGameConfirm: bool = None
    bankdrawntile: bool = None
    pendingTileHandler: bool = None
    
    placePhase: bool = True if clientMode == "hostLocal" else False
    choosingNewChain: bool = False
    mergeChainPriority: bool = False
    prepForMerge: bool = False
    defunctPayout: bool = False
    setupDefunctVars: bool = False
    defunctMode: bool = False
    checkGameEndable: bool = False
    askToBuy: bool = False
    buyPhase: bool = False
    turnWrapup: bool = False
    
    dragging_knob1, dragging_knob2 = [False]*2
    # endregion
    
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
      send_gameStateUpdate(tilebag, board, players, bank, clientMode)
      if clientMode == "hostServer" and p.uuid == my_uuid:
        placePhase = True
      propagate(players, None, Command("set player turn", p.uuid))
    # endregion
    
    while ongoingTurn:
      # region debug
      # print(p, placePhase, checkGameEndable, turnWrapup)
      # endregion
      
      # region Network Update Commands
      u = fetch_updates(players) if not u_overflow else u_overflow
      toPropagate = []
      while len(u):
        uuid, comm = u.pop(0)
        if clientMode == "hostServer":
          # command revieved from clients
          if comm == DISCONN:
            find_player(uuid, players).syncSendDISCONN(inResponse=True)
            # TODO create choose (wait for rejoin) / (quit here) dialog
          
          elif comm.dump() == "set server gameState":
            gameStateUpdate: bytes = comm.val
            tilebag, board, players, bank = unpack_gameState(gameStateUpdate, players)
            overflow_update(u, u_overflow)
          
          elif comm.dump() == "set player turn" and not comm.val:
            ongoingTurn = False
          
          elif comm.dump() == "set game completed" and comm.val:
            gameCompleted = True
          
          elif comm.dump() == "set bank merge": # expecting u_overflow
            datatup: tuple[str, str, list[str], str | tuple[str], list[str], list[int, int]] = comm.val
            turntile, bigchain, defunctchains, pendingTileHandler, statementsList, iofnStatement = datatup
            defunctPayout = True
            toPropagate.append(Command("set bank merge", (statementsList, iofnStatement)))
            focus_content.clear("defunctPayout")
            
            defunctChain = defunctchains.pop(0)
            pDefunctingLoop = [p for p in players if p.stocks[defunctChain] > 0 ]
            pDefuncting = pDefunctingLoop.pop(0)
            if pDefuncting.uuid == my_uuid:
              setupDefunctVars = True
            toPropagate.append(Command("set player defunct", pDefuncting.uuid))
          
          elif comm.dump() == "set player defunct" and not comm.val: # expecting u_overflow
            pDefunctingLoop, pDefuncting, defunctchains, defunctChain, pendingTileHandler = cycle_pDefuncting(pDefunctingLoop, defunctchains, turntile,
                                                                                                              bigchain, defunctChain, pendingTileHandler)
            if pDefuncting is not None:
              if pDefuncting.uuid == my_uuid:
                setupDefunctVars = True
              toPropagate.append(Command("set player defunct", (bigchain, defunctChain, pDefuncting.uuid)))
            else:
              if p.uuid == my_uuid:
                if pendingTileHandler is not None:
                  turntile = pendingTileHandler
                  placePhase = True
                else:
                  checkGameEndable = True
              toPropagate.append(Command("set player resume", (pendingTileHandler, p.uuid)))
          
          else: # unexpected / unknown command
            print("[UNEXPECTED COMMAND] : ", comm)
            continue
          
          send_gameStateUpdate(tilebag, board, players, bank, clientMode, uuid)
          for prop in toPropagate:
            propagate(players, None, prop)
        
        else:
          # command recieved from server
          if comm == DISCONN:
            HOST.syncSendDISCONN(inResponse=True)
            cyclingPlayers = False
            ongoingTurn = False
          
          elif comm.dump() == "set client gameState":
            gameStateUpdate: bytes = comm.val
            tilebag, board, players, bank = unpack_gameState(gameStateUpdate, players)
          
          elif comm.dump() == "set player turn":
            p_uuid: UUID | bool = comm.val
            if comm.val and my_uuid == p_uuid:
              p = P
              placePhase = True
            else:
              p = None
              placePhase = False
          
          elif comm.dump() == "set bank merge":
            datatup: tuple[list[tuple[str | None, str | None, str | None]], list[int]] = comm.val
            statementsList, iofnStatement = datatup
            defunctPayout = True
            focus_content.clear("defunctPayout")
          
          elif comm.dump() == "set player defunct" and comm.val:
            datatup: tuple[str, str, UUID] = comm.val
            bigchain, defunctChain, p_uuid = datatup
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
          
          else: # unexpected / unknown command
            print("[UNEXPECTED COMMAND] : ", comm)
            continue
        
        # P is given a new memory address each time gameState is updated over network, this fixes that
        if cyclingPlayers:
          P = find_player(my_uuid, players)
          HOST = find_player(host_uuid, players)
        forceRender = True
      # endregion
      
      iAmPlayer = (p is not None and p.uuid == my_uuid) or (pDefuncting is not None and pDefuncting.uuid == my_uuid)
      
      event = pygame.event.poll()
      # region Render Process
      if (forceRender or event.type not in NO_RENDER_EVENTS) and not skipRender:
        forceRender = False
        
        # Clear the screen
        screen.fill((255, 255, 255))
        
        # Draw Sidebar Area
        display_player = (pDefuncting if defunctMode else p) if clientMode == "hostLocal" else P
        indicate_player_turn = iAmPlayer and not clientMode == "hostLocal"
        prohibitedTiles = board.contraceptcheck(display_player.tiles, checkChainAvail=True)
        tilehider_rect, tile_rects, _, popup_select_rects = draw_main_screen(screen, display_player, showTiles, prohibitedTiles, 
                                                                          defunctMode, indicate_player_turn, focus_content)
        
        # region Focus Area
        if focus_content.game_board:
          draw_game_board(screen, board)
        elif focus_content.other_player_stats:
          draw_other_player_stats(screen, bank, [player for player in players if player is not (P if not clientMode == "hostLocal" else p)])
        elif choosingNewChain and focus_content.newchain:
          newchain_rects = draw_newChain_fullscreen(screen, board)
        elif mergeChainPriority and focus_content.mergeChainPriority:
          mergeChain_rects, mergecart_rects, stopmerger_button_rect = draw_mergeChainPriority_fullscreen(screen, mergeCart, chainoptions)
        elif defunctPayout and focus_content.defunctPayout:
          stopdefunctpayout_button_rect = draw_defunctPayout_fullscreen(screen, statementsList[0], iofnStatement)
        elif defunctMode and focus_content.defunctMode:
          stopdefunct_button_rect, knobs_slider_rects = draw_defunctMode_fullscreen(screen, bank, knob1_x, knob2_x, tradeBanned, pDefuncting, defunctChain, bigchain)
          knob1_rect, knob2_rect, slider_rect = knobs_slider_rects
          slider_x = slider_rect.x; slider_width = slider_rect.width
        elif endGameConfirm and focus_content.endGameConfirm:
          yesandno_rects = draw_focus_area_select(screen, 'endGameConfirm')
        elif askToBuy and focus_content.askToBuy:
          yesandno_rects = draw_focus_area_select(screen, 'askToBuy')
        elif buyPhase and focus_content.stockbuy:
          stockbuy_confirm_rect, stock_plusmin_rects = draw_stockbuy_fullscreen(screen, board, bank, display_player, stockcart)
        # endregion
        
        pygame.display.flip()
      skipRender = False
      # endregion
      
      # region Handle common events
      if event.type == pygame.QUIT:
        if not clientMode == "hostLocal":
          for p_DISCONN in players:
            p_DISCONN.syncSendDISCONN()
        cyclingPlayers = False
        ongoingTurn = False
        break
      elif event.type == pygame.VIDEORESIZE:
        # Update the window size
        screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
      elif event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = event.dict["pos"]
        for i, popup_select_rect in enumerate(popup_select_rects): # Check if any of the popup_selects were clicked
          if popup_select_rect.collidepoint(pos):
            # propagate(players, None, Command("test test test", False)) # DEBUG NETWORK COMMAND
            focus_content.change_showing(i)
      # endregion
      
      # region gameState elifs
      if clientMode == "hostLocal" or iAmPlayer:
        
        # Hide Tiles from Players if clientMode == "hostLocal"
        if not showTiles:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = event.dict["pos"]
            if tilehider_rect.collidepoint(pos): 
              showTiles = True
        
        # Waiting to Draw and Handle Events in Draw Mode
        elif placePhase:
          if turntile is None and tile_rects is not None and event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = event.dict["pos"]
            # Check if any of the tile_rects were clicked
            for i, tile_rect in enumerate(tile_rects):
              if (tile_rect.collidepoint(pos) and not prohibitedTiles[i]):
                turntile = p.tiles[i]
                break
          if turntile is not None:
            placePhase = False
            if pendingTileHandler is None:
              p.playtile(turntile)
            mode, chains = board.tileplaymode(turntile)
            if mode == "place":
              checkGameEndable = True; skipRender = True
              send_gameStateUpdate(tilebag, board, players, bank, clientMode)
            elif mode == "create":
              choosingNewChain = True; forceRender = True
              unopenedchains = [chain for chain in tilebag.chainnames if chain not in board.fetchactivechains()]
              p.stats.chainsFounded[-1] += 1
              focus_content.clear("newchain")
              send_gameStateUpdate(tilebag, board, players, bank, clientMode)
            elif mode == "expand":
              checkGameEndable = True; skipRender = True
              board.chaindict[turntile] = chains
              chaingrowth = board.tileprop(turntile, chains)
              p.stats.mostExpandedChain[chains][-1] += chaingrowth
              send_gameStateUpdate(tilebag, board, players, bank, clientMode)
            else: #prep for merge
              prepForMerge = True
              mergeCartInit = board.mergeCart_init(chains) # mergeCart is sorted in order of size
              send_gameStateUpdate(tilebag, board, players, bank, clientMode)
              if isinstance(mergeCartInit, list): # Feeds Directly to prepForMerge
                mergeCart = mergeCartInit
              else: # Merge needs player tiebreaking first
                mergeChainPriority = True
                mergeCart = mergeCartInit[0] 
                chainoptions = mergeCartInit[1]
                defunctchains = bigchain = None
                focus_content.clear("mergeChainPriority")
        
        # Waiting to Choose New Chain
        elif choosingNewChain: 
          for i, newchain_rect in enumerate(newchain_rects):
            # print(newchain_rect, pos, newchain_rect.collidepoint(pos))
            if newchain_rect.collidepoint(pos):
              choosingNewChain = False
              checkGameEndable = True; skipRender = True
              newchain = unopenedchains[i]
              board.chaindict[turntile] = newchain
              chaingrowth = board.tileprop(turntile, newchain)
              p.stats.mostExpandedChain[newchain][-1] += chaingrowth
              p.stocks[newchain] = p.stocks[newchain] + 1
              p.stats.stocksAcquired[-1] += 1
              p.stats.stockChainsOwned[-1].add(newchain)
              bank.stocks[newchain] = bank.stocks[newchain] - 1
              focus_content.clear()
              send_gameStateUpdate(tilebag, board, players, bank, clientMode)
              break
        
        # Waiting to Choose Merger Prioritization if necessary
        elif mergeChainPriority:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = event.dict["pos"]
            for i, mergeChain_rect in enumerate(mergeChain_rects):
              if mergeChain_rect is not None and mergeChain_rect.collidepoint(pos):
                if isinstance(mergeCart, tuple) and '' in mergeCart[i//2] and chainoptions[i//2][i%2] not in mergeCart[i//2]:
                  mergeCart[i//2][mergeCart[i//2].index('')] = chainoptions[i//2][i%2]
                elif '' in mergeCart and chainoptions[i] not in mergeCart:
                  mergeCart[mergeCart.index('')] = chainoptions[i]
                send_gameStateUpdate(tilebag, board, players, bank, clientMode)
            for i, mergecart_rect in enumerate(mergecart_rects):
              if mergecart_rect is not None and mergecart_rect.collidepoint(pos):
                if isinstance(mergeCart, tuple) and mergeCart[i//2] != '':
                  mergeCart[i//2][i%2] = ''
                elif mergeCart[i] != '': 
                  mergeCart[i] = ''
                send_gameStateUpdate(tilebag, board, players, bank, clientMode)
            if stopmerger_button_rect is not None and stopmerger_button_rect.collidepoint(pos):
              if isinstance(mergeCart, tuple):
                mergeCart = iter_flatten(mergeCart)
              mergeChainPriority = False
              skipRender = True
        
        # Setup Variables for Merging
        elif prepForMerge:
          prepForMerge = False
          bigchain = mergeCart[0]
          defunctchains = mergeCart[1:]
          defunctchains.reverse() # mergeCart displays as largest to smallest, we want to merge from smallest to largest defunctChain
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
            defunctChain = defunctchains.pop(0)
            pDefunctingLoop = [p for p in players if p.stocks[defunctChain] > 0 ]
            pDefuncting = pDefunctingLoop.pop(0)
          elif clientMode == "hostServer":
            send_gameStateUpdate(tilebag, board, players, bank, clientMode)
            overflow_update(u, u_overflow, (my_uuid, Command("set bank merge", (turntile, bigchain, defunctchains, pendingTileHandler,
                                                               statementsList, iofnStatement))))
          else:
            send_gameStateUpdate(tilebag, board, players, bank, clientMode)
            propagate(players, None, Command("set bank merge", (turntile, bigchain, defunctchains, pendingTileHandler,
                                                                statementsList, iofnStatement)))
          
          defunctPayout = True
          setupDefunctVars = True
          focus_content.clear("defunctPayout")
        
        # Waiting to player to dismiss all merge payout popups
        elif defunctPayout:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = event.dict["pos"]
            if stopdefunctpayout_button_rect.collidepoint(pos):
              iofnStatement[0] += 1
              if len(statementsList) > 1:
                statementsList = statementsList[1:]
              else:
                statementsList = None; iofnStatement = None
                defunctPayout = False
                if not setupDefunctVars:
                  focus_content.clear(); forceRender = True
        
        # Setup Variables for Defuncting
        elif setupDefunctVars:
          setupDefunctVars = False
          defunctMode = True
          knob1_x = 0
          knob2_x = pDefuncting.stocks[defunctChain]
          tradeBanned = bank.stocks[bigchain] == 0 or knob2_x < 2
          focus_content.clear("defunctMode")
        
        # Waiting for each Player to Handle Defunct Decision
        elif defunctMode:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = event.dict["pos"]
            if knob1_rect.collidepoint(event.pos):
              dragging_knob1 = True
            elif knob2_rect.collidepoint(event.pos) and bank.stocks[bigchain] > 0:
              dragging_knob2 = True
          elif event.type == pygame.MOUSEBUTTONUP:
            dragging_knob1 = False
            dragging_knob2 = False
          elif event.type == pygame.MOUSEMOTION:
            defunctingStocks = pDefuncting.stocks[defunctChain]
            if dragging_knob1 or dragging_knob2:
              forceRender = True
            if dragging_knob1:
              knob1_x = round((event.pos[0] - slider_x) * (defunctingStocks / slider_width))
              knob1_x = max(knob1_x, 0)  #Ensure knob1_x doesn't go beyond the slider's left side
              knob1_x = min(knob1_x, knob2_x)  #Ensure knob1_x doesn't go beyond knob2_x
            elif dragging_knob2 and bank.stocks[bigchain] > 0:
              knob2_x = (round((event.pos[0] - slider_x) * (defunctingStocks / slider_width))// 2)*2 + defunctingStocks % 2 #Make knob2_x odd if defunctingStocks is odd
              knob2_x = max(knob2_x, ((knob1_x + (defunctingStocks+1)%2) // 2)*2 + defunctingStocks%2 )  #Ensure knob2_x is greater than knob1_x
              knob2_x = min(knob2_x, defunctingStocks)  #Ensure knob2_x doesn't exceed defunctingStocks
              tradeBanned = (defunctingStocks - knob2_x)/2 >= bank.stocks[bigchain] or knob2_x < 2
              if (tradeBanned):
                knob2_x = max(knob2_x, defunctingStocks - (bank.stocks[bigchain]*2) )
          defunctStockInv = {'keep': knob1_x,
                             'sell': knob2_x - knob1_x,
                             'trade': pDefuncting.stocks[defunctChain] - knob2_x} # unhalved trade value
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = event.dict["pos"]
            if stopdefunct_button_rect is not None and stopdefunct_button_rect.collidepoint(pos): # Player finished
              # region move stocks
              #sell
              pDefuncting.stocks[defunctChain] -= defunctStockInv['sell']
              bank.stocks[defunctChain] += defunctStockInv['sell']
              pDefuncting.bal += bank.stockcost(defunctChain, board.fetchchainsize(defunctChain))*defunctStockInv['sell']
              #trade
              pDefuncting.stocks[defunctChain] -= defunctStockInv['trade']
              bank.stocks[defunctChain] += defunctStockInv['trade']
              pDefuncting.stocks[bigchain] += int(defunctStockInv['trade']/2)
              bank.stocks[bigchain] -= int(defunctStockInv['trade']/2)
              #stats
              pDefuncting.stats.stocksSold[-1] += defunctStockInv['sell']
              pDefuncting.stats.stocksTradedAway[-1] += defunctStockInv['trade']
              pDefuncting.stats.stocksAcquired[-1] += int(defunctStockInv['trade']/2)
              send_gameStateUpdate(tilebag, board, players, bank, clientMode)
              # endregion
              
              # region cycle pDefuncting
              if clientMode == "hostLocal":
                pDefunctingLoop, pDefuncting, defunctchains, defunctChain, pendingTileHandler = cycle_pDefuncting(pDefunctingLoop, defunctchains, turntile,
                                                                                                                  bigchain, defunctChain, pendingTileHandler)
                if pDefuncting is not None:
                  knob1_x = 0
                  knob2_x = pDefuncting.stocks[defunctChain]
                  tradeBanned = bank.stocks[bigchain] == 0 or knob2_x < 2
                else:
                  defunctMode = False
                  checkGameEndable = True; skipRender = True
                  if pendingTileHandler is not None:
                    turntile = pendingTileHandler
                    pendingTileHandler = None
              elif clientMode == "hostServer":
                defunctMode = False
                send_gameStateUpdate(tilebag, board, players, bank, clientMode)
                overflow_update(u, u_overflow, (my_uuid, Command("set player defunct", False)))
              else:
                  defunctMode = False
                  send_gameStateUpdate(tilebag, board, players, bank, clientMode)
                  propagate((my_uuid, Command("set player defunct", False)))
              # endregion
        
        #Post Draw Endgame and Buyability Check - SHOULD BE HIT EVERY TURN W/O FAIL
        elif checkGameEndable:
          checkGameEndable = False
          turnWrapup = True
          endGameConfirm = board.endgamecheck()
          buyPhase = len(board.fetchactivechains()) > 0 and any([bank.stocks[chain] for chain in board.fetchactivechains()]) and p.bal >= bank.fetchcheapeststock()[1]
          
          if buyPhase:
            askToBuy = True
            focus_content.clear("askToBuy"); forceRender = True
          if endGameConfirm:
            focus_content.clear("endGameConfirm"); forceRender = True
          if not endGameConfirm and not askToBuy:
            skipRender = True
        
        #Waiting for Player to Choose to End Game
        elif endGameConfirm:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = event.dict["pos"]
            # Check ask to end the game
            for i, yesorno_rect in enumerate(yesandno_rects):
              if yesorno_rect.collidepoint(pos):
                endGameConfirm = False
                focus_content.clear()
                if askToBuy:
                  focus_content.clear("askToBuy")
                if i == 1:
                  gameCompleted = True
                  propagate(players, None, Command("set game completed", gameCompleted))
                  if not clientMode == "hostLocal":
                    cyclingPlayers = False
        
        #Waiting for Player to Choose to Buy Stocks
        elif askToBuy:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = event.dict["pos"]
            # Check if askToBuy was clicked
            for i, yesorno_rect in enumerate(yesandno_rects):
              if yesorno_rect.collidepoint(pos):
                askToBuy = False
                if i == 1:
                  boughtthisturn = 0
                  stockcart = []
                  buyablechains = [chain for chain in board.fetchactivechains() if bank.stocks[chain] or chain in stockcart]
                  preBuyBal = p.bal
                  focus_content.clear("stockbuy")
                else:
                  buyPhase = False
        
        #Waiting to Buy and Handle Events in Buy Mode
        elif buyPhase:
          if event.type == pygame.MOUSEBUTTONDOWN:
            # Get the mouse position
            pos = event.dict["pos"]
            for i, stock_plusmin_rect in enumerate(stock_plusmin_rects):
              # print(newchain_rect, pos, newchain_rect.collidepoint(pos))
              if stock_plusmin_rect is not None and stock_plusmin_rect.collidepoint(pos) and buyablechains:
                buykey = buyablechains[i//2]
                if i%2 == 0: #minus
                  if buykey in stockcart: 
                    stockcart.remove(buykey); stockcart = [entry for entry in stockcart if entry != '']
                    p.stocks[buykey] -= 1
                    bank.stocks[buykey] += 1
                    p.bal += bank.stockcost(buykey, board.fetchchainsize(buykey) )
                    boughtthisturn -= 1
                    send_gameStateUpdate(tilebag, board, players, bank, clientMode)
                else: #plus
                  if boughtthisturn < 3:
                    if bank.stockcost(buykey, board.fetchchainsize(buykey)) > p.bal:
                      # print('Transaction Failed! You are too poor! :(')
                      pass
                    else:
                      stockcart.append(buykey); stockcart = [entry for entry in stockcart if entry != '']
                      p.stocks[buykey] += 1
                      bank.stocks[buykey] -= 1
                      p.bal -= bank.stockcost(buykey, board.fetchchainsize(buykey) )
                      boughtthisturn += 1
                      send_gameStateUpdate(tilebag, board, players, bank, clientMode)
                  else: 
                    # print('no cheating :(')
                    pass
            # Check if stockbuy close was clicked
            if stockbuy_confirm_rect.collidepoint(pos):
              p.stats.moneySpent[-1] += preBuyBal - p.bal
              p.stats.stocksAcquired[-1] += len(stockcart)
              for buykey in stockcart:
                p.stats.stockChainsOwned[-1].add(buykey)
              focus_content.clear()
              buyPhase = False
        
        # Turn Over
        elif turnWrapup:
          if cyclingPlayers and not gameCompleted:
            p.drawtile()
            p.deadduckremoval()
          send_gameStateUpdate(tilebag, board, players, bank, clientMode)
          ongoingTurn = False
          propagate(players, None, Command("set player turn", False))
      
      # endregion
      
      clock.tick(1 if VARIABLE_FRAMERATE and not pygame.key.get_focused() else MAX_FRAMERATE)
    
    # Host Iter Stats & Sync & Endgame
    if "host" in clientMode:
      if gameCompleted:
        # adds payouts directly to players' balance internally
        _ = bank.chainpayout(players, board.fetchactivechains())
        bank.sellallstock(players)
      
      assignStatVals(players)
      send_gameStateUpdate(tilebag, board, players, bank, clientMode)
  
  return gameCompleted, saveData
