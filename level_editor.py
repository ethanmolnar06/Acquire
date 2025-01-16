# region Initialize Pygame
import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "silent"
import pygame
pygame.init()
window_size = (1600, 900)
screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
pygame.scrap.init()
pygame.display.set_caption('Game Setup')
clock = pygame.time.Clock()
pygame.key.set_repeat(300, 50) #time in ms
gameUtils = (screen, clock)
# endregion

from pregame import config
successfullBoot, _, _, gameState = config(gameUtils, allowNonLocal=False)

if not successfullBoot:
  # Shut down Pygame
  pygame.quit()
  sys.exit()

from objects import *
from common import NO_RENDER_EVENTS, VARIABLE_FRAMERATE, MAX_FRAMERATE, pack_gameState, write_save
from gui import GUI_area, draw_main_screen, draw_game_board, draw_other_player_stats

tilebag, board, players, bank = gameState
focus_content = GUI_area(levelEditor=True)
display_player_index: int = 0
levelEditing: bool = True

forceRender: bool = True
skipRender: bool = False

while levelEditing:
  event = pygame.event.poll()
  # region Render Process
  if (forceRender or event.type not in NO_RENDER_EVENTS) and not skipRender:
    forceRender = False
    
    # Clear the screen
    screen.fill((255, 255, 255))
    
    prohibitedTiles = board.contraceptcheck(players[display_player_index].tiles, checkChainAvail=True)
    _, tile_rects, player_stat_rects, popup_select_rects = draw_main_screen(screen, players[display_player_index], True, prohibitedTiles, False, False, focus_content)
    
    if focus_content.game_board:
      board_rects = draw_game_board(screen, board)
    elif focus_content.other_player_stats:
      draw_other_player_stats(screen, bank, [player for player in players if player is not players[display_player_index]])
    
    # Update the display
    pygame.display.flip()
  # endregion
  
  # region Handle common events
  if event.type == pygame.QUIT:
    levelEditing = False
    saveData = pack_gameState(tilebag, board, players, bank)
    write_save(saveData, [p._truename for p in players], levelEditor=True)
    break
  elif event.type == pygame.VIDEORESIZE:
    # Update the window size
    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
  elif event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = event.dict["pos"]
        for i, popup_select_rect in enumerate(popup_select_rects): # Check if any of the popup_selects were clicked
          if popup_select_rect.collidepoint(pos):
            focus_content.change_showing(i)
  # endregion
  
  if event.type == pygame.MOUSEBUTTONDOWN:
    pos = event.dict["pos"]
    
    # region Check for Click
    clicked_board_tile = None
    clicked_player_stat_index = None
    clicked_player_tile = None
    
    for i, board_rect in enumerate(board_rects):
      if board_rect.collidepoint(pos):
        clicked_board_tile = tilebag.alltiles[i]
        break
    
    if clicked_board_tile is None:
      for i, player_stat_rect in enumerate(player_stat_rects):
        if player_stat_rect.collidepoint(pos):
          clicked_player_stat_index = i
          break
    
    if clicked_board_tile is None and clicked_player_stat_index is None and tile_rects is not None:
      for i, tile_rect in enumerate(tile_rects):
        if tile_rect.collidepoint(pos):
          clicked_player_tile = players[display_player_index].tiles[i]
          break
    # endregion
    
    # region Change Board State
    if clicked_board_tile is not None:
      mode, chains = board.tileplaymode(clicked_board_tile)
      if event.button == 1: # left click
        for p in players:
          if clicked_board_tile in p.tiles:
            p.drawtile()
            p.returntile(clicked_board_tile)
          break
        board._play_tile(clicked_board_tile, clicked_board_tile in board.tilesinplay)
        if clicked_board_tile in board.chaindict.keys():
          del board.chaindict[clicked_board_tile]
      elif event.button == 3 and clicked_board_tile in board.tilesinplay and mode != "place": # right click
        inactivechains = board.fetchactivechains(True)
        if not clicked_board_tile in board.chaindict.keys() and inactivechains:
          newchain = inactivechains[0]
        elif inactivechains:
          newchain = board.chaindict[clicked_board_tile]
          while newchain not in inactivechains:
            chainindex = tilebag.chainnames.index(newchain)
            newchain = tilebag.chainnames[(chainindex + 1) % len(tilebag.chainnames)]
        board.chaindict[clicked_board_tile] = newchain
        board.tileprop(clicked_board_tile, newchain)
    # endregion
    
    # region Change Current Viewed Player Stats
    if clicked_player_stat_index is not None:
      if clicked_player_stat_index == 0:
        display_player_index = (display_player_index + 1) % len(players)
      elif clicked_player_stat_index == 1:
        if event.button == 1: # left click
          players[display_player_index].bal += 100
        elif event.button == 3: # right click
          players[display_player_index].bal -= 100
      else:
        setchain = tilebag.chainnames[clicked_player_stat_index - 2]
        if event.button == 1 and bank.stocks[setchain] > 0: # left click
          players[display_player_index].stocks[setchain] += 1
          bank.stocks[setchain] -= 1
        elif event.button == 3 and players[display_player_index].stocks[setchain] > 0: # right click
          players[display_player_index].stocks[setchain] -= 1
          bank.stocks[setchain] += 1
    # endregion
    
    # region Change Current Viewed Player Tiles
    if focus_content.random_tiles:
      focus_content.game_board = True
      focus_content.random_tiles = False
      for tile in players[display_player_index].tiles.copy():
        players[display_player_index].returntile(tile)
      players[display_player_index].drawtile(players[display_player_index].tileQuant)
    
    if clicked_player_tile is not None:
      players[display_player_index].returntile(clicked_player_tile)
      if event.button == 1: # left click
        players[display_player_index].swapnexttile(clicked_player_tile)
      elif event.button == 3: # right click
        players[display_player_index].swapnexttile(clicked_player_tile, prev=True)
    # endregion
  
  
  clock.tick(1 if VARIABLE_FRAMERATE and not pygame.key.get_focused() else MAX_FRAMERATE)