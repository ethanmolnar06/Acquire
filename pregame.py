import pygame
import os
import pickle
import text
import operator
from __main__ import HIDE_PERSONAL_INFO
from gui_fullscreen import draw_fullscreenSelect, draw_newGameInit, draw_selectSaveFile

def pregame(dir_path: str, screen: pygame.Surface, clock: pygame.time.Clock, framerate: int):
  global tilebag, globalStats, board, bank
  acquireSetup = True
  successfullBoot = False
  
  askHostJoin = True
  askLoadSave = False
  selectSaveFile = False
  newGameInit = False
  stockSettings = False
  customSettings = False
  
  popup_open = False
  while acquireSetup:
    # print(askLoadSave, selectSaveFile, newGameInit, stockSettings, customSettings)
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
      directory_rect, savefile_rects, load_rect = save_rects_vec
    elif newGameInit:
      text_field_rects, yesandno_rects = draw_newGameInit(playerNameTxtbxs, clicked_textbox_int)
    elif customSettings:
      pass
    # Update the display
    pygame.display.flip()
    # endregion
    
    # region Handle common events
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
      acquireSetup = False
      gameStart = False
      break
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
   
    #Waiting to Load Save Y/N
    elif askLoadSave:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if not popup_open:
          # Check if askToBuy was clicked
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              askLoadSave = False
              if i == 1:
                selectSaveFile = True
                loadedSaveFile = True
                saves_path = dir_path + r'\saves'
                savefiles = os.listdir(dir_path + r'\saves')
                hover_directory, clicked_directory = [False]*2
                hover_save_int, clicked_save_int = [None]*2
              else:
                newGameInit = True
                loadedSaveFile = True
                pygame.key.set_repeat(500, 50) #time in ms
                clicked_textbox_int = None
                playerNameTxtbxs = [''] * 6 #this int sets the max number of players
    
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
        if hover_directory:
          clicked_directory = not clicked_directory
        elif clicked_directory and hover_save_int != None:
          clicked_save_int = (hover_save_int if clicked_save_int != hover_save_int else None)
        elif clicked_save_int != None and load_rect.collidepoint(pos):
          savefile = savefiles[clicked_save_int]
          with open(rf'{saves_path}\{savefile}', 'rb') as file:
            tilebag, bank, board, players, globalStats = pickle.load(file)
          if HIDE_PERSONAL_INFO:
            personal_info_names = [p.name for p in players]
            for i, p in enumerate(players):
              p.name = f"Player {i+1}"
          else: 
            personal_info_names = None
          selectSaveFile = False
    
    elif newGameInit:
      newGameInit = False
      stockSettings = True
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
              if i == 1:
                stockSettings = True
              else:
                customSettings = True
      elif event.type == pygame.KEYDOWN and clicked_textbox_int != None and pygame.key.get_focused():
        playerNameTxtbxs, clicked_textbox_int = text.interface("playerName", (playerNameTxtbxs, clicked_textbox_int))
    
    elif stockSettings:
      from tilebag import TileBag
      tilebag = TileBag(24, 18, 84, 85, 83)
      from stats import Stats
      globalStats = Stats(globalStats=True)
      from board import Board
      board = Board()
      from bank import Bank
      bank = Bank()
      pTileQuant = 9
      playernames = ['Ethan', 'Robbie', 'Tommy', 'Ben'] # debug convenience, TODO remove
      # playernames = ['Ethan', 'Robbie', 'Tommy', 'Ben', "ajajjs", "skeiis", "ojjljnj", "yytututy"] # debug convenience, TODO remove
      # playernames = ['Ethan', 'Robbie'] # debug convenience, TODO remove
      orderdict = {}
      for name in playernames:
        gamestarttileID = tilebag.drawtile()
        orderdict[name] = gamestarttileID
        gamestarttile = tilebag.tileIDinterp([gamestarttileID])
        board.debug_tilesinplayorder.append(gamestarttile[0])
        print(f'{name} drew {gamestarttile[0]}!')
      sortedplayers = [tup[0] for tup in sorted(orderdict.items(), key=operator.itemgetter(1))]
      personal_info_names = sortedplayers
      from player import Player
      players = [Player(pName, tileQuant = pTileQuant) for i, pName in enumerate(sortedplayers)]
      if HIDE_PERSONAL_INFO:
        for i, p in enumerate(players): p.name=f"Player {i+1}" 
      print('Player order is:', *sortedplayers)
      for p in players:
        p.drawtile(p.tileQuant)
      sortactiveIDs = tilebag.tilesToIDs(board.debug_tilesinplayorder)
      sortactiveIDs.sort()
      board.tilesinplay = tilebag.tileIDinterp(sortactiveIDs)
      stockSettings = False

    elif customSettings:
      # TODO setup custom setting options
      stockSettings = True
      customSettings = False
      # acquireSetup = False
      # gameStart = True
    
    else: #prep for game startup
      pygame.display.set_caption('Acquire Board')
      acquireSetup = False
      successfullBoot = True
      gameStart = True

    clock.tick(framerate)
  return successfullBoot, gameStart, tilebag, board, bank, players, personal_info_names, globalStats, loadedSaveFile