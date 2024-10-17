import pygame
import os
from copy import copy, deepcopy

from objects import *
from objects.networking import DISCONN
from common import DIR_PATH, MAX_FRAMERATE, unpack_gameState

def config(gameUtils: tuple[pygame.Surface, pygame.time.Clock]) -> tuple[bool, str, bool | None, tuple[TileBag, Board, list[Player], Bank] | str]:
  global screen
  screen, clock = gameUtils
  from gui_fullscreen import draw_fullscreenSelect, draw_singleTextBox, draw_setPlayerNamesLocal, \
                             draw_selectSaveFile, draw_customSettings, draw_selectPlayerFromSave
  
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
        title = "Enter Host IP"; confirm_label = 'Connect'
        yesandno_rects = draw_singleTextBox(ipTxtbx, title, confirm_label)
      elif setPlayerNameHost:
        title = "Enter Your Username"; confirm_label = 'Start Server'
        yesandno_rects = draw_singleTextBox(playernameTxtbx, title, confirm_label)
      elif askHostLocal:
        yesandno_rects = draw_fullscreenSelect('hostLocal')
      elif askLoadSave:
        yesandno_rects = draw_fullscreenSelect('loadSave')
      elif selectSaveFile:
        drawinfo: tuple[bool, int, bool, int] = (hover_directory, hover_save_int, clicked_directory, clicked_save_int)
        saveinfo: tuple[str, list[str]] = (saves_path, savefiles)
        save_rects_vec = draw_selectSaveFile(drawinfo, saveinfo)
        directory_rect, savefile_rects, load_rect, back_button_rect = save_rects_vec
      elif selectPlayerFromSave:
        drawinfo = (hover_player_int, clicked_player_int)
        player_rects, load_rect, back_button_rect = draw_selectPlayerFromSave(drawinfo, players)
      elif setPlayerNamesLocal:
        text_field_rects, yesandno_rects, back_button_rect = draw_setPlayerNamesLocal(settings["playernames"], clicked_textbox_int)
      elif customSettings:
        drawnSettings = {**settings["board"], **settings["player"], **settings["bank"]}
        if settings["bank"]["Stock Pricing Function"] in {"Logarithmic", "Exponential"}:
          drawnSettings.update(**settings["bankLinear"])
        drawnSettings.update(**settings["bank" + settings["bank"]["Stock Pricing Function"]])
        text_field_rects, yesandno_rects, back_button_rect = draw_customSettings(drawnSettings, clicked_textbox_key, longestKey)
      # Update the display
      pygame.display.flip()
    # endregion
    
    # region Handle common events
    if event.type == pygame.QUIT:
      acquireSetup = False
      return successfullBoot, None, None, None
    elif event.type == pygame.VIDEORESIZE:
      # Apparently this is legacy code but idc
      screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
    # endregion
    
    if askHostJoin:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        # Check if askHostJoin was clicked
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            askHostJoin = False; forceRender = True
            if i == 1:
              askJoinCode = True
              ipTxtbx: str = ""
              newGame = None
            else:
              askHostLocal = True
    
    # possibly rework to make ip "." static on display
    # format ip as 4 sets of up to 3 digit numbers
    # or use join codes -> url -> ip tunnel
    elif askJoinCode: # only reachable for join
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            if i == 0:
              askJoinCode = False; forceRender = True
              askHostJoin = True
            else:
              # TODO valid ip checker
              if len(ipTxtbx) >= 7: # minimum 0.0.0.0 ip length
                askJoinCode = False; forceRender = True
                clientMode = "join"
                gameState: str = ipTxtbx
      elif event.type == pygame.KEYDOWN and pygame.key.get_focused():
        ipTxtbx: str = text.crunch_ip(event, ipTxtbx)
    
    elif askHostLocal:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        # Check if askHostJoin was clicked
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            askHostLocal = False; forceRender = True
            askLoadSave = True
            if i == 1:
              clientMode = "hostServer"
            else:
              clientMode = "hostLocal"
    
    elif askLoadSave:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        # Check if load save was clicked
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            askLoadSave = False; forceRender = True
            if i == 1:
              selectSaveFile = True
              newGame = False
              saves_path = DIR_PATH + r'\saves'
              savefiles = os.listdir(DIR_PATH + r'\saves'); savefiles.sort()
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
          selectSaveFile = False; forceRender = True
          askHostJoin = True
          clicked_textbox_int = None
        if hover_directory:
          clicked_directory = not clicked_directory
        elif clicked_directory and hover_save_int is not None:
          clicked_save_int = (hover_save_int if clicked_save_int != hover_save_int else None)
        elif clicked_save_int is not None and load_rect.collidepoint(pos):
          selectSaveFile = False; forceRender = True
          if clientMode == "hostServer":
            selectPlayerFromSave = True
            hover_player_int, clicked_player_int = [None]*2
          
          savefile = savefiles[clicked_save_int]
          with open(rf'{saves_path}\{savefile}', 'rb') as file:
            saveData = file.read()
          tilebag, board, players, bank = unpack_gameState(saveData)
          for p in players:
            p.conn = None
    
    elif selectPlayerFromSave: # only reachable for hostServer
      # Get the mouse position
      pos = pygame.mouse.get_pos()
      for i, player_rect in enumerate(player_rects):
        if player_rect.collidepoint(pos):
          hover_player_int = i
          break
        else:
          hover_player_int = None
      if event.type == pygame.MOUSEBUTTONDOWN:
        if back_button_rect.collidepoint(pos):
          selectPlayerFromSave = False; forceRender = True
          selectSaveFile = True
          saves_path = DIR_PATH + r'\saves'
          savefiles = os.listdir(DIR_PATH + r'\saves'); savefiles.sort()
          hover_directory, clicked_directory = [False]*2
          hover_save_int, clicked_save_int = [None]*2
        if hover_player_int is not None:
          clicked_player_int = (hover_player_int if clicked_player_int != hover_player_int else None)
        elif clicked_player_int is not None and load_rect.collidepoint(pos):
          selectPlayerFromSave = False; forceRender = True
          players[clicked_player_int].conn = Connection("host", None)
    
    elif customSettings:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if back_button_rect.collidepoint(pos):
          customSettings = False; forceRender = True
          askHostJoin = True
        for i, text_field_rect in enumerate(text_field_rects):
          clicked_textbox_key = None
          if text_field_rect.collidepoint(pos):
            clicked_textbox_key = list(drawnSettings.keys())[i]
            break
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            if i == 0:
              settings = deepcopy(stockGameSettings)
            else:
              customSettings = False; forceRender = True
              if clientMode == "hostLocal":
                setPlayerNamesLocal = True
                clicked_textbox_int = None
                settings["playernames"] = ["",] * int(settings["player"]["Max Players"])
              else:
                setPlayerNameHost = True
                playernameTxtbx = ""
                clicked_textbox_int = None
      elif event.type == pygame.KEYDOWN and clicked_textbox_key is not None and pygame.key.get_focused():
        settings, clicked_textbox_key = text.crunch_customSettings_nav(event, settings, clicked_textbox_key, list(drawnSettings.keys()))
    
    elif setPlayerNamesLocal: # only reachable for hostLocal
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if back_button_rect.collidepoint(pos):
          setPlayerNamesLocal = False; forceRender = True
          askHostJoin = True
        for i, text_field_rect in enumerate(text_field_rects):
          clicked_textbox_int = None
          if text_field_rect.collidepoint(pos):
            clicked_textbox_int = i
            break
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            if i == 0:
              setPlayerNamesLocal = False; forceRender = True
              customSettings = True
              clicked_textbox_key = None
            else:
              # minimum names filled
              if sum(['' != box for box in settings["playernames"]]) >= 2:
                setPlayerNamesLocal = False; forceRender = True
          
      elif event.type == pygame.KEYDOWN and clicked_textbox_int is not None and pygame.key.get_focused():
        clicked_textbox_int = text.nav_handler(event, settings["playernames"], clicked_textbox_int, 2)
        settings["playernames"][clicked_textbox_int] = text.crunch_playername(event, settings["playernames"][clicked_textbox_int])
    
    elif setPlayerNameHost: # only reachable for hostServer
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            if i == 0:
              setPlayerNameHost = False; forceRender = True
              askHostJoin = True
            else:
              if len(playernameTxtbx) >= 1:
                setPlayerNameHost = False; forceRender = True
                settings["playernames"][0] = playernameTxtbx
                gameState = None
      elif event.type == pygame.KEYDOWN and pygame.key.get_focused():
        playernameTxtbx: str = text.crunch_playername(event, playernameTxtbx)
    
    else: #prep for lobby
      if newGame:
        tilebag = TileBag(*settings["board"].values())
        board = Board(tilebag, settings["bank"]["Chain Size Cost Cap"])
        players: list[Player] = []
        for i, name in enumerate([p for p in settings["playernames"] if p != ""], start=1):
          players.append(Player(tilebag, board, name, i,
                                *settings["player"].values()))
        bank = Bank(tilebag, board,
                    *settings["bank"].values(),
                    *settings["bankClassic"].values(),
                    *settings["bankLogarithmic"].values(),
                    *settings["bankExponential"].values())
      if not clientMode == "join":
        gameState: tuple[TileBag, Board, list[Player], Bank] = (tilebag, board, players, bank)
      acquireSetup = False
      successfullBoot = True
      return successfullBoot, clientMode, newGame, gameState
    
    clock.tick(MAX_FRAMERATE if pygame.key.get_focused() else 1)

