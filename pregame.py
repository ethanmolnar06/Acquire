import pygame
import os
import pickle
import text
from copy import copy, deepcopy
from uuid import UUID

from objects.tilebag import TileBag
from objects.board import Board
from objects.player import Player
from objects.bank import Bank

from common import DIR_PATH, HIDE_PERSONAL_INFO, ALLOW_SAVES, ALLOW_QUICKSAVES, MAX_FRAMERATE, \
                   pack_save, unpack_save
from gui_fullscreen import draw_fullscreenSelect, draw_joinCode, draw_setPlayerNameJoin, \
     draw_setPlayerNamesLocal, draw_selectSaveFile, draw_customSettings, draw_waitingForJoin, \
     draw_selectPlayerFromSave

def config(screen: pygame.Surface, clock: pygame.time.Clock) -> tuple[bool, str, bool | None, bytes | tuple[str, str]]:
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
  
  acquireSetup: bool = True
  successfullBoot: bool = False
  newGame: bool | None = None
  
  askHostJoin: bool = True
  askJoinCode: bool = False
  setPlayerNameJoin: bool = False
  askHostLocal: bool = False
  askLoadSave: bool = False
  selectSaveFile: bool = False
  selectPlayerFromSave: bool = False
  setPlayerNamesLocal: bool = False
  setPlayerNameHost: bool = False
  customSettings: bool = False
  
  popup_open: bool = False
  while acquireSetup:
    # region Render Process
    # Clear the screen
    screen.fill((255, 255, 255))
    #Draw depending on current state
    if askHostJoin:
      yesandno_rects = draw_fullscreenSelect('hostJoin')
    elif askJoinCode:
      text_field_rect, yesandno_rects = draw_joinCode(ipTxtbx, clicked_textbox)
    elif setPlayerNameJoin or setPlayerNameHost:
      text_field_rect, yesandno_rects = draw_setPlayerNameJoin(playernameTxtbx, clicked_textbox)
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
    event = pygame.event.poll()
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
                ipTxtbx = ""
                clicked_textbox = False
              else:
                askHostLocal = True
    
    # possibly rework to make ip "." static on display
    # format ip as 4 sets of up to 3 digit numbers
    # or use join codes -> url -> ip tunnel
    elif askJoinCode:
      if event.type == pygame.MOUSEBUTTONDOWN:
        clicked_textbox = False
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if text_field_rect.collidepoint(pos):
          clicked_textbox = True
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            if i == 0:
              askJoinCode = False
              askHostJoin = True
            else:
              # TODO valid ip checker
              if not popup_open and len(ipTxtbx) >= 7: # minimum 0.0.0.0 ip length
                askJoinCode = False
                setPlayerNameJoin = True
                playernameTxtbx = ""
      elif event.type == pygame.KEYDOWN and clicked_textbox and pygame.key.get_focused():
        ipTxtbx = text.interface("ip", ipTxtbx)
    
    elif setPlayerNameJoin:
      if event.type == pygame.MOUSEBUTTONDOWN:
        clicked_textbox = False
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if text_field_rect.collidepoint(pos):
          clicked_textbox = True
        for i, yesorno_rect in enumerate(yesandno_rects):
          if yesorno_rect.collidepoint(pos):
            if i == 0:
              setPlayerNameJoin = False
              askHostJoin = True
            else:
              if not popup_open and len(playernameTxtbx) >= 2:
                setPlayerNameJoin = False
                clientMode = "join"
                newGame = None 
                saveData = (ipTxtbx, playernameTxtbx)
      elif event.type == pygame.KEYDOWN and clicked_textbox and pygame.key.get_focused():
        playernameTxtbx = text.interface("playername", playernameTxtbx)
    
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
          tilebag, board, players, bank, _ = unpack_save(saveData, ignore_PIN=True, clearConns=True)
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
          saveData = pack_save(tilebag, board, players, bank)
    
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
        settings, clicked_textbox_key = text.interface("customSettings", (settings, clicked_textbox_key, list(drawnSettings.keys())))
    
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
        settings["playernames"], clicked_textbox_int = text.interface("playerNames", (settings["playernames"], clicked_textbox_int))
    
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
                saveData = None
      elif event.type == pygame.KEYDOWN and clicked_textbox and pygame.key.get_focused():
        playernameTxtbx = text.interface("playername", playernameTxtbx)
    
    else: #prep for game startup
      if newGame:
        tilebag = TileBag(*settings["board"].values())
        board = Board(tilebag, settings["bank"]["Chain Size Cost Cap"])
        players: list[Player] = []
        for name in [p for p in settings["playernames"] if p != ""]:
          players.append(Player(tilebag, board, name, 
                                *settings["player"].values()))
        bank = Bank(tilebag, board,
                    *settings["bank"].values(),
                    *settings["bankClassic"].values(),
                    *settings["bankLogarithmic"].values(),
                    *settings["bankExponential"].values())
        saveData, _ = pack_save(tilebag, board, players, bank)
      
      acquireSetup = False
      successfullBoot = True
      return successfullBoot, clientMode, newGame, saveData
    
    clock.tick(MAX_FRAMERATE)

