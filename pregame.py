import pygame
import os
import pickle
import text
import operator
from copy import deepcopy
from __main__ import HIDE_PERSONAL_INFO
from gui_fullscreen import draw_fullscreenSelect, draw_newGameInit, draw_selectSaveFile, draw_customSettings

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
}

def pregame(dir_path: str, screen: pygame.Surface, clock: pygame.time.Clock, framerate: int):
  global tilebag, board, globalStats, bank
  acquireSetup = True
  successfullBoot = False
  
  askHostJoin = True
  askLoadSave = False
  selectSaveFile = False
  newGameInit = False
  customSettings = False
  
  popup_open = False
  while acquireSetup:
    # region Render Process
    # Clear the screen
    screen.fill((255, 255, 255))
    #Draw ask to load savestate
    if askHostJoin:
      yesandno_rects = draw_fullscreenSelect('hostJoin')
    elif askLoadSave:
      yesandno_rects = draw_fullscreenSelect('loadSave')
    elif selectSaveFile:
      drawinfo = (hover_directory, hover_save_int, clicked_directory, clicked_save_int)
      saveinfo = (saves_path, savefiles)
      save_rects_vec = draw_selectSaveFile(drawinfo, saveinfo)
      directory_rect, savefile_rects, load_rect, noload_button_rect = save_rects_vec
    elif newGameInit:
      text_field_rects, yesandno_rects = draw_newGameInit(playerNameTxtbxs, clicked_textbox_int)
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
      return successfullBoot, None, None, None, None, None, None
    elif event.type == pygame.VIDEORESIZE:
      # Update the window size
      screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
    # endregion
    
    if askHostJoin:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if not popup_open:
          # Check if askToBuy was clicked
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              askHostJoin = False
              if i == 1:
                # TODO join host logic
                askLoadSave = True
              else:
                # Host Logic
                askLoadSave = True
   
    elif askLoadSave:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if not popup_open:
          # Check if load save was clicked
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              askLoadSave = False
              playerNameTxtbxs = [''] * 6 #this int sets the max number of players
              if i == 1:
                selectSaveFile = True
                saves_path = dir_path + r'\saves'
                savefiles = os.listdir(dir_path + r'\saves')
                hover_directory, clicked_directory = [False]*2
                hover_save_int, clicked_save_int = [None]*2
              else:
                newGameInit = True
                pygame.key.set_repeat(500, 50) #time in ms
                clicked_textbox_int = None
    
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
        if noload_button_rect.collidepoint(pos):
          selectSaveFile = False
          newGameInit = True
          clicked_textbox_int = None
        if hover_directory:
          clicked_directory = not clicked_directory
        elif clicked_directory and hover_save_int is not None:
          clicked_save_int = (hover_save_int if clicked_save_int != hover_save_int else None)
        elif clicked_save_int is not None and load_rect.collidepoint(pos):
          selectSaveFile = False
          savefile = savefiles[clicked_save_int]
          with open(rf'{saves_path}\{savefile}', 'rb') as file:
            data = pickle.load(file)
            datarem, tilebag = pickle.loads(data)
            datarem, board = pickle.loads(datarem)
            datarem, globalStats = pickle.loads(datarem)
            datarem, players = pickle.loads(datarem)
            _, bank = pickle.loads(datarem)
          if HIDE_PERSONAL_INFO:
            personal_info_names = [p.name for p in players]
            for i, p in enumerate(players):
              p.name = f"Player {i+1}"
          else: 
            personal_info_names = None
          pygame.display.set_caption('Acquire Board')
          acquireSetup = False
          successfullBoot = True
          return successfullBoot, tilebag, board, bank, players, personal_info_names, globalStats
    
    elif newGameInit:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        for i, text_field_rect in enumerate(text_field_rects):
          clicked_textbox_int = None
          if text_field_rect.collidepoint(pos):
            clicked_textbox_int = i
            break
        if not popup_open and sum(['' != box for box in playerNameTxtbxs]) >= 2:
          # minimum names filled, check for click to go to settings
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              newGameInit = False
              playernames = [pname for pname in playerNameTxtbxs if pname != '']
              settings = deepcopy(stockGameSettings)
              if i == 0:
                customSettings = True
                pygame.key.set_repeat(500, 50) #time in ms
                clicked_textbox_key = None
                longestKey = max([ max([len(k) for k in d.keys()]) for d in stockGameSettings.values()])
              break
      elif event.type == pygame.KEYDOWN and clicked_textbox_int is not None and pygame.key.get_focused():
        playerNameTxtbxs, clicked_textbox_int = text.interface("playerName", (playerNameTxtbxs, clicked_textbox_int))
    
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
      elif event.type == pygame.KEYDOWN and clicked_textbox_key is not None and pygame.key.get_focused():
        settings, clicked_textbox_key = text.interface("customSettings", (settings, clicked_textbox_key, list(drawnSettings.keys())))
    
    else: #prep for game startup
      from tilebag import TileBag
      tilebag = TileBag(*settings["board"].values())
      from stats import Stats
      globalStats = Stats(globalStats=True)
      from board import Board
      board = Board(settings["bank"]["Chain Size Cost Cap"])
      from bank import Bank
      bank = Bank(*settings["bank"].values(),
                  *settings["bankClassic"].values(),
                  *settings["bankLogarithmic"].values(),
                  *settings["bankExponential"].values())
      
      from player import Player
      order = []
      for name in playernames:
        gamestarttileID = tilebag.drawtile()
        gamestarttile = tilebag.tileIDinterp([gamestarttileID])
        board.debug_tilesinplayorder.append(gamestarttile[0])
        # print(f'{name} drew {gamestarttile[0]}!')
        order.append( (Player(name, *settings["player"].values()), gamestarttile) )
      players: list[Player] = [tup[0] for tup in sorted(order, key=operator.itemgetter(1))]
      
      personal_info_names = [p.name for p in players]
      if HIDE_PERSONAL_INFO:
        for i, p in enumerate(players): p.name=f"Player {i+1}" 
      # print('Player order is:', *sortedplayers)
      for p in players:
        p.drawtile(p.tileQuant)
      sortactiveIDs = tilebag.tilesToIDs(board.debug_tilesinplayorder)
      sortactiveIDs.sort()
      board.tilesinplay = tilebag.tileIDinterp(sortactiveIDs)
      
      pygame.display.set_caption('Acquire Board')
      acquireSetup = False
      successfullBoot = True
    
    clock.tick(framerate)
  return successfullBoot, tilebag, board, bank, players, personal_info_names, globalStats