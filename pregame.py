import pygame
from pygame import Surface
from pygame.time import Clock
import os
import pickle
import text
from copy import deepcopy

from objects.tilebag import TileBag
from objects.board import Board
from objects.player import Player
from objects.bank import Bank

from common import DIR_PATH, MAX_FRAMERATE, unpack_gameState
from networking import Connection
from gui_fullscreen import draw_fullscreenSelect, draw_joinCode, draw_setPlayerNameHost, \
     draw_setPlayerNamesLocal, draw_selectSaveFile, draw_customSettings, draw_selectPlayerFromSave

def config(screen: Surface, clock: Clock) -> tuple[bool, str, bool | None, tuple[TileBag, Board, list[Player], Bank] | str]:
  # region define statemap & defaults
  stockGameSettings = {
    "board": {
      "Board Length": "12",
      "Board Height": "9",
      "Economy Chains": "2",
      "Standard Chains": "3",
      "Luxury Chains": "2",
    },
    "player": {
      "Player Starting Stock": "0",
      "Player Starting Cash": "6000",
      "Player Tiles Held": "6",
      "Max Players": "6",
    },
    "bank": {
      "Total Stock Per Chain": "25",
      "Global Cost Offset": "0",
      "Global Cost Multiplier": "1",
      "Stock Pricing Function": "Classic",
      "Linear Cost Slope": "100",
      "Prestige Fee": "100",
      "Chain Size Cost Cap": "41",
    },
    "bankClassic": {
      "Chain Size Boundary": "5",
    },
    "bankLinear": {
      "Linear Cost Offset": "600",
    },
    "bankLogarithmic": {
      "Pre-Logarithm Stretch": "1.5",
      "Logarithmic Base": "2.6",
    },
    "bankExponential": {
      "Pre-Exponential Divisor": "240",
      "Exponential Power": "2",
      "Exponential Offset Reducer": "3",
    },
    "playernames": ["",] * 6
  }
  longestKey = max([ max([len(k) for k in d.keys()]) for d in stockGameSettings.values() if type(d) == dict])
  
  forceRender: bool = True
  acquireSetup: bool = True
  successfullBoot: bool = False
  newGame: bool | None = None
  
  askHostJoin: bool = True
  askJoinCode: bool = False
  askHostLocal: bool = False
  askLoadSave: bool = False
  selectSaveFile: bool = False
  selectPlayerFromSave: bool = False
  setPlayerNamesLocal: bool = False
  setPlayerNameHost: bool = False
  customSettings: bool = False
  
  popup_open: bool = False
  # endregion
  
  while acquireSetup:
    event = pygame.event.poll()
    # region Render Process
    if forceRender or event.type:
      forceRender = False
      # Clear the screen
      screen.fill((255, 255, 255))
      #Draw depending on current state
      if askHostJoin:
        yesandno_rects = draw_fullscreenSelect('hostJoin')
      elif askJoinCode:
        text_field_rect, yesandno_rects = draw_joinCode(ipTxtbx, clicked_textbox)
      elif setPlayerNameHost:
        text_field_rect, yesandno_rects = draw_setPlayerNameHost(playernameTxtbx, clicked_textbox)
      elif askHostLocal:
        yesandno_rects = draw_fullscreenSelect('hostLocal')
      elif askLoadSave:
        yesandno_rects = draw_fullscreenSelect('loadSave')
      elif selectSaveFile:
        drawinfo = (hover_directory, hover_save_int, clicked_directory, clicked_save_int)
        saveinfo = (saves_path, savefiles)
        save_rects_vec = draw_selectSaveFile(drawinfo, saveinfo)
        directory_rect, savefile_rects, load_rect, back_button_rect = save_rects_vec
      elif selectPlayerFromSave:
        drawinfo = (hover_player_int, clicked_player_int)
        player_rects, load_rect = draw_selectPlayerFromSave(drawinfo, players)
      elif setPlayerNamesLocal:
        text_field_rects, yesandno_rects = draw_setPlayerNamesLocal(settings["playernames"], clicked_textbox_int)
      elif customSettings:
        drawnSettings = {**settings["board"], **settings["player"], **settings["bank"]}
        if settings["bank"]["Stock Pricing Function"] in {"Logarithmic", "Exponential"}:
          drawnSettings.update(**settings["bankLinear"])
        drawnSettings.update(**settings["bank" + settings["bank"]["Stock Pricing Function"]])
        text_field_rects, yesandno_rects = draw_customSettings(drawnSettings, clicked_textbox_key, longestKey)
      # Update the display
      pygame.display.flip()
    # endregion
    
    # region Handle common events
    if event.type == pygame.QUIT:
      acquireSetup = False
      return successfullBoot, None, None, None
    elif event.type == pygame.VIDEORESIZE:
      # Update the window size
      screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
    # endregion
    
    if askHostJoin:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if not popup_open:
          # Check if askHostJoin was clicked
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              askHostJoin = False
              if i == 1:
                askJoinCode = True
                ipTxtbx: str = ""
                newGame = None
              else:
                askHostLocal = True
    
    # possibly rework to make ip "." static on display
    # format ip as 4 sets of up to 3 digit numbers
    # or use join codes -> url -> ip tunnel
    elif askJoinCode:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            if i == 0:
              askJoinCode = False
              askHostJoin = True
            else:
              # TODO valid ip checker
              if not popup_open and len(ipTxtbx) >= 7: # minimum 0.0.0.0 ip length
                askJoinCode = False
                clientMode = "join"
                gameState: str = ipTxtbx
      elif event.type == pygame.KEYDOWN and pygame.key.get_focused():
        ipTxtbx: str = text.crunch_ip(ipTxtbx)
    
    elif askHostLocal:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if not popup_open:
          # Check if askHostJoin was clicked
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              askHostLocal = False
              askLoadSave = True
              if i == 1:
                clientMode = "hostServer"
              else:
                clientMode = "hostLocal"
    
    elif askLoadSave:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if not popup_open:
          # Check if load save was clicked
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              askLoadSave = False
              if i == 1:
                selectSaveFile = True
                newGame = False
                saves_path = DIR_PATH + r'\saves'
                savefiles = os.listdir(DIR_PATH + r'\saves')
                hover_directory, clicked_directory = [False]*2
                hover_save_int, clicked_save_int = [None]*2
              else:
                customSettings = True
                newGame = True
                clicked_textbox_key = None
                settings = deepcopy(stockGameSettings)
    
    elif selectSaveFile:
      # Get the mouse position
      pos = pygame.mouse.get_pos()
      if directory_rect.collidepoint(pos):
        hover_directory = True
      else:
        hover_directory = False
        if clicked_directory:
          hover_save_int = None
          for i, savefile_rect in enumerate(savefile_rects):
            if savefile_rect.collidepoint(pos):
              hover_save_int = i
              break
        else:
          hover_save_int = None
      if event.type == pygame.MOUSEBUTTONDOWN:
        if back_button_rect.collidepoint(pos):
          selectSaveFile = False
          askHostJoin = True
          clicked_textbox_int = None
        if hover_directory:
          clicked_directory = not clicked_directory
        elif clicked_directory and hover_save_int is not None:
          clicked_save_int = (hover_save_int if clicked_save_int != hover_save_int else None)
        elif clicked_save_int is not None and load_rect.collidepoint(pos):
          selectSaveFile = False
          savefile = savefiles[clicked_save_int]
          with open(rf'{saves_path}\{savefile}', 'rb') as file:
            saveData = pickle.load(file)
          
          selectPlayerFromSave = True
          tilebag, board, players, bank = unpack_gameState(saveData)
          for p in players:
            p.__setConn(None)
          hover_save_int, clicked_save_int = [None]*2
    
    elif selectPlayerFromSave:
      # Get the mouse position
      pos = pygame.mouse.get_pos()
      for i, player_rect in enumerate(player_rects):
        if player_rect.collidepoint(pos):
          hover_player_int = i
          break
        else:
          hover_player_int = None
      if event.type == pygame.MOUSEBUTTONDOWN:
        if hover_save_int is not None:
          clicked_player_int = (hover_save_int if clicked_player_int != hover_save_int else None)
        elif clicked_save_int is not None and load_rect.collidepoint(pos):
          selectPlayerFromSave = False
          players[clicked_save_int].__setConn(Connection("host"))
          gameState: tuple[TileBag, Board, list[Player], Bank] = (tilebag, board, players, bank)
    
    elif customSettings:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        for i, text_field_rect in enumerate(text_field_rects):
          clicked_textbox_key = None
          if text_field_rect.collidepoint(pos):
            clicked_textbox_key = list(drawnSettings.keys())[i]
            break
        if not popup_open:
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              if i == 0:
                settings = deepcopy(stockGameSettings)
              else:
                customSettings = False
                if clientMode == "hostLocal":
                  setPlayerNamesLocal = True
                  clicked_textbox_int = None
                  settings["playernames"] = ["",] * int(settings["player"]["Max Players"])
                else:
                  setPlayerNameHost = True
                  playernameTxtbx = ""
                  clicked_textbox = None
      elif event.type == pygame.KEYDOWN and clicked_textbox_key is not None and pygame.key.get_focused():
        settings, clicked_textbox_key = text.crunch_customSettings_nav(settings, clicked_textbox_key, list(drawnSettings.keys()))
    
    elif setPlayerNamesLocal:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        for i, text_field_rect in enumerate(text_field_rects):
          clicked_textbox_int = None
          if text_field_rect.collidepoint(pos):
            clicked_textbox_int = i
            break
        if not popup_open and sum(['' != box for box in settings["playernames"]]) >= 2:
          # minimum names filled, check for click to go to settings
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              setPlayerNamesLocal = False
              if i == 0:
                customSettings = True
                clicked_textbox_key = None
      elif event.type == pygame.KEYDOWN and clicked_textbox_int is not None and pygame.key.get_focused():
        settings["playernames"], clicked_textbox_int = text.nav_handler(settings["playernames"], clicked_textbox_int)
        settings["playernames"], clicked_textbox_int = text.crunch_playername(settings["playernames"], clicked_textbox_int)
    
    elif setPlayerNameHost:
      if event.type == pygame.MOUSEBUTTONDOWN:
        clicked_textbox = False
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if text_field_rect.collidepoint(pos):
          clicked_textbox = True
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            if i == 0:
              setPlayerNameHost = False
              askHostJoin = True
            else:
              if not popup_open and len(playernameTxtbx) >= 2:
                setPlayerNameHost = False
                settings["playernames"][0] = playernameTxtbx
                gameState = None
      elif event.type == pygame.KEYDOWN and clicked_textbox and pygame.key.get_focused():
        playernameTxtbx = text.crunch_playername(playernameTxtbx)
    
    else: #prep for lobby
      if newGame:
        tilebag = TileBag(*settings["board"].values())
        board = Board(tilebag, settings["bank"]["Chain Size Cost Cap"])
        players: list[Player] = []
        for i, name in enumerate([p for p in settings["playernames"] if p != ""]):
          players.append(Player(tilebag, board, name, i 
                                *settings["player"].values()))
        bank = Bank(tilebag, board,
                    *settings["bank"].values(),
                    *settings["bankClassic"].values(),
                    *settings["bankLogarithmic"].values(),
                    *settings["bankExponential"].values())
        gameState: tuple[TileBag, Board, list[Player], Bank] = (tilebag, board, players, bank)
      
      acquireSetup = False
      successfullBoot = True
      return successfullBoot, clientMode, newGame, gameState
    
    clock.tick(MAX_FRAMERATE)