from networking import DISCONN, Command, Connection, send, fetch_updates, propagate

def lobby(screen: pygame.Surface, clock: pygame.time.Clock, conn_dict: dict[UUID, Connection], clientMode: str, newGame: bool, saveData: bytes):  
  tilebag, board, players, bank, _ = unpack_save(saveData, ignore_PIN=True)
  
  if clientMode == "hostLocal":
    return conn_dict, saveData
  
  waitingForJoin = True
  
  selectPlayerFromSave = False
  
  playernames = ["",] * len(players)
  player_ready = [False,] * len(playernames)
  clicked_textbox_int: int | None = None
  
  if clientMode == "join":
    selectPlayerFromSave = True
    unclaimed_players: list[Player] = [p for p in players if p.conn is None]
    hover_save_int, clicked_save_int = [None]*2
  else:
    playernames = [p.name for p in players if p.conn is not None]
  
  popup_open = False
  while waitingForJoin:
    # region check for updates over network
    u = fetch_updates(conn_dict)
    if u:
      for uuid, d in u:
        if d.dump() == "set server connection" and d.val == DISCONN:
          print(f"{conn_dict[uuid].addr} disconnected.")
          
          for p in players:
            if p.conn.uuid == uuid or p.uuid == uuid:
              playernames.remove(p.name)
              if newGame:
                players.remove(p)
          
          conn_dict[uuid].thread.kill()
          del conn_dict[uuid]
        
        if clientMode == "hostServer":
          if d.dump() == "set player name":
            if newGame: # d.val is str
              newplayer: Player = copy(players[0])
              newplayer.name = d.val
              players.append(newplayer)
            else: # d.val is UUID
              # theorhetically, there should be no uuid4 collisions...
              newplayer = [p for p in players if p.uuid == d.val][0]
            
            newplayer.__setConn(conn_dict[uuid])
            playernames.append(newplayer.name)
            print(f"player {newplayer.name} joined")
          
          saveData = pack_save(tilebag, board, players, bank)
          propagate(conn_dict, None, Command("set", "client", "saveData", saveData))
          
        else:
          if d.dump() == "set client saveData":
            saveData = d.val
            tilebag, board, players, bank, _ = unpack_save(saveData, ignore_PIN=True)
            unclaimed_players: list[Player] = [p for p in players if p.conn is None]
        
        # clear processed data
        conn_dict[uuid].data = None
      
    # endregion
    
    # region Render Process
    # Clear the screen
    screen.fill((255, 255, 255))
    #Draw depending on current state
    if selectPlayerFromSave:
      drawinfo = (hover_player_int, clicked_player_int)
      player_rects, load_rect = draw_selectPlayerFromSave(drawinfo, unclaimed_players)
    else:
      text_field_rects, yesandno_rects = draw_waitingForJoin(clientMode, playernames, player_ready, clicked_textbox_int)
    # Update the display
    pygame.display.flip()
    # endregion
    
    # region Handle common events
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
      waitingForJoin = False
    elif event.type == pygame.VIDEORESIZE:
      # Update the window size
      screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
    # endregion
    
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
          send(conn_dict["Server"]["socket"], Command("set", "player", "name", unclaimed_players[clicked_player_int].uuid))
    
    if event.type == pygame.MOUSEBUTTONDOWN:
      # Get the mouse position
      pos = pygame.mouse.get_pos()
      for i, text_field_rect in enumerate(text_field_rects):
        clicked_textbox_int = None
        if text_field_rect.collidepoint(pos):
          clicked_textbox_int = i
          break
      
      for i, yesorno_rect in enumerate(yesandno_rects):
        if yesorno_rect.collidepoint(pos):
          if clientMode == "hostServer":
            if i == 0:
              # kick player
              pass
            else:
              # minimum names filled, start game
              if not popup_open and sum(['' != box for box in playernames]) >= 2:
                pass
          else:
            if i == 0:
              send(conn_dict["Server"]["socket"], Command("set", "server", "connection", DISCONN))
            else:
              # mark ready
              pass
    elif event.type == pygame.KEYDOWN and clicked_textbox_int is not None and pygame.key.get_focused():
      playernames, clicked_textbox_int = text.interface("playerNames", (playernames, clicked_textbox_int))
    
    
    clock.tick(MAX_FRAMERATE)
  
  return conn_dict, saveData
  
  