from uuid import UUID
from common import pack_gameState, find_player
from objects.networking import fetch_updates, propagate

def lobby(gameUtils: tuple[pygame.Surface, pygame.time.Clock], conn_dict: dict[UUID, Connection], clientMode: str, newGame: bool,
          gameState: tuple[TileBag, Board, list[Player], Bank] | None) -> tuple[bool, tuple[TileBag, Board, list[Player], Bank], UUID | None,  UUID | None]:  
  
  forceRender: bool = True
  inLobby: bool = True
  successfulStart: bool = False
  
  selectPlayerFromSave: bool = False
  setPlayerNameJoin: bool = False
  waitingForJoin: bool = False
  
  if clientMode == "hostLocal":
    successfulStart = True
    return successfulStart, gameState, None, None
  elif clientMode == "join":
    waitingForHandshake = True
    while waitingForHandshake:
      u = fetch_updates(conn_dict)
      for uuid, d in u:
        if d is not None and d.dump() == "set client connection":
          waitingForHandshake = False
          handshake: tuple[bool, bytes]= d.val
          newGame, gameStateUpdate = handshake
          gameState = unpack_gameState(gameStateUpdate, conn_dict)
          break
  
  screen, clock = gameUtils
  tilebag, board, players, bank = gameState
  from gui_fullscreen import draw_selectPlayerFromSave, draw_setPlayerNameJoin, draw_waitingForJoin
  
  def send_gameStateUpdate():
    gameStateUpdate = pack_gameState(tilebag, board, players, bank)
    target = "client" if clientMode == "hostServer" else "server"
    source = uuid if u_overflow is not None else None
    propagate(conn_dict, source, Command(f"set {target} gameState", gameStateUpdate))
  
  # host will always send own conn as Connection("host", None) and any clients as None
  HOST: Player = [p for p in players if p.conn is not None][0]
  host_uuid = HOST.uuid; my_uuid = None
  
  if clientMode == "hostServer":
    P = HOST
    my_uuid = P.uuid
    waitingForJoin = True
  else:
    # wait to assign HOST.conn = conn_dict["server"] until 
    # AFTER P = deepcopy(HOST)
    conn_dict["server"].uuid = host_uuid
    if newGame:
      setPlayerNameJoin = True
    else:
      selectPlayerFromSave = True
  
  u_overflow = None
  playernameTxtbx = ""
  hover_save_int, clicked_player_int = [None]*2
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
          p.DISCONN()
          if newGame:
            players.remove(p) # this should deref p
          else:
            p.conn = None
          del conn_dict[uuid] # this should deref p.conn
        
        elif comm.dump() == "set server gameState":
          gameStateUpdate: bytes = comm.val
          tilebag, board, players, bank = unpack_gameState(gameStateUpdate, conn_dict)
          u_overflow = copy(u); u = []
        
        elif comm.dump() == "set player uuid": # claim player from save
          p_uuid: UUID = comm.val
          newplayer = find_player(p_uuid, players)
          if newplayer.connClaimed: # prevent race condition
            print(f"invalid claim of player {newplayer.name} by {conn_dict[uuid]}")
            # TODO add a dedicated error handler / propogator
            continue
          newplayer.conn = conn_dict[uuid]
          print(f"{newplayer.name} joined")
        
        elif comm.dump() == "set player ready":
          readiness: bool = comm.val
          find_player(uuid, players).ready = readiness
        
        send_gameStateUpdate()
      
      else:
        # command recieved from server
        if comm.dump() == "set client connection" and comm.val == DISCONN:
          print(f"You have been disconnected.")
          inLobby = False
          successfulStart = False
        
        elif comm.dump() == "set client gameState":
          gameStateUpdate: bytes = comm.val
          tilebag, board, players, bank = unpack_gameState(gameStateUpdate, conn_dict)
        
        elif comm.dump() == "set game start" and comm.val:
          waitingForJoin = False
      
      connected_players: list[Player] = [p for p in players if p.connClaimed]
      unclaimed_players: list[Player] = [p for p in players if not p.connClaimed]
      forceRender = True
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
        confirm_rect = draw_setPlayerNameJoin(playernameTxtbx)
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
      # Apparently this is legacy code but idc
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
        elif clicked_player_int is not None and load_rect.collidepoint(pos):
          selectPlayerFromSave = False
          P: Player = unclaimed_players[clicked_player_int]
          HOST.conn.send(Command("set player uuid", P.uuid))
          clicked_player_int: int | None = None
    
    elif setPlayerNameJoin:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if confirm_rect.collidepoint(pos) and len(playernameTxtbx) >= 2:
          setPlayerNameJoin = False
          waitingForJoin = True
          P = deepcopy(HOST)
          HOST.conn = conn_dict["server"]
          my_uuid = P.uuid
          P.setGameObj(tilebag, board)
          P.conn = Connection("client", None)
          P.name = (playernameTxtbx, len(players)+1)
          players.append(P)
          HOST.conn.send(Command("set server gameState", pack_gameState(tilebag, board, players, bank)))
          clicked_player_int: int | None = None; forceRender = True
      elif event.type == pygame.KEYDOWN and pygame.key.get_focused():
        playernameTxtbx: str = text.crunch_playername(event, playernameTxtbx)
    
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
                p.DISCONN()
                if newGame:
                  players.remove(p) # this should deref p -> kill
                else:
                  p.conn = None
                del conn_dict[p.uuid] # this should deref p.conn
                send_gameStateUpdate()
              else:
                # start game                      (requires all savedPlayers are connected)
                if len(connected_players) >= 2 and len(connected_players) == len(players) and all([p.ready for p in connected_players]):
                  waitingForJoin = False
                  propagate(conn_dict, None, Command("set game start", True))
        elif event.type == pygame.KEYDOWN and clicked_player_int is not None and pygame.key.get_focused():
          clicked_player_int = text.nav_handler(event, connected_players, clicked_player_int, 2)
      
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
                P.ready = not P.ready
                HOST.conn.send(Command("set player ready", not P.ready))
        elif event.type == pygame.KEYDOWN and clicked_player_int is not None and pygame.key.get_focused():
          clicked_player_int = text.nav_handler(event, connected_players, clicked_player_int, 2)
    
    else: #prep for game startup
      successfulStart = True
      inLobby = False
      gameState = (tilebag, board, players, bank)
    
    clock.tick(MAX_FRAMERATE if pygame.key.get_focused() else 1)
  
  return successfulStart, gameState, host_uuid, my_uuid