from uuid import UUID
from common import pack_gameState, find_player
from networking import DISCONN, Command, fetch_updates, propagate
from gui_fullscreen import draw_waitingForJoin, draw_setPlayerNameJoin

def lobby(screen: Surface, clock: Clock, conn_dict: dict[UUID, Connection], clientMode: str, newGame: bool,
          gameState: tuple[TileBag, Board, list[Player], Bank] | None) -> tuple[bool, tuple[TileBag, Board, list[Player], Bank]]:  
  
  forceRender: bool = True
  inLobby: bool = True
  successfulStart: bool = False
  
  selectPlayerFromSave: bool = False
  setPlayerNameJoin: bool = False
  waitingForJoin: bool = False
  
  if clientMode == "hostLocal":
    successfulStart = True
    return successfulStart, gameState
  elif clientMode == "join":
    waitingForHandshake = True
    while waitingForHandshake:
      u, _ = fetch_updates(conn_dict)
      for uuid, d in u:
        if d is not None and d.dump() == "set client connection":
          waitingForHandshake = False
          handshake: tuple[bool, bytes]= d.val
          newGame, gameStateUpdate = handshake
          gameState = unpack_gameState(gameStateUpdate)
          break
  
  tilebag, board, players, bank = gameState
  HOST: Player = [p for p in players if p.conn is not None][0]
  
  if clientMode == "hostServer":
    P = HOST
    waitingForJoin = True
    clicked_player_int: int | None = None
  else:
    HOST.conn = conn_dict["server"]
    HOST.conn.uuid = HOST.uuid
    if newGame:
      setPlayerNameJoin = True
      playernameTxtbx = ""
    else:
      selectPlayerFromSave = True
      hover_save_int, clicked_save_int = [None]*2
  
  u_overflow = None
  connected_players: list[Player] = [p for p in players if p.connClaimed] # == players if newGame
  unclaimed_players: list[Player] = [p for p in players if not p.connClaimed] # == [] if newGame
  
  while inLobby:
    # region check for updates over network
    u = fetch_updates(conn_dict) if u_overflow is None else u_overflow
    while len(u):
      uuid, comm = u.pop(0)
      if clientMode == "hostServer":
        # command revieved from clients
        if comm.dump() == "set server connection" and comm.val == DISCONN:
          print(f"{conn_dict[uuid].addr} disconnected.")
          p = find_player(uuid, players)
          p.conn.kill()
          if newGame:
            players.remove(p) # this should deref p
          else:
            p.__setConn(None)
          del conn_dict[uuid] # this should deref p.conn
        
        elif comm.dump() == "set server gameState":
          gameStateUpdate: bytes = comm.val
          tilebag, board, players, bank = unpack_gameState(gameStateUpdate)
          u_overflow = deepcopy(u); u = []
        
        elif comm.dump() == "set player uuid":
          p_uuid: UUID = comm.val
          newplayer = find_player(p_uuid, players)
          if newplayer.connClaimed: # prevent race condition
            print(f"invalid claim of player {newplayer.truename}")
            # TODO add a dedicated error handler / propogator
            continue
          newplayer.__setConn(conn_dict[uuid])
          print(f"player {newplayer.name} joined")
        
        elif comm.dump() == "set player ready":
          readiness: bool = comm.val
          find_player(uuid, players).ready = readiness
        
        gameStateUpdate = pack_gameState(tilebag, board, players, bank)
        propagate(conn_dict, uuid if u_overflow else None, Command("set client gameState", gameStateUpdate))
      
      else:
        # command recieved from server
        if comm.dump() == "set client connection" and comm.val == DISCONN:
          print(f"You have been disconnected.")
          inLobby = False
          successfulStart = False
        
        elif comm.dump() == "set client gameState":
          gameStateUpdate: bytes = comm.val
          tilebag, board, players, bank = unpack_gameState(gameStateUpdate)
      
      connected_players: list[Player] = [p for p in players if p.connClaimed]
      unclaimed_players: list[Player] = [p for p in players if not p.connClaimed]
    # endregion
    
    event = pygame.event.poll()
    # region Render Process
    if forceRender or event.type:
      forceRender = False
      # Clear the screen
      screen.fill((255, 255, 255))
      #Draw depending on current state
      if selectPlayerFromSave:
        drawinfo = (hover_player_int, clicked_player_int)
        player_rects, load_rect = draw_selectPlayerFromSave(drawinfo, unclaimed_players)
      elif setPlayerNameJoin:
        text_field_rect, confirm_rect = draw_setPlayerNameJoin(playernameTxtbx, clicked_textbox)
      else:
        player_rects, yesandno_rects = draw_waitingForJoin(clientMode, connected_players, clicked_player_int)
      # Update the display
      pygame.display.flip()
    # endregion
    
    # region Handle common events
    if event.type == pygame.QUIT:
      inLobby = False
      successfulStart = False
    elif event.type == pygame.VIDEORESIZE:
      # Update the window size
      screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
    # endregion
    
    if selectPlayerFromSave:
      # Get the mouse position
      pos = pygame.mouse.get_pos()
      for i, player_rect in enumerate(player_rects):
        if player_rect.collidepoint(pos):
          hover_player_int = i
          break
        else:
          hover_player_int = None
      if event.type == pygame.MOUSEBUTTONDOWN:
        if hover_save_int is not None:
          clicked_player_int = (hover_save_int if clicked_player_int != hover_save_int else None)
        elif clicked_save_int is not None and load_rect.collidepoint(pos):
          selectPlayerFromSave = False
          P: Player = unclaimed_players[clicked_player_int]
          HOST.conn.send(Command("set player uuid", P.uuid))
          clicked_player_int: int | None = None
    
    elif setPlayerNameJoin:
      if event.type == pygame.MOUSEBUTTONDOWN:
        clicked_textbox = False
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if text_field_rect.collidepoint(pos):
          clicked_textbox = True
        elif confirm_rect.collidepoint(pos) and len(playernameTxtbx) >= 2:
          setPlayerNameJoin = False
          P = deepcopy(HOST)
          P.__setObjLinks(tilebag, board)
          P.__setName(playernameTxtbx, len(players)+1)
          players.append(P)
          HOST.conn.send(Command("set server gameState", pack_gameState(tilebag, board, players, bank)))
      elif event.type == pygame.KEYDOWN and clicked_textbox and pygame.key.get_focused():
        playernameTxtbx = text.crunch_playername(playernameTxtbx)
    
    elif waitingForJoin:
      if clientMode == "hostServer":
        if event.type == pygame.MOUSEBUTTONDOWN:
          # Get the mouse position
          pos = pygame.mouse.get_pos()
          for i, player_rect in enumerate(player_rects):
            clicked_player_int = None
            if player_rect.collidepoint(pos):
              clicked_player_int = i
              break
          # perform actions
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              if i == 0 and clicked_player_int is not None:
                p = connected_players[clicked_player_int]
                p.conn.send(Command("set client connection", DISCONN))
                p.conn.kill()
                if newGame:
                  players.remove(p) # this should deref p -> kill
                else:
                  p.__setConn(None)
                del conn_dict[p.uuid] # this should deref p.conn
              else:
                # start game (requires all savedPlayers are connected)
                if len(connected_players) >= 2 and len(connected_players) == len(players) and all([p.ready for p in connected_players]):
                  waitingForJoin = False
                  # TODO tell clients to start game
        elif event.type == pygame.KEYDOWN and clicked_player_int is not None and pygame.key.get_focused():
          playernames, clicked_player_int = text.nav_handler(playernames, clicked_player_int)
      
      else:
        if event.type == pygame.MOUSEBUTTONDOWN:
          # Get the mouse position
          pos = pygame.mouse.get_pos()
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              if i == 0:
                HOST.conn.send(Command("set server connection", DISCONN))
                inLobby = False
                successfulStart = False
              else:
                # mark ready
                HOST.conn.send(Command("set player ready", not P.ready))
                pass
        elif event.type == pygame.KEYDOWN and clicked_player_int is not None and pygame.key.get_focused():
          playernames, clicked_player_int = text.nav_handler(playernames, clicked_player_int)
    
    else: #prep for game startup
      successfulStart = True
      gameState = (tilebag, board, players, bank)
    
    clock.tick(MAX_FRAMERATE)
  
  return successfulStart, gameState
