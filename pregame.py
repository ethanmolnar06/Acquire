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
      if "host" in clientMode:
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
  gameStartable: bool = False
  
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
          handshake: tuple[UUID, bool, bytes]= d.val
          my_uuid, newGame, gameStateUpdate = handshake
          gameState = unpack_gameState(gameStateUpdate, conn_dict)
          break
  
  screen, clock = gameUtils
  tilebag, board, players, bank = gameState
  from gui_fullscreen import draw_selectPlayerFromSave, draw_setPlayerNameJoin, draw_waitingForJoin
  
  # host will always send own conn as Connection("host", None) and any clients as None
  HOST: Player = [p for p in players if p.conn is not None][0]
  host_uuid = HOST.uuid; P = None
  
  if clientMode == "hostServer":
    P = HOST; my_uuid = host_uuid
    conn_dict[my_uuid] = P.conn
    waitingForJoin = True
  else:
    # sync client's version of host uuid to host's version of host uuid
    conn_dict["server"].uuid = host_uuid
    conn_dict[host_uuid] = conn_dict["server"]
    del conn_dict["server"]
    HOST.conn = conn_dict[host_uuid]
    print(f"[HANDSHAKE COMPLETE] Client Connected to {conn_dict[host_uuid]}")
    if newGame:
      setPlayerNameJoin = True
    else:
      selectPlayerFromSave = True
      awaitResponse = False
  
  u_overflow = None
  playernameTxtbx = ""
  hover_save_int, clicked_player_int = [None]*2
  connected_players: list[Player] = [p for p in players if p.connClaimed] # == players if newGame
  unclaimed_players: list[Player] = [p for p in players if not p.connClaimed] # == [] if newGame
  
  def send_gameStateUpdate():
    gameStateUpdate = pack_gameState(tilebag, board, players, bank)
    target = "client" if clientMode == "hostServer" else "server"
    propagate(conn_dict, None, Command(f"set {target} gameState", gameStateUpdate))
  
  def overflow_update(update: tuple[UUID, Command] | None):
    global u, u_overflow
    # try to be super safe, not drop any updates in either queue
    if update is not None:
      u_overflow += [update,]
    u_overflow += copy(u) 
    u = []
  
  while inLobby:
    # region check for updates over network
    u = fetch_updates(conn_dict) if not u_overflow else u_overflow
    while len(u):
      uuid, comm = u.pop(0)
      if clientMode == "hostServer":
        # command revieved from clients
        if comm.dump() == "set server connection" and comm.val == DISCONN:
          p = find_player(uuid, players)
          print(f"[PLAYER DROPPED] Disconnect Message Recieved from {p.conn}")
          p.DISCONN()
          if newGame:
            players.remove(p) # this should deref p
          else:
            p.conn = None
          del conn_dict[uuid] # this should deref p.conn
        
        elif comm.dump() == "set player name": # create new player
          newplayer: Player = comm.val
          newplayer.setGameObj(tilebag, board)
          newplayer.conn = conn_dict[uuid]
          players.append(newplayer)
          overflow_update()
        
        elif comm.dump() == "set player uuid": # claim player from save
          sel_p_uuid: UUID = comm.val
          newplayer = find_player(sel_p_uuid, players)
          if newplayer.connClaimed: # prevent race condition
            print(f"[PLAYER CLAIM ERROR] Invalid Claim of {newplayer.name} from {p.conn}")
            conn_dict[uuid].send(Command("set client selectionConfirmed", False))
            continue
          # overwrite old sel_p_uuid with client conn's real uuid
          newplayer.conn = conn_dict[uuid]
          print(f"[PLAYER CLAIMED] {newplayer.name} Claimed by {p.conn}")
          newplayer.conn.send(Command("set client selectionConfirmed", True))
          overflow_update()
        
        elif comm.dump() == "set player ready":
          readiness: bool = comm.val
          find_player(uuid, players).ready = readiness
        
        send_gameStateUpdate()
      
      else:
        # command recieved from server
        if comm.dump() == "set client connection" and comm.val == DISCONN:
          # will break if P not yet set for client, but this *shouldn't* be possible
          P.DISCONN()
          inLobby = False
          successfulStart = False
        
        elif comm.dump() == "set client gameState":
          gameStateUpdate: bytes = comm.val
          tilebag, board, players, bank = unpack_gameState(gameStateUpdate, conn_dict)
        
        elif comm.dump() == "set client selectionConfirmed":
          awaitResponse = False
          if d.val:
            selectPlayerFromSave = False
            try:
              P = find_player(sel_p_uuid, players)
              sel_p_uuid = None
            except:
              # catch for if "set client gameState" Command somehow beats "set client selectionConfirmed"
              P = find_player(my_uuid, players)
            P.conn = Connection("client", None, my_uuid)
            conn_dict[my_uuid] = P.conn
        
        elif comm.dump() == "set game start" and comm.val:
          waitingForJoin = False
      
      connected_players: list[Player] = [p for p in players if p.connClaimed]
      unclaimed_players: list[Player] = [p for p in players if not p.connClaimed]
      gameStartable = len(connected_players) >= 2 and len(connected_players) == len(players) and all([p.ready for p in connected_players])
      HOST = find_player(host_uuid, players)
      if my_uuid in [p.uuid for p in players]:
        P = find_player(my_uuid, players)
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
        player_rects, yesandno_rects = draw_waitingForJoin(clientMode, connected_players, clicked_player_int, gameStartable)
      # Update the display
      pygame.display.flip()
    # endregion
    
    # region Handle common events
    if event.type == pygame.QUIT:
      target = "client" if clientMode == "hostServer" else "server"
      propagate(conn_dict, None, Command(f"set {target} connection", DISCONN))
      P.DISCONN()
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
      if event.type == pygame.MOUSEBUTTONDOWN and not awaitResponse:
        if hover_save_int is not None:
          clicked_player_int = (hover_save_int if clicked_player_int != hover_save_int else None)
        elif clicked_player_int is not None and load_rect.collidepoint(pos):
          sel_p_uuid = unclaimed_players[clicked_player_int].uuid
          HOST.conn.send(Command("set player uuid", sel_p_uuid))
          clicked_player_int: int | None = None
          awaitResponse = True
    
    elif setPlayerNameJoin:
      print(HOST, HOST.conn.sock)
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if confirm_rect.collidepoint(pos) and len(playernameTxtbx) >= 2:
          setPlayerNameJoin = False
          waitingForJoin = True
          HOST.conn = None
          P = deepcopy(HOST)
          HOST.conn = conn_dict[host_uuid]
          P.setGameObj(tilebag, board)
          P.conn = Connection("client", None, my_uuid)
          conn_dict[my_uuid] = P.conn
          P.name = (playernameTxtbx, len(players)+1)
          players.append(P)
          HOST.conn.send(Command("set player name", P))
          connected_players: list[Player] = [p for p in players if p.connClaimed]
          unclaimed_players: list[Player] = [p for p in players if not p.connClaimed]
          forceRender = True
          clicked_player_int: int | None = None
      elif event.type == pygame.KEYDOWN and pygame.key.get_focused():
        playernameTxtbx: str = text.crunch_playername(event, playernameTxtbx)
    
    elif waitingForJoin:
      if clientMode == "hostServer":
        if event.type == pygame.MOUSEBUTTONDOWN:
          # Get the mouse position
          pos = pygame.mouse.get_pos()
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              if i == 0 and clicked_player_int is not None:
                p = connected_players[clicked_player_int]
                if p == HOST:
                  break
                p.conn.send(Command("set client connection", DISCONN))
                p.DISCONN()
                if newGame:
                  players.remove(p) # this should deref p -> kill
                else:
                  p.conn = None
                del conn_dict[p.uuid] # this should deref p.conn
                send_gameStateUpdate()
                connected_players: list[Player] = [p for p in players if p.connClaimed]
                unclaimed_players: list[Player] = [p for p in players if not p.connClaimed]
                gameStartable = len(connected_players) >= 2 and len(connected_players) == len(players) and all([p.ready for p in connected_players])
                forceRender = True
                break
              elif i == 1:
                P.ready = not P.ready
                send_gameStateUpdate()
                #                                              (requires all savedPlayers are connected)
                gameStartable = len(connected_players) >= 2 and len(connected_players) == len(players) and all([p.ready for p in connected_players])
                forceRender = True
                break
              elif i == 2:
                gameStartable = len(connected_players) >= 2 and len(connected_players) == len(players) and all([p.ready for p in connected_players])
                if gameStartable:
                  waitingForJoin = False
                  propagate(conn_dict, None, Command("set game start", True))
          for i, player_rect in enumerate(player_rects):
            clicked_player_int = None
            if player_rect.collidepoint(pos):
              clicked_player_int = i
              break
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
                P.DISCONN()
                inLobby = False
                successfulStart = False
              else:
                P.ready = not P.ready
                HOST.conn.send(Command("set player ready", P.ready))
        elif event.type == pygame.KEYDOWN and clicked_player_int is not None and pygame.key.get_focused():
          clicked_player_int = text.nav_handler(event, connected_players, clicked_player_int, 2)
    
    else: #prep for game startup
      successfulStart = True
      inLobby = False
      gameState = (tilebag, board, players, bank)
    
    clock.tick(MAX_FRAMERATE if pygame.key.get_focused() else 1)
  
  return successfulStart, gameState, host_uuid, my_uuid
